#!/usr/bin/env python3
"""Restore original ZA v2.0.2 Trinity pair directly, without staging a second 4.75 GiB copy.

Every archived part is validated against the pinned transfer manifest before
the first 7-Zip invocation; 7z t and the restored original SHA-256 are mandatory.
Outputs are written outside the source archive checkout and are never pushed
as the original large file.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

VERSION = "v2.0.2"
SOURCE_PREFIX = "v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/1/arc/"

def file_sha(path: Path):
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()

def verify(path: Path, expected_len: int, expected_sha: str, label: str):
    if not path.is_file():
        raise FileNotFoundError(f"Missing {label}: {path}")
    if path.stat().st_size != expected_len:
        raise ValueError(f"{label} length mismatch: {path}, expected {expected_len}")
    actual = file_sha(path)
    if actual.lower() != expected_sha.lower():
        raise ValueError(f"{label} SHA-256 mismatch: {path}, expected {expected_sha}, actual {actual}")
    print(f"VERIFIED {label} {path.name} bytes={expected_len}", flush=True)
    return actual

def restore(manifest: Path, archive_root: Path, workspace: Path, sevenzip: str) -> dict:
    metadata = json.loads(manifest.read_text(encoding="utf-8-sig"))
    if metadata.get("schemaVersion") != 1 or metadata.get("version") != VERSION:
        raise ValueError("Invalid manifest schema/version")
    records = {r["sourceRelativePath"]: r for r in metadata["files"]}
    for rel in ("arc/data.trpfd", "arc/data.trpfs"):
        if rel not in records:
            raise ValueError("Missing manifest original: " + rel)
    desc = records["arc/data.trpfd"]
    packed = records["arc/data.trpfs"]
    if desc["archiveType"] != "Raw" or packed["archiveType"] != "7z":
        raise ValueError("Expected raw TRPFD and 7z multi-volume TRPFS")
    parts = packed["archiveParts"]
    if packed["volumeCount"] != 87 or len(parts) != 87:
        raise ValueError("Wrong TRPFS volume count (expected 87)")
    expected_prefix = SOURCE_PREFIX
    source_descriptor = archive_root / "data.trpfd"
    verify(source_descriptor, desc["sourceSizeBytes"], desc["sourceSha256"], "TRPFD")
    if desc["archiveParts"][0]["path"] != expected_prefix + "data.trpfd":
        raise ValueError("Unexpected TRPFD archive location")
    for i, part in enumerate(parts, 1):
        expected_name = f"data.trpfs.7z.{i:03}"
        if part["path"] != expected_prefix + expected_name:
            raise ValueError(f"Out of order or unsafe archive volume {i}")
        verify(archive_root / expected_name, part["sizeBytes"], part["sha256"], f"volume {i:03}/087")
    disk = shutil.disk_usage(workspace if workspace.exists() else workspace.parent)
    if disk.free < packed["sourceSizeBytes"] + (1024**3):
        raise RuntimeError(f"Insufficient free disk for verified restore: {disk.free} bytes")
    first = archive_root / "data.trpfs.7z.001"
    subprocess.run([sevenzip, "t", "-bd", str(first)], check=True)
    target = workspace / "arc"
    target.mkdir(parents=True, exist_ok=True)
    dest_descriptor = target / "data.trpfd"
    if dest_descriptor.exists():
        verify(dest_descriptor, desc["sourceSizeBytes"], desc["sourceSha256"], "existing restored TRPFD")
    else:
        shutil.copyfile(source_descriptor, dest_descriptor)
        verify(dest_descriptor, desc["sourceSizeBytes"], desc["sourceSha256"], "restored TRPFD")
    dest_packed = target / "data.trpfs"
    if dest_packed.is_file():
        verify(dest_packed, packed["sourceSizeBytes"], packed["sourceSha256"], "existing restored TRPFS")
    else:
        subprocess.run([sevenzip, "x", "-y", "-bd", str(first), "-o" + str(target)], check=True)
        verify(dest_packed, packed["sourceSizeBytes"], packed["sourceSha256"], "restored TRPFS")
    info = {
        "status": "CONFIRMED_ORIGINAL_BYTES",
        "version": VERSION,
        "originals": [
            {"path": "arc/data.trpfd", "sizeBytes": desc["sourceSizeBytes"],
             "sha256": desc["sourceSha256"]},
            {"path": "arc/data.trpfs", "sizeBytes": packed["sourceSizeBytes"],
             "sha256": packed["sourceSha256"], "archiveVolumes": 87,
             "archiveTotalBytes": packed["compressedTotalBytes"]}
        ],
        "validation": ["all 87 volume sizes and SHA-256", "7z t archive test",
                       "restored TRPFD original SHA-256", "restored TRPFS original SHA-256"],
        "caution": "Verified archive restoration does not alone establish virtual file extraction."
    }
    return info

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--sevenzip", required=True)
    p.add_argument("--evidence", type=Path, required=True)
    args = p.parse_args()
    info = restore(args.manifest.resolve(), args.archive_root.resolve(),
                   args.workspace.resolve(), args.sevenzip)
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False, indent=2), flush=True)

if __name__ == "__main__":
    main()
