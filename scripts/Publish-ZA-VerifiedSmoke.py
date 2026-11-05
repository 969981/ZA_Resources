#!/usr/bin/env python3
"""Publish verified ZA native smoke outputs using the isolated-index Git path.

This is deliberately separate from extraction; original game archives are
never staged, and independently published descriptor indices are preserved.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path

ROOT_REL = Path("Unpack/v2.0.2/romfs/arc/data.trpfs")
EVIDENCE = ("trpfs-restore.json", "export.jsonl", "batch_summary.json")

def file_list(repo: Path) -> list[str]:
    out = repo / ROOT_REL
    summary = json.loads((out / "_index/batch_summary.json").read_text(encoding="utf-8"))
    if (summary.get("status") != "VERIFIED_WINDOW"
            or summary.get("failedFileCount") != 0
            or summary.get("verifiedExtractedFileCount", 0) < 1):
        raise RuntimeError("No successful verified native extraction in index")
    allowed = [out / "_index" / x for x in EVIDENCE]
    allowed += sorted((out / "virtual").rglob("*"))
    verified = []
    for p in allowed:
        if p.is_dir():
            continue
        if not p.is_file() or p.stat().st_size >= 100_000_000:
            raise RuntimeError("Required evidence missing or file exceeds GitHub blob limit: " + str(p))
        verified.append(p.relative_to(repo).as_posix())
    if len(verified) <= len(EVIDENCE):
        raise RuntimeError("No actual virtual files to publish")
    return verified

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = p.parse_args()
    root = args.repo_root.resolve()
    spec = importlib.util.spec_from_file_location("za_full", root / "scripts" / "Run-ZA-FullExtract.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Full publisher source missing")
    full = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(full)
    paths = file_list(root)
    print(f"Publishing {len(paths)} verified smoke artifacts without pull/rebase on dirty worktree")
    full.git_commit_and_push(root, paths,
        "data(za): verified native TRPFS smoke extraction and source checks", False)

if __name__ == "__main__":
    main()
