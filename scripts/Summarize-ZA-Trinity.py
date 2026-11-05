#!/usr/bin/env python3
"""Verify ZA Trinity batch exports and report exact success/failure, never inferred completion."""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()

def summarize(output: Path, source_descriptor: Path | None = None) -> dict:
    log = output / "_index" / "export.jsonl"
    if not log.is_file():
        raise FileNotFoundError(log)
    latest = {}
    errors = Counter()
    line_count = 0
    for line in log.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        line_count += 1
        row = json.loads(line)
        h = row["Hash"].upper()
        if len(h) != 16:
            raise ValueError("Invalid 64-bit hash in export log")
        latest[h] = row
        if row["Status"] == "FAILED":
            errors[str(row.get("Error") or "Unknown failure").split(":")[0]] += 1
    stats = Counter(row["Status"] for row in latest.values())
    nbytes = 0
    output_files = 0
    virtual = output / "virtual"
    for row in latest.values():
        if row["Status"] != "OK":
            continue
        name = row["Name"]
        if not name or ".." in name.replace("\\", "/").split("/"):
            raise ValueError("Unsafe virtual output path")
        actual = virtual / Path(name.replace("\\", "/"))
        if not actual.is_file() or digest(actual) != row["Sha256"].upper() or actual.stat().st_size != row["Size"]:
            raise RuntimeError("Exported file failed byte/sha verification: " + name)
        output_files += 1
        nbytes += actual.stat().st_size
    result = {
        "status": "PARTIAL" if stats["FAILED"] else "VERIFIED_WINDOW",
        "batchLogEntries": line_count,
        "uniqueHashEntries": len(latest),
        "verifiedExtractedFileCount": output_files,
        "verifiedExtractedBytes": nbytes,
        "failedFileCount": stats["FAILED"],
        "failureGroups": dict(errors.most_common(30)),
        "sourceType": "native TRPFD + original TRPFS archive",
        "completenessClaim": "Window only; compare against descriptorFiles=238546 and packCount=13181 before claiming full extraction.",
        "sha256Verification": "Full byte-by-byte rehash of every successful output",
    }
    if source_descriptor and source_descriptor.is_file():
        result["descriptorIndex"] = json.loads(source_descriptor.read_text(encoding="utf-8"))["descriptorFiles"]
    target = output / "_index" / "batch_summary.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--descriptor-summary", type=Path)
    a = p.parse_args()
    summarize(a.output.resolve(), a.descriptor_summary.resolve() if a.descriptor_summary else None)

if __name__ == "__main__":
    main()
