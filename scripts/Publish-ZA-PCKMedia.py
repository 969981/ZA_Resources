#!/usr/bin/env python3
"""Publish validated 90 MiB 7z volumes of ZA Wwise PCK extracted media.

Original PCK files and the existing PCK JSON indexes are immutable. This script
never reconstructs audio or transcodes WEM; it archives the extracted bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

MEDIA_ROOT = Path("Unpack/v2.0.2/romfs/audio/wwise/bin/Switch")
STEMS = ("Stream", "Stream_dlc")
MAX_GIT_BLOB = 100_000_000
MAX_VOLUME = 90 * 1024 * 1024
BLOCK = 1024 * 1024


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(BLOCK), b""):
            sha.update(block)
    return sha.hexdigest()


def expected_media(index: dict, stem: str) -> dict[str, dict]:
    if index.get("source") != stem + ".pck" or index.get("status") != "COMPLETE":
        raise ValueError(f"{stem}: index does not show a completed matching PCK")
    items = index.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError(f"{stem}: missing PCK media catalog")
    expected = {}
    for record in items:
        raw = record.get("path")
        if not isinstance(raw, str) or "\\" in raw:
            raise ValueError(f"{stem}: invalid source path {raw!r}")
        pieces = PurePosixPath(raw).parts
        if (len(pieces) < 5 or pieces[:2] != ("ZA_PCK_MEDIA", stem)
                or any(x in ("", ".", "..") for x in pieces) or raw.startswith("/")):
            raise ValueError(f"{stem}: index path escapes expected package: {raw}")
        relative = PurePosixPath(*pieces[2:]).as_posix()
        size = record.get("size")
        sha = record.get("sha256")
        if (not isinstance(size, int) or size < 0
                or not isinstance(sha, str) or re.fullmatch(r"[0-9a-fA-F]{64}", sha) is None
                or record.get("status") != "EXTRACTED"):
            raise ValueError(f"{stem}: incomplete or invalid index record {raw}")
        value = {"size": size, "sha256": sha.lower()}
        if relative in expected and expected[relative] != value:
            raise ValueError(f"{stem}: file ID collision with different bytes: {relative}")
        expected[relative] = value
    return expected


def check_tree(root: Path, expected: dict[str, dict]) -> tuple[int, int]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"Missing or symlinked media directory: {root}")
    actual: set[str] = set()
    nbytes = 0
    for f in root.rglob("*"):
        if f.is_symlink():
            raise ValueError(f"Media tree contains symlink: {f}")
        if not f.is_file():
            continue
        rel = f.relative_to(root).as_posix()
        if rel not in expected:
            raise ValueError(f"Undocumented media file: {rel}")
        if f.stat().st_size != expected[rel]["size"] or digest(f) != expected[rel]["sha256"]:
            raise ValueError(f"Media SHA-256/size mismatch: {rel}")
        actual.add(rel)
        nbytes += expected[rel]["size"]
    missing = set(expected) - actual
    if missing:
        raise ValueError(f"Missing {len(missing)} media files, e.g. {sorted(missing)[:3]}")
    return len(actual), nbytes


def run_7z(exe: str, args: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.run([exe, *args], cwd=cwd, check=False)
    if proc.returncode:
        raise RuntimeError(f"7-Zip failed (exit {proc.returncode}) during {args[0]}")


def inspect_parts(archive: Path) -> list[Path]:
    directory = archive.parent
    pattern = re.compile(r"^" + re.escape(archive.name) + r"\.(\d{3,})$")
    found = []
    for item in directory.iterdir():
        m = pattern.match(item.name)
        if m:
            found.append((int(m.group(1)), item))
    found.sort()
    if not found:
        raise ValueError(f"No 7z volumes generated for {archive}")
    result = []
    for expected_number, (actual_number, part) in enumerate(found, start=1):
        if actual_number != expected_number:
            raise ValueError(f"7z volume gap: {archive}, expected {expected_number:03d}")
        n = part.stat().st_size
        if n == 0 or n > MAX_VOLUME or n >= MAX_GIT_BLOB:
            raise ValueError(f"7z volume over Git safe limit or empty: {part} ({n})")
        result.append(part)
    return result


def archive_one(
    media_root: Path,
    index_root: Path,
    archive_root: Path,
    stem: str,
    exe: str,
    source_run: int,
) -> dict:
    source = index_root / (stem + ".pck.json")
    index = json.loads(source.read_text(encoding="utf-8-sig"))
    expected = expected_media(index, stem)
    n, length = check_tree(media_root / stem, expected)
    archive = archive_root / (stem + ".pck.media.7z")
    archive_root.mkdir(parents=True, exist_ok=True)
    # Refuse to overwrite published or incomplete archives.
    if any(archive_root.glob(archive.name + ".*")):
        raise ValueError(f"Refusing to overwrite existing archive volumes: {archive}")
    # 7z includes the top-level package name so two sets remain disjoint.
    run_7z(exe, ["a", "-t7z", "-mx=1", "-mmt=on", "-v90m",
                 "-bd", "-y", str(archive.resolve()), stem], cwd=media_root)
    parts = inspect_parts(archive)
    run_7z(exe, ["t", "-bd", "-y", str(parts[0])])
    # CRC alone is insufficient: independently restore and hash each original WEM.
    with tempfile.TemporaryDirectory(prefix=f"za_{stem}_check_") as work:
        restored = Path(work)
        run_7z(exe, ["x", "-bd", "-y", str(parts[0]), "-o" + str(restored)])
        count, restored_length = check_tree(restored / stem, expected)
        if count != n or restored_length != length:
            raise ValueError(f"Archive roundtrip reconciliation failed for {stem}")
    volumes = []
    for part in parts:
        volumes.append({
            "path": part.as_posix(),  # made repository-relative by caller
            "sizeBytes": part.stat().st_size,
            "sha256": digest(part),
        })
    return {
        "sourcePackage": stem + ".pck",
        "sourcePackageSha256": index["sourceSha256"],
        "indexSha256": digest(source),
        "sourceArtifactRunId": source_run,
        "mediaRecords": len(index["items"]),
        "uniqueMediaFiles": n,
        "mediaBytes": length,
        "volumeSizeLimitMiB": 90,
        "archiveMethod": "7z -t7z -mx=1 -v90m",
        "volumeCount": len(volumes),
        "archiveBytes": sum(x["sizeBytes"] for x in volumes),
        "volumes": volumes,
        "verification": "7z TEST + extracted payload SHA-256 for all indexed media",
        "status": "COMPLETE",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--media-root", type=Path, required=True)
    ap.add_argument("--sevenzip", default="7z")
    ap.add_argument("--source-run", type=int, default=42055289781)
    args = ap.parse_args()
    if args.source_run < 1:
        ap.error("--source-run must be positive")
    repo = args.repo.resolve()
    media = args.media_root.resolve()
    index_dir = repo / MEDIA_ROOT / "_index"
    dest = repo / MEDIA_ROOT / "_media_archives"
    if media == dest or repo in media.parents:
        raise ValueError("Downloaded audio must reside outside Git checkout")
    archive_data = []
    for stem in STEMS:
        data = archive_one(media, index_dir, dest, stem, args.sevenzip, args.source_run)
        for part in data["volumes"]:
            part["path"] = (dest / Path(part["path"]).name).relative_to(repo).as_posix()
        archive_data.append(data)
    manifest = {
        "schemaVersion": 1,
        "version": "v2.0.2",
        "generatedFromWorkflowRun": args.source_run,
        "packages": archive_data,
        "complete": True,
    }
    output = dest / "media-archive-manifest.json"
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": output.relative_to(repo).as_posix(),
                      "sources": len(archive_data),
                      "mediaFiles": sum(p["uniqueMediaFiles"] for p in archive_data),
                      "volumes": sum(p["volumeCount"] for p in archive_data),
                      "archiveBytes": sum(p["archiveBytes"] for p in archive_data)}))


if __name__ == "__main__":
    main()
