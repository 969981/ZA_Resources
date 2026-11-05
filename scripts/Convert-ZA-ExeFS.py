#!/usr/bin/env python3
"""Convert verified ZA v2.0.2 NSO modules to ELF and optionally decompressed NSO, preserving provenance.

Large ELF files are 7z-volume archived for normal Git; the full ELF remains
in _work/ for workflow artifact upload when --keep-elf is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

DEFAULT_NAMES = ("main", "rtld", "sdk")
MAX_GIT_BYTES = 90 * 1024 * 1024
TOOL_COMMIT = "a1760ba54e2aefb41444933f53b90e6e8b05c399"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_nso(path: Path) -> str:
    with path.open("rb") as stream:
        header = stream.read(0x60)
    if len(header) < 0x60 or header[:4] != b"NSO0":
        raise ValueError(f"Invalid NSO0 header: {path}")
    return header[0x40:0x60].hex()


def verify_elf(path: Path) -> None:
    with path.open("rb") as stream:
        header = stream.read(64)
    if (len(header) != 64 or header[:4] != b"\x7fELF" or
            header[4] != 2 or header[5] != 1):
        raise ValueError(f"Missing ELF64 little-endian header: {path}")
    if struct.unpack_from("<H", header, 18)[0] != 183:
        raise ValueError(f"Not AArch64 ELF: {path}")
    if path.stat().st_size < 4096:
        raise ValueError(f"Suspiciously small ELF: {path}")


def checked(command: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def export_one(root: Path, converter: Path, name: str,
               sevenzip: str | None, keep_elf: bool, export_uncompressed: bool = False) -> dict:
    if name not in DEFAULT_NAMES:
        raise ValueError(f"Unrecognized main filename: {name}")
    source = root / "v2.0.2" / "4a70b3ff963bfe412681185cea68bf55_NCA" / "0" / name
    if not source.is_file():
        raise FileNotFoundError(source)
    build_id = verify_nso(source)
    source_size, source_hash = source.stat().st_size, file_hash(source)

    dest = root / "Unpack" / "v2.0.2" / "exefs" / name
    dest.mkdir(parents=True, exist_ok=True)
    persistent_work = dest / "_work"
    if keep_elf:
        persistent_work.mkdir(exist_ok=True)
        temp = None
        work = persistent_work
    else:
        temp = tempfile.TemporaryDirectory(prefix=f"za-nx2elf-{name}-")
        work = Path(temp.name)
    try:
        elf = work / f"{name}.elf"
        elf.unlink(missing_ok=True)
        # Upstream nx2elf can return exit code zero even when NsoToElf fails:
        # always validate output contents, not just the process exit code.
        command = [str(converter), str(source), "--export-elf", str(elf)]
        unpacked = work / f"{name}.uncompressed.nso"
        if export_uncompressed:
            unpacked.unlink(missing_ok=True)
            command.extend(["--export-uncompressed", str(unpacked)])
        checked(command)
        if not elf.is_file():
            raise RuntimeError(f"nx2elf did not create {elf}")
        verify_elf(elf)
        elf_size, elf_hash = elf.stat().st_size, file_hash(elf)
        artifacts: list[dict] = []
        if elf_size < MAX_GIT_BYTES:
            stored = dest / f"{name}.elf"
            shutil.copyfile(elf, stored)
            if file_hash(stored) != elf_hash:
                raise RuntimeError(f"ELF copy hash mismatch: {stored}")
            artifacts.append({"path": stored.relative_to(root).as_posix(),
                              "size": stored.stat().st_size, "sha256": file_hash(stored)})
            mode = "raw-elf"
        else:
            if not sevenzip:
                raise RuntimeError("ELF exceeds 90 MiB; install 7z for verified volumes")
            archive = dest / f"{name}.elf.7z"
            # Remove stale volumes only for this exact generated basename.
            for old in dest.glob(f"{name}.elf.7z.*"):
                if old.is_file():
                    old.unlink()
            archive.unlink(missing_ok=True)
            checked([sevenzip, "a", "-t7z", "-mx=1", "-v90m",
                     str(archive), elf.name], cwd=work)
            volumes = sorted(dest.glob(f"{name}.elf.7z.*"))
            if not volumes and archive.is_file():
                volumes = [archive]
            if not volumes:
                raise RuntimeError(f"No 7z volume produced for {name}")
            checked([sevenzip, "t", str(volumes[0])])
            with tempfile.TemporaryDirectory(prefix=f"za-elf-verify-{name}-") as tmp:
                checked([sevenzip, "x", "-y", f"-o{tmp}", str(volumes[0])])
                extracted = Path(tmp) / elf.name
                verify_elf(extracted)
                if file_hash(extracted) != elf_hash:
                    raise RuntimeError(f"7z round-trip hash mismatch for {name}")
            for stored in volumes:
                if stored.stat().st_size >= 100_000_000:
                    raise RuntimeError(f"Git single-file size limit exceeded: {stored}")
                artifacts.append({"path": stored.relative_to(root).as_posix(),
                                  "size": stored.stat().st_size,
                                  "sha256": file_hash(stored)})
            mode = "7z-volumes"
        uncompressed_info = None
        if export_uncompressed:
            if not unpacked.is_file():
                raise RuntimeError(f"nx2elf did not produce uncompressed NSO: {unpacked}")
            unpacked_build = verify_nso(unpacked)
            if unpacked_build != build_id:
                raise RuntimeError("Decompressed NSO BuildID differs from original")
            unc_size, unc_sha = unpacked.stat().st_size, file_hash(unpacked)
            unc_artifacts = []
            if unc_size < MAX_GIT_BYTES:
                target = dest / unpacked.name
                shutil.copyfile(unpacked, target)
                if file_hash(target) != unc_sha:
                    raise RuntimeError("Uncompressed NSO copy SHA256 mismatch")
                unc_artifacts.append({"path": target.relative_to(root).as_posix(),
                                      "size": target.stat().st_size, "sha256": file_hash(target)})
                unc_storage = "raw-nso"
            else:
                if not sevenzip:
                    raise RuntimeError("Uncompressed NSO exceeds 90 MiB; 7z required")
                archive = dest / (unpacked.name + ".7z")
                for old in dest.glob(unpacked.name + ".7z.*"):
                    old.unlink()
                archive.unlink(missing_ok=True)
                checked([sevenzip, "a", "-t7z", "-mx=1", "-v90m",
                         str(archive), unpacked.name], cwd=work)
                volumes = sorted(dest.glob(unpacked.name + ".7z.*"))
                if not volumes and archive.is_file():
                    volumes = [archive]
                if not volumes:
                    raise RuntimeError("No uncompressed NSO 7z volume was produced")
                checked([sevenzip, "t", str(volumes[0])])
                with tempfile.TemporaryDirectory(prefix=f"za-nso-verify-{name}-") as tmp:
                    checked([sevenzip, "x", "-y", f"-o{tmp}", str(volumes[0])])
                    rebuilt = Path(tmp) / unpacked.name
                    if file_hash(rebuilt) != unc_sha or verify_nso(rebuilt) != build_id:
                        raise RuntimeError("NSO archive round-trip / BuildID check failed")
                for target in volumes:
                    if target.stat().st_size >= 100_000_000:
                        raise RuntimeError("NSO archive volume exceeds GitHub blob limit")
                    unc_artifacts.append({"path": target.relative_to(root).as_posix(),
                                          "size": target.stat().st_size,
                                          "sha256": file_hash(target)})
                unc_storage = "7z-volumes"
            uncompressed_info = {"filename": unpacked.name, "size": unc_size,
                                 "sha256": unc_sha, "storage": unc_storage,
                                 "artifacts": unc_artifacts,
                                 "buildIdMatchesInput": True}
            artifacts.extend(unc_artifacts)
        info = {
            "status": "CONFIRMED",
            "version": "v2.0.2",
            "game": "Pokemon Legends Z-A",
            "sourcePath": source.relative_to(root).as_posix(),
            "sourceSize": source_size,
            "sourceSha256": source_hash,
            "nsoBuildIdHex": build_id,
            "converter": "tools/nx2elf",
            "converterUpstreamCommit": TOOL_COMMIT,
            "command": [str(converter.relative_to(root)) if converter.is_relative_to(root) else converter.name,
                        str(source.relative_to(root)), "--export-elf",
                        f"Unpack/v2.0.2/exefs/{name}/_work/{name}.elf"],
            "elfFilename": f"{name}.elf",
            "elfSize": elf_size,
            "elfSha256": elf_hash,
            "elfFormat": "ELF64 little-endian AArch64",
            "uncompressedNso": uncompressed_info,
            "storage": mode,
            "artifacts": artifacts,
            "validated": ["NSO0 magic", "ELF64 AArch64 header",
                          "SHA256 output", "archive round-trip" if mode == "7z-volumes"
                          else "ELF copy round-trip"],
        }
        (dest / "provenance.json").write_text(
            json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return info
    finally:
        if temp is not None:
            temp.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--nx2elf", type=Path, required=True)
    parser.add_argument("--7z", dest="sevenzip", default=shutil.which("7z"))
    parser.add_argument("--export-uncompressed", action="store_true",
                        help="also reconstruct and publish uncompressed NSO")
    parser.add_argument("--keep-elf", action="store_true",
                        help="Retain raw ELF under ignored _work/ for artifact upload")
    parser.add_argument("--names", nargs="+", choices=DEFAULT_NAMES,
                        default=["main"])
    args = parser.parse_args()
    root = args.repo_root.resolve()
    converter = args.nx2elf.resolve()
    if not converter.is_file():
        parser.error(f"nx2elf binary not found: {converter}")
    for name in args.names:
        info = export_one(root, converter, name, args.sevenzip, args.keep_elf,
                          args.export_uncompressed)
        print(json.dumps({k: info[k] for k in
                          ("game", "sourcePath", "elfSize", "elfSha256",
                           "storage", "artifacts")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
