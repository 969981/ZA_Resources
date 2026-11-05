#!/usr/bin/env python3
"""Reconcile every converted ZA virtual input with the native TRPFD path index."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import gzip
import json
from pathlib import Path
import re
import runpy
import sys

ROOT = Path("Unpack/v2.0.2/romfs/arc/data.trpfs")
VOLUME = re.compile(r"\.7z\.(\d{3})$", re.IGNORECASE)


def expected_paths(file_index: Path):
    expected = {}
    repeated = []
    with gzip.open(file_index, "rt", encoding="utf-8-sig", newline="") as f:
        records = csv.DictReader(f, delimiter="\t")
        if not {"hash", "virtual_path"}.issubset(records.fieldnames or []):
            raise ValueError("unexpected original TRPFD file index columns")
        for row in records:
            name = row["virtual_path"] or "_unknown/" + row["hash"].upper() + ".bin"
            if name in expected:
                repeated.append({"path": name, "hashes": [expected[name], row["hash"]]})
            expected[name] = row["hash"]
    return expected, repeated


def inventory_records(index: Path):
    files = sorted(index.glob("*.jsonl.gz"))
    records = []
    for file in files:
        with gzip.open(file, "rt", encoding="utf-8") as stream:
            for line in stream:
                rec = json.loads(line)
                rec["inventory"] = file.name
                records.append(rec)
    return records, files


def audit(repo: Path):
    root = repo / ROOT
    descriptor = json.loads((repo / "Unpack/v2.0.2/romfs/arc/data.trpfd/descriptor_summary.json").read_text())
    progress = json.loads((root / "_index/full-extract-progress.json").read_text())
    expected, native_collisions = expected_paths(root / "_index/file_index.tsv.gz")
    rows, manifests = inventory_records(root / "virtual_converted/_index")
    logical = {}
    parts = {}
    double_paths = []
    invalid_parts = []
    for row in rows:
        original = row["sourcePath"]
        m = VOLUME.search(original)
        if m:
            base = original[:m.start()]
            parts.setdefault(base, []).append((m.group(1), row))
            if m.group(1) != "001":
                if row.get("status") != "VOLUME_PART":
                    invalid_parts.append(original)
                continue
            original = base
        if original in logical:
            double_paths.append(original)
        else:
            logical[original] = row
    for original, members in parts.items():
        indices = sorted(int(n) for n, _ in members)
        if indices != list(range(1, len(indices) + 1)):
            invalid_parts.append(original)
    missing = sorted(set(expected).difference(logical))
    extra = sorted(set(logical).difference(expected))
    statuses = Counter(row.get("status", "INVALID") for row in logical.values())
    unreadable = [{"path": p, "status": row.get("status"), "message": row.get("message")}
                  for p, row in logical.items() if row.get("status") != "CONVERTED"]
    check_complete = (progress.get("state") == "COMPLETE" and
                      progress.get("totalPacks") == progress.get("nextPack") == 13181)
    path_coverage = (len(expected) == descriptor["descriptorFiles"] and
                     not native_collisions and not double_paths and not invalid_parts
                     and not missing and not extra)
    semantic_complete = (check_complete and path_coverage and
                         statuses.get("CONVERTED", 0) == len(expected))
    return {
        "schemaVersion": 1, "version": "ZA v2.0.2",
        "nativeIndexEntries": descriptor["descriptorFiles"],
        "nativeExpectedUniquePaths": len(expected),
        "nativeIndexDuplicatePaths": native_collisions[:100],
        "checkpoint": progress,
        "categoryManifests": [x.name for x in manifests],
        "inputManifestPhysicalFiles": len(rows),
        "logicalOriginalPathsAccounted": len(logical),
        "countsByStatus": dict(sorted(statuses.items())),
        "largeFilesFromOriginalSplitArchives": len(parts),
        "nativeSourceComplete": check_complete,
        "nativePathCoverageComplete": path_coverage,
        "semanticConversionComplete": semantic_complete,
        "missingNativePathsCount": len(missing),
        "extraInputPathsCount": len(extra),
        "repeatedInputPathsCount": len(double_paths),
        "brokenOriginalArchiveGroupsCount": len(invalid_parts),
        "notFullyConvertedCount": len(unreadable),
        "missingNativePathSamples": missing[:100],
        "extraInputPathSamples": extra[:100],
        "repeatedInputPathSamples": sorted(set(double_paths))[:100],
        "brokenArchiveSamples": invalid_parts[:100],
        "unconvertedSamples": sorted(unreadable, key=lambda x: x["path"])[:250],
        "note": "Category manifests audit input SHA256 and produced output SHA256. "
                "STRUCTURE_ONLY and EXTRACTED_ONLY are NOT semantic conversion successes."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    a = parser.parse_args()
    repo = a.repo.resolve()
    result = audit(repo)
    target = repo / ROOT / "virtual_converted/_index/native-coverage-audit.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    if a.publish:
        publish = runpy.run_path(str(repo / "scripts/Run-ZA-FullExtract.py"))["git_commit_and_push"]
        publish(repo, [target.relative_to(repo).as_posix()],
                "audit(za): reconcile virtual conversion against all native TRPFD paths", False)
    print(json.dumps({k: v for k, v in result.items() if not k.endswith("Samples")
                      and k not in ("checkpoint", "nativeIndexDuplicatePaths")}, indent=2))
    if a.require_complete and not result["semanticConversionComplete"]:
        sys.exit("ZA native conversion NOT COMPLETE: inspect native-coverage-audit.json")


if __name__ == "__main__":
    main()
