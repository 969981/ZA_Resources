#!/usr/bin/env python3
"""Copy exact pinned source snapshots from SV_Resources/tools into ZA_Resources/tools.

This is a one-shot source import helper used by GitHub Actions; it never uses
game files or downloads unpinned branches. Call once per allowed directory.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

def git(*args, cwd):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()

def copy_one(source, destination, spec, name):
    selected = set(spec["sourcePaths"])
    relative = "tools/" + name
    if relative not in selected:
        raise RuntimeError(f"Path not allowlisted: {relative}")
    if "/" in name and name not in ("HashCaches/ZA", "PokeDocs-Supplement/ZA"):
        raise RuntimeError(f"Unexpected nested source: {name}")
    head = git("rev-parse", "HEAD", cwd=source)
    if head != spec["sourceCommit"]:
        raise RuntimeError(f"Source SHA mismatch: expected {spec['sourceCommit']}, actual {head}")
    src = source / relative
    dest = destination / relative
    if not src.is_dir():
        raise RuntimeError(f"Missing pinned source directory: {src}")
    if dest.exists():
        raise RuntimeError(f"Existing target {dest} must never be overwritten")
    raw = git("ls-tree", "-r", "HEAD", "--", relative, cwd=source)
    entries = [line for line in raw.splitlines() if line]
    if not entries:
        raise RuntimeError("No source entries")
    for line in entries:
        mode = line.split(" ", 1)[0]
        if mode not in ("100644", "100755"):
            raise RuntimeError(f"Prohibited gitlink/symlink/unexpected mode: {line[:200]}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    files = [p for p in dest.rglob("*") if p.is_file()]
    if len(files) != len(entries):
        raise RuntimeError(f"File count mismatch: expected {len(entries)}, received {len(files)}")
    print(json.dumps({"name": name, "files": len(files), "sourceCommit": head}, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--name", required=True)
    options = parser.parse_args()
    source = options.source.resolve()
    destination = options.destination.resolve()
    spec = json.loads(options.spec.read_text(encoding="utf-8"))
    if spec.get("schemaVersion") != 1 or spec.get("sourceRepository") != "969981/SV_Resources":
        raise RuntimeError("Unexpected vendor import request")
    copy_one(source, destination, spec, options.name)

if __name__ == "__main__":
    main()
