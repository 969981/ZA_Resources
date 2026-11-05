#!/usr/bin/env python3
"""Recover verified 2-pack ZA Trinity extraction from an existing Actions artifact.

Rejects missing provenance, mismatched file hashes and unsafe paths. It never
touches original RomFS/ExeFS sources, and does not claim full extraction.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

REL = Path("Unpack/v2.0.2/romfs/arc/data.trpfs")
EXPECTED_HASHES = 2
EXPECTED_BYTES = 122072

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()

def recover(artifact: Path, repo: Path) -> dict:
    matches = list(artifact.rglob("batch_summary.json"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one batch_summary.json, found {len(matches)}")
    root = matches[0].parent.parent
    if not (root / "_index" / "export.jsonl").is_file():
        raise RuntimeError("No native export.jsonl for artifact")
    summary = json.loads(matches[0].read_text(encoding="utf-8"))
    if summary.get("failedFileCount") != 0 or summary.get("verifiedExtractedFileCount") != EXPECTED_HASHES:
        raise RuntimeError(f"Native extraction counts inconsistent: {summary}")
    if summary.get("verifiedExtractedBytes") != EXPECTED_BYTES:
        raise RuntimeError("Native extraction bytes differ from logged Windows run")
    if summary.get("descriptorIndex") != 238546:
        raise RuntimeError("Native TRPFD inventory differs")
    descriptor = root / "_index" / "descriptor_summary.json"
    if not descriptor.is_file():
        raise RuntimeError("Missing real TRPFD descriptor summary")
    d = json.loads(descriptor.read_text(encoding="utf-8"))
    if d.get("descriptorFiles") != 238546 or d.get("packCount") != 13181:
        raise RuntimeError("Unexpected descriptor inventory")
    latest = {}
    for line in (root / "_index" / "export.jsonl").read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            row = json.loads(line)
            latest[row["Hash"]] = row
    if len(latest) != EXPECTED_HASHES or any(row["Status"] != "OK" for row in latest.values()):
        raise RuntimeError("Original export records differ from complete 2-pack smoke test")
    for row in latest.values():
        name = row["Name"]
        parts = name.replace("\\", "/").split("/")
        if not name or name.startswith("/") or ":" in name or any(p in ("", ".", "..") for p in parts):
            raise RuntimeError("Unsafe resource path: "+repr(name))
        virtual = root / "virtual" / Path(*parts)
        if not virtual.is_file() or virtual.stat().st_size != row["Size"] or sha(virtual) != row["Sha256"].upper():
            raise RuntimeError("Extracted resource bytes not reproducible: "+name)
    dest = repo / REL
    # Copy only this ZIP's verified generated files. Preserve other tracked files.
    copied = []
    for source in sorted(root.rglob("*")):
        if not source.is_file():
            continue
        rel = source.relative_to(root)
        if ".." in rel.parts or any(p in ("", ".", "..") for p in rel.parts):
            raise RuntimeError("Unsafe artifact path")
        target = dest / rel
        if target.is_file():
            if sha(target) != sha(source):
                if rel.as_posix() == "_index/descriptor_summary.json":
                    old_summary = json.loads(target.read_text(encoding="utf-8"))
                    new_summary = json.loads(source.read_text(encoding="utf-8"))
                    keys = ("sourceSha256", "cacheSha256", "descriptorFiles",
                            "namedFiles", "unnamedFiles", "packCount")
                    if any(str(old_summary.get(k)).upper() != str(new_summary.get(k)).upper() for k in keys):
                        raise RuntimeError("Native descriptor inventory conflicts with separately published index")
                    print("Kept already-verified native descriptor summary")
                elif rel.as_posix() == "_index/file_index.tsv.gz":
                    import gzip
                    with gzip.open(target, "rb") as earlier, gzip.open(source, "rb") as later:
                        if earlier.read().decode("utf-8-sig").splitlines() != later.read().decode("utf-8-sig").splitlines():
                            raise RuntimeError("Native file index semantic content conflict")
                    print("Kept equivalent native file index (gzip stream bytes differ)")
                elif rel.as_posix() == "_index/pack_index.tsv":
                    if target.read_text(encoding="utf-8-sig").splitlines() != source.read_text(encoding="utf-8-sig").splitlines():
                        raise RuntimeError("Native pack index content conflict")
                    print("Kept equivalent native pack index")
                else:
                    raise RuntimeError("Existing output differs, not overwriting: "+str(rel))
        elif target.exists():
            raise RuntimeError("Nonfile path conflicts: "+str(rel))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        copied.append(rel.as_posix())
    print(json.dumps({"status": "RECOVERED_AND_VERIFIED",
                      "source": "GitHub Actions run 42007205332, artifact 13405648302",
                      "verifiedNativeFiles": len(latest),
                      "verifiedNativeBytes": EXPECTED_BYTES,
                      "copiedArtifactFiles": copied}, ensure_ascii=False, indent=2))
    return summary

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = p.parse_args()
    recover(args.artifact.resolve(), args.repo_root.resolve())

if __name__ == "__main__":
    main()
