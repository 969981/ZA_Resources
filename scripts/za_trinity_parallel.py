#!/usr/bin/env python3
"""Isolated multiprocess ZA Trinity decoder used by Run-ZA-FullExtract.

Workers are independent .NET processes with separate outputs and JSONL. The
coordinator alone promotes SHA-256-verified files to the shared virtual root
and publishes one contiguous pack window. This avoids shared FileStream,
Oodle native state, FileStreamWriter and output-path races.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

_HEX16 = re.compile(r"^[0-9A-Fa-f]{16}$")


def sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as fp:
        for data in iter(lambda: fp.read(4 * 1024 * 1024), b""):
            sha.update(data)
    return sha.hexdigest().upper()


def ranges(start: int, end: int, workers: int) -> list[tuple[int, int]]:
    if start < 0 or end <= start or not 1 <= workers <= 8:
        raise ValueError("Invalid pack window or worker count")
    count = min(end - start, workers)
    result = [(start + (end-start)*i//count,
               start + (end-start)*(i+1)//count) for i in range(count)]
    assert result[0][0] == start and result[-1][1] == end
    assert all(a < b for a, b in result)
    assert all(result[i][1] == result[i+1][0] for i in range(len(result)-1))
    return result


def safe_file(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name or ":" in name or name.startswith("/"):
        raise ValueError("Unsafe decoded resource name: " + repr(name))
    parts = name.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise ValueError("Unsafe path components: " + repr(name))
    base = root.resolve()
    target = (base / name).resolve()
    if not target.is_relative_to(base):
        raise ValueError("Decoded name escapes virtual root")
    return target


def load_pack_counts(index: Path) -> list[int]:
    """Read per-pack native referenced file counts, fail closed on bad order."""
    from csv import reader
    with index.open("r", encoding="utf-8-sig", newline="") as f:
        rows = reader(f, delimiter="\t")
        head = next(rows)
        if head[:3] != ["pack_index", "pack_name", "referenced_files"]:
            raise ValueError("Unexpected original native pack index header")
        counts = []
        for line in rows:
            if not line:
                continue
            if len(line) < 3 or int(line[0]) != len(counts):
                raise ValueError(f"Native pack index not ordered at {len(counts)}")
            count = int(line[2])
            if count < 0:
                raise ValueError("Negative native Pack file count")
            counts.append(count)
    if len(counts) != 13181:
        raise ValueError(f"Native ZA pack count mismatch: {len(counts)} != 13181")
    return counts


def _decode_worker(prefix: list[str], workspace: Path, root: Path, cache: Path,
                   oodle: Path, a: int, b: int, worker_id: int) -> dict:
    out = root / f"worker-{worker_id:02}"
    out.mkdir(parents=True, exist_ok=True)
    report = out / "_index" / "export.jsonl"
    report.parent.mkdir(parents=True, exist_ok=True)
    logfile = root / f"worker-{worker_id:02}.log"
    cmd = [*prefix, "--romfs", str(workspace), "--output", str(out),
           "--cache", str(cache), "--oodle", str(oodle),
           "--start-pack", str(a), "--max-packs", str(b-a),
           "--report", str(report)]
    start = time.monotonic()
    with logfile.open("w", encoding="utf-8") as log:
        # Separate process, own FileStream and Oodle runtime; not merely Python threads.
        result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT,
                                timeout=1800, check=False)
    elapsed = time.monotonic()-start
    if result.returncode not in (0, 1):
        tail = logfile.read_text(encoding="utf-8", errors="replace")[-4000:]
        raise RuntimeError(f"Native worker {worker_id} pack {a}-{b-1} "
                           f"fatal exit {result.returncode}; log tail:\n{tail}")
    if not report.is_file():
        raise RuntimeError(f"Native worker {worker_id} produced no JSONL report")
    rows = []
    with report.open("r", encoding="utf-8-sig") as f:
        for raw in f:
            if raw.strip():
                rows.append(json.loads(raw))
    if not rows:
        raise RuntimeError(f"Native worker {worker_id} reported zero records")
    return {"id": worker_id, "from": a, "to": b,
            "durationSeconds": round(elapsed,3), "exitCode": result.returncode,
            "root": out, "rows": rows, "log": logfile}


def _promote(source: Path, target: Path, expected_size: int, expected_sha: str) -> None:
    if not source.is_file():
        raise FileNotFoundError("Native worker OK row has no file: " + str(source))
    if source.stat().st_size != expected_size or sha256(source) != expected_sha.upper():
        raise RuntimeError("Native worker output SHA-256 mismatch: " + str(source))
    if target.is_file():
        if target.stat().st_size != expected_size or sha256(target) != expected_sha.upper():
            raise RuntimeError("Different native hashes resolve to a conflicting output path: " + str(target))
        return
    if target.exists():
        raise RuntimeError("Native output conflicts with nonfile path: " + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".za-worker-writing")
    if temporary.exists():
        raise RuntimeError("Existing stale worker temp output: " + str(temporary))
    # Copy into the target filesystem then move atomically. Only the
    # coordinator writes shared outputs; workers never race on those paths.
    try:
        shutil.copyfile(source, temporary)
        if temporary.stat().st_size != expected_size or sha256(temporary) != expected_sha.upper():
            raise RuntimeError("Worker output changed during promotion: " + str(source))
        temporary.rename(target)
    finally:
        if temporary.exists():
            temporary.unlink()


def parallel_decode(*, repo: Path, workspace: Path, output: Path, report: Path,
                    cache: Path, oodle: Path, start: int, end: int, workers: int,
                    pack_counts: list[int], command_prefix: list[str] | None = None) -> dict:
    """Extract contiguous native pack window via bounded independent processes.

    Each worker gets a disjoint pack interval and isolated temp output. The
    coordinator checks every expected hash and output SHA and writes one
    merged JSONL used by the legacy publisher and final audit. No progress
    or Git state is touched in this function.
    """
    spans = ranges(start, end, workers)
    if end > len(pack_counts):
        raise ValueError("Pack window exceeds native descriptor")
    prefix = command_prefix or [
        "dotnet", str(repo / "tools/ZA.TrinityDump/bin/Release/net8.0/ZA.TrinityDump.dll")]
    report.parent.mkdir(parents=True, exist_ok=True)
    if report.exists() or report.with_name(report.name+".za-worker-writing").exists():
        raise RuntimeError("Batch report already exists; refusing to append stale records: "+str(report))
    output_virtual = output / "virtual"
    staging = Path(os.environ.get("RUNNER_TEMP") or tempfile.gettempdir())
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="za-trinity-parallel-", dir=staging) as temp:
        worker_root = Path(temp)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(spans)) as pool:
            futures = [
                pool.submit(_decode_worker, prefix, workspace, worker_root, cache, oodle,
                            a,b,i) for i,(a,b) in enumerate(spans)]
            results = [future.result() for future in futures]
        results.sort(key=lambda r: r["id"])
        consolidated = []
        unique_hashes: set[str] = set()
        stats = []
        for result in results:
            worker_hashes = set()
            ok = fail = 0
            for row in result["rows"]:
                if not isinstance(row, dict):
                    raise ValueError("Native worker reported a non-object JSON row")
                hashval = str(row.get("Hash", ""))
                if not _HEX16.fullmatch(hashval):
                    raise ValueError("Worker record has invalid native 64-bit Hash")
                hashval = hashval.upper()
                if hashval in unique_hashes:
                    raise RuntimeError("Duplicate Hash appears in separate worker pack ranges: "+hashval)
                unique_hashes.add(hashval)
                worker_hashes.add(hashval)
                status = row.get("Status")
                if status == "OK":
                    name = row.get("Name")
                    target = safe_file(output_virtual, name)
                    source = safe_file(result["root"] / "virtual", name)
                    size = row.get("Size")
                    digest = row.get("Sha256")
                    if not isinstance(size, int) or size < 0 or not isinstance(digest, str):
                        raise RuntimeError("Native OK record has invalid byte length or SHA")
                    _promote(source, target, size, digest)
                    row["OutputPath"] = str(target)
                    ok += 1
                elif status == "FAILED":
                    # Preserve exactly why a resource failed; only final
                    # audit can establish true completeness.
                    if row.get("Name") not in (None, "_missing", "_pack_failed"):
                        row["OutputPath"] = str(safe_file(output_virtual, row["Name"]))
                    else:
                        row["OutputPath"] = None
                    fail += 1
                else:
                    raise RuntimeError("Unexpected native worker record status: "+str(status))
                consolidated.append(row)
            expected = sum(pack_counts[result["from"]:result["to"]])
            if len(worker_hashes) != expected:
                raise RuntimeError(f"Worker {result['id']} Pack {result['from']}..{result['to']-1} "
                                   f"native count mismatch: expected {expected}, actual {len(worker_hashes)}")
            if result["exitCode"] == 1 and fail == 0:
                raise RuntimeError("Worker exited with failure code without FAILED rows")
            if result["exitCode"] == 0 and fail != 0:
                raise RuntimeError("Worker exited success but reported FAILED rows")
            stats.append({"workerId": result["id"], "startPack":result["from"],
                          "endPackExclusive":result["to"], "ok":ok,
                          "failed":fail, "seconds":result["durationSeconds"]})
        expected_total = sum(pack_counts[start:end])
        if len(unique_hashes) != expected_total:
            raise RuntimeError("Parallel merge is incomplete versus original TRPFD descriptor")
        temp_report = report.with_name(report.name + ".za-worker-writing")
        try:
            with temp_report.open("x", encoding="utf-8", newline="\n") as out:
                for row in consolidated:
                    out.write(json.dumps(row, separators=(",",":"), ensure_ascii=False)+"\n")
            temp_report.rename(report)
        finally:
            if temp_report.exists():
                temp_report.unlink()
    data = {"workers":len(spans), "workerRanges":stats,
            "decodeSeconds":round(time.monotonic()-t0,3),
            "records":len(unique_hashes),
            "failed":sum(r["failed"] for r in stats)}
    print("ZA multiprocess native extraction " + json.dumps(data,ensure_ascii=False),flush=True)
    return data
