#!/usr/bin/env python3
"""ZA v2.0.2 virtual -> virtual_converted: auditable, resumable native-file pass.

No filename extension is by itself proof that a format has been decoded.
UNSUPPORTED and STRUCTURE_ONLY remain explicit work items, not successes.
"""
from __future__ import annotations

import argparse
import concurrent.futures as futures
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

VERSION = "za-virtual-convert-2-dat"
ROOT = Path("Unpack/v2.0.2/romfs/arc/data.trpfs")
LIMIT = 90 * 1024 * 1024
MAX_DECODE = 128 * 1024 * 1024
VOL_RE = re.compile(r"^(?P<stem>.+)\.7z\.(?P<part>[0-9]{3})$", re.IGNORECASE)
FBS_EXT = {".trmdl", ".trmsh", ".trskl", ".tranm", ".trmmt", ".trmtr",
           ".trmbf", ".tracm", ".traef", ".trscn", ".trres", ".trmap"}
TEXT_EXT = {".txt", ".csv", ".tsv", ".json", ".xml", ".yaml", ".yml"}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".za-convert-partial")
    try:
        tmp.write_bytes(data)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def json_bytes(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def ahtb(data: bytes) -> dict:
    if len(data) < 8 or data[:4] != b"AHTB":
        raise ValueError("invalid AHTB header")
    count = struct.unpack_from("<I", data, 4)[0]
    if count > 1_000_000:
        raise ValueError("unreasonable AHTB entry count")
    pos, rows = 8, []
    for i in range(count):
        if pos + 10 > len(data):
            raise ValueError("truncated AHTB entry")
        key, length = struct.unpack_from("<QH", data, pos)
        pos += 10
        if length == 0 or pos + length > len(data):
            raise ValueError("invalid AHTB string length")
        raw = data[pos:pos + length]
        pos += length
        name = raw.rstrip(b"\0").decode("utf-8", "strict")
        rows.append({"index": i, "hash": f"{key:016X}", "name": name})
    if any(x != 0 for x in data[pos:]):
        raise ValueError("unexpected nonzero AHTB tail")
    return {"format": "AHTB", "count": count, "entries": rows}


def dat_header(data: bytes) -> dict:
    if len(data) < 20:
        raise ValueError("short DAT header")
    section, count, declared, initial_key, offset = struct.unpack_from("<HHIIi", data)
    if not (0 <= offset <= len(data) - 4 and count <= 1_000_000):
        raise ValueError("invalid DAT section pointers")
    section_length = struct.unpack_from("<I", data, offset)[0]
    if section_length > len(data) - offset:
        raise ValueError("DAT section length exceeds physical file")
    return {"format": "Trinity message DAT", "textSectionCount": section,
            "textCount": count, "declaredLength": declared, "initialKey": initial_key,
            "sectionOffset": offset, "sectionLength": section_length,
            "note": "Header verified; encoded text and key-to-string join NOT decoded."}



def decode_message_dat(data: bytes) -> dict:
    """Decode authenticated GF/Trinity UTF-16 message slots, not hash/name joins.

    Verified on ZA 2.0.2 English, Simp_Chinese and JPN bag.dat. The high
    16 bits of entry length carry flags; low 16 bits are UTF-16 units.
    Every slot starts with key (0x7c89 + index * 0x2983) mod 65536.
    Rotate key left by three bits after each encrypted UTF-16 unit.
    """
    result = dat_header(data)
    if result["textSectionCount"] != 1:
        raise ValueError("multi-section DAT requires another native decoder")
    count = result["textCount"]
    offset = result["sectionOffset"]
    section_end = offset + result["sectionLength"]
    table_begin = offset + 4
    table_end = table_begin + count * 8
    if table_end > section_end:
        raise ValueError("DAT entry table exceeds section bounds")
    slots = []
    for index in range(count):
        rel, packed_length = struct.unpack_from("<II", data, table_begin + index * 8)
        code_units = packed_length & 0xFFFF
        flags = packed_length >> 16
        start = offset + rel
        end = start + code_units * 2
        if start < table_end or end > section_end:
            raise ValueError(f"DAT text slot {index} exceeds declared section")
        key = (0x7C89 + index * 0x2983) & 0xFFFF
        decoded = []
        for i in range(code_units):
            encrypted = struct.unpack_from("<H", data, start + i * 2)[0]
            decoded.append(encrypted ^ key)
            key = ((key << 3) | (key >> 13)) & 0xFFFF
        trimmed = list(decoded)
        while trimmed and trimmed[-1] == 0:
            trimmed.pop()
        rendered = []
        control_units = 0
        for unit in trimmed:
            if unit == 0x0A:
                rendered.append("\n")
            elif unit == 0x09:
                rendered.append("\t")
            elif (unit < 0x20 or 0xD800 <= unit <= 0xDFFF or
                  0xE000 <= unit <= 0xF8FF):
                rendered.append(f"<U+{unit:04X}>")
                control_units += 1
            else:
                rendered.append(chr(unit))
        slots.append({
            "index": index, "offsetInSection": rel,
            "utf16Units": code_units, "flagsUpper16": flags,
            "trailingZeroPaddingUnits": len(decoded) - len(trimmed),
            "displayText": "".join(rendered),
            "rawDecodedUtf16Hex": "".join(f"{u:04X}" for u in decoded),
            "escapedControlUnits": control_units
        })
    result["format"] = "GF Trinity encrypted UTF-16 message DAT"
    result["decoding"] = "confirmed-per-slot-XOR-rotate3-index-seed"
    result["messages"] = slots
    result["note"] = ("UTF-16 code units decrypted; control markers kept as U+ tokens. "
                      "AHTB hash/name matching is NOT inferred by position.")
    return result


def flatbuffer_structure(data: bytes) -> dict:
    if len(data) < 12:
        raise ValueError("short FlatBuffer")
    root = struct.unpack_from("<I", data)[0]
    if root < 4 or root + 4 > len(data):
        raise ValueError("invalid FlatBuffer root")
    rel = struct.unpack_from("<i", data, root)[0]
    vtable = root - rel
    if vtable < 4 or vtable + 4 > len(data):
        raise ValueError("invalid FlatBuffer vtable offset")
    vsize, objsize = struct.unpack_from("<HH", data, vtable)
    if vsize < 4 or vsize % 2 or objsize < 4 or vtable + vsize > len(data) or root + objsize > len(data):
        raise ValueError("invalid FlatBuffer object bounds")
    fields = [struct.unpack_from("<H", data, vtable + i)[0]
              for i in range(4, vsize, 2)]
    if any(x and x >= objsize for x in fields):
        raise ValueError("invalid FlatBuffer field offset")
    return {"format": "FlatBuffer-compatible table", "rootOffset": root,
            "vtableOffset": vtable, "objectSize": objsize,
            "fieldOffsets": fields,
            "note": "Root table structure only; schema-specific fields, geometry, skeleton and animation NOT converted."}


def safe_rel(name: str) -> Path:
    p = Path(name)
    if p.is_absolute() or any(s in ("", ".", "..") for s in p.parts) or "\\" in name or ":" in name:
        raise ValueError("unsafe archive entry path")
    return p


def archive_outputs(original: Path, seven_zip: str) -> list[dict]:
    if original.stat().st_size < LIMIT:
        return [{"path": original, "size": original.stat().st_size, "sha256": sha(original)}]
    target = original.with_name(original.name + ".7z")
    subprocess.run([seven_zip, "a", "-t7z", "-mx=1", "-v90m", str(target), original.name],
                   cwd=original.parent, check=True, stdout=subprocess.DEVNULL)
    parts = sorted(original.parent.glob(original.name + ".7z.*"))
    if not parts or parts[0].suffix != ".001":
        raise RuntimeError("split archive missing .001")
    for i, part in enumerate(parts, 1):
        if part.suffix != f".{i:03d}" or not 0 < part.stat().st_size <= LIMIT:
            raise ValueError("invalid 7z volume sequence")
    subprocess.run([seven_zip, "t", str(parts[0])], check=True, stdout=subprocess.DEVNULL)
    with tempfile.TemporaryDirectory(prefix="za-converted-check-") as td:
        subprocess.run([seven_zip, "x", "-y", "-o" + td, str(parts[0])],
                       check=True, stdout=subprocess.DEVNULL)
        restored = Path(td) / original.name
        if not restored.is_file() or sha(restored) != sha(original):
            raise ValueError("converted archive roundtrip SHA256 mismatch")
    original.unlink()
    return [{"path": x, "size": x.stat().st_size, "sha256": sha(x)}
            for x in parts]


def transform(source: Path, logical: str, dest: Path) -> tuple[str, list[Path], str]:
    ext = source.suffix.lower()
    data = source.read_bytes() if source.stat().st_size <= MAX_DECODE else None
    if ext == ".tbl":
        if data is None:
            return "UNSUPPORTED", [], "AHTB input exceeds size limit"
        result = ahtb(data)
        target = dest / (logical + ".json")
        atomic(target, json_bytes(result))
        return "CONVERTED", [target], "AHTB hash/name list decoded; text association remains unverified"
    if ext == ".dat" and "ik_message/" in logical:
        if data is None:
            return "UNSUPPORTED", [], "message DAT exceeds size limit"
        header = dat_header(data)
        if header["textSectionCount"] != 1:
            target = dest / (logical + ".structure.json")
            atomic(target, json_bytes(header))
            return "STRUCTURE_ONLY", [target], "Multi-section DAT not yet decoded"
        target = dest / (logical + ".json")
        result = decode_message_dat(data)
        atomic(target, json_bytes(result))
        return "CONVERTED", [target], "Decrypted each UTF-16 slot; control units retained"
    if ext in FBS_EXT:
        if data is None:
            return "UNSUPPORTED", [], "large Trinity binary requires native adapter"
        try:
            metadata = flatbuffer_structure(data)
        except ValueError as e:
            return "UNSUPPORTED", [], "FlatBuffer validation not proven: " + str(e)
        target = dest / (logical + ".structure.json")
        atomic(target, json_bytes(metadata))
        return "STRUCTURE_ONLY", [target], metadata["note"]
    if ext in TEXT_EXT:
        if data is None:
            return "UNSUPPORTED", [], "large text requires streaming adapter"
        text = data.decode("utf-8-sig", "strict")
        if ext == ".json":
            normalized = json_bytes(json.loads(text))
            newext = ".json"
        elif ext == ".xml":
            ET.fromstring(text)
            normalized, newext = text.encode("utf-8"), ".xml"
        elif ext in (".csv", ".tsv"):
            list(csv.reader(io.StringIO(text), delimiter="," if ext == ".csv" else "\t"))
            normalized, newext = text.encode("utf-8"), ext
        else:
            normalized, newext = text.encode("utf-8"), ext
        target = dest / (logical + ".normalized" + newext)
        atomic(target, normalized)
        return "CONVERTED", [target], "Strict text decoding/validation"
    if ext in (".gz", ".gzip") and data is not None:
        with gzip.GzipFile(fileobj=io.BytesIO(data), mode="rb") as stream:
            expanded = stream.read(MAX_DECODE + 1)
        if len(expanded) > MAX_DECODE:
            return "UNSUPPORTED", [], "expanded size limit exceeded"
        target = dest / (logical + ".decompressed")
        atomic(target, expanded)
        return "EXTRACTED_ONLY", [target], "GZIP extracted; inner format not interpreted"
    if ext == ".zip" and data is not None:
        paths = []
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            members = z.infolist()
            if len(members) > 5000 or sum(x.file_size for x in members) > MAX_DECODE:
                return "UNSUPPORTED", [], "archive extraction limits exceeded"
            for entry in members:
                if entry.is_dir():
                    continue
                rel = safe_rel(entry.filename)
                target = dest / (logical + ".extracted") / rel
                atomic(target, z.read(entry))
                paths.append(target)
        return "EXTRACTED_ONLY", paths, "ZIP extracted; members require further format processing"
    return "UNSUPPORTED", [], "No validated native decoder for this file type"


def enumerated_sources(source: Path):
    found = []
    for root, directories, names in os.walk(source, followlinks=False):
        directories[:] = sorted(n for n in directories if not (Path(root) / n).is_symlink())
        for n in sorted(names):
            file = Path(root) / n
            if file.is_symlink():
                raise ValueError("symlink encountered in original virtual tree: " + str(file))
            found.append(file)
    return found


def load_previous(path: Path):
    old = {}
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                old[obj["sourcePath"]] = obj
    return old


def convert_one(file: Path, source_root: Path, dest: Path,
                previous: dict, seven_zip: str):
    relative = file.relative_to(source_root).as_posix()
    rec = {"sourcePath": relative, "sourceBytes": file.stat().st_size,
           "sourceSha256": sha(file), "converterVersion": VERSION,
           "status": "PENDING", "outputs": [], "message": ""}
    prior = previous.get(relative)
    if prior and all(prior.get(k) == rec.get(k) for k in
                     ("sourcePath", "sourceBytes", "sourceSha256", "converterVersion")):
        outputs = prior.get("outputs", [])
        if all((dest / v["path"]).is_file() and
               (dest / v["path"]).stat().st_size == v["bytes"] and
               sha(dest / v["path"]) == v["sha256"] for v in outputs):
            return prior
    vol = VOL_RE.match(file.name)
    if vol and vol.group("part") != "001":
        rec.update(status="VOLUME_PART", message="Part of original split 7z, decoded via .001")
        return rec
    logical = relative[: -len(".7z.001")] if vol else relative
    try:
        with tempfile.TemporaryDirectory(prefix="za-original-volume-") as td:
            actual = file
            if vol:
                subprocess.run([seven_zip, "t", str(file)], check=True, stdout=subprocess.DEVNULL)
                subprocess.run([seven_zip, "x", "-y", "-o" + td, str(file)],
                               check=True, stdout=subprocess.DEVNULL)
                extracted = [p for p in Path(td).rglob("*") if p.is_file()]
                if len(extracted) != 1 or extracted[0].name != Path(logical).name:
                    raise ValueError("split 7z must restore exactly its original basename")
                actual = extracted[0]
            status, paths, message = transform(actual, logical, dest)
            out_records = []
            for target in paths:
                original_hash = sha(target)
                original_bytes = target.stat().st_size
                for item in archive_outputs(target, seven_zip):
                    out_records.append({"path": item["path"].relative_to(dest).as_posix(),
                                        "bytes": item["size"], "sha256": item["sha256"],
                                        "decodedBytes": original_bytes,
                                        "decodedSha256": original_hash})
            rec.update(status=status, outputs=out_records, message=message)
    except Exception as e:
        rec.update(status="FAILED", message=f"{type(e).__name__}: {e}"[:400])
    return rec


def write_inventory(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".za-convert-partial")
    try:
        with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--category", required=True,
                        help="One real directory under virtual, e.g. ik_pokemon")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seven-zip", default="7z")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9_]+", args.category) or not 1 <= args.workers <= 16:
        parser.error("invalid category or workers")
    repo = args.repo.resolve()
    source_root = repo / ROOT / "virtual"
    source = source_root / args.category
    dest = repo / ROOT / "virtual_converted"
    if not source.is_dir():
        raise FileNotFoundError("Source category not checked out: " + str(source))
    inventory = dest / "_index" / (args.category + ".jsonl.gz")
    summary_path = dest / "_index" / (args.category + ".summary.json")
    previous = load_previous(inventory)
    inputs = enumerated_sources(source)
    if not inputs:
        raise RuntimeError("No source files in category; refusing empty audit")
    results = []
    with futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        tasks = [pool.submit(convert_one, p, source_root, dest, previous, args.seven_zip)
                 for p in inputs]
        for i, item in enumerate(futures.as_completed(tasks), 1):
            results.append(item.result())
            if i % 500 == 0:
                print(f"{args.category}: {i}/{len(inputs)} originals audited", flush=True)
    results.sort(key=lambda x: x["sourcePath"])
    if len({r["sourcePath"] for r in results}) != len(inputs):
        raise RuntimeError("duplicate or unaccounted original file")
    statuses = {k: sum(x["status"] == k for x in results)
                for k in ("CONVERTED", "EXTRACTED_ONLY", "STRUCTURE_ONLY",
                          "UNSUPPORTED", "VOLUME_PART", "FAILED")}
    progress_file = repo / ROOT / "_index" / "full-extract-progress.json"
    progress = json.loads(progress_file.read_text(encoding="utf-8")) if progress_file.exists() else {}
    summary = {"schemaVersion": 1, "converterVersion": VERSION,
               "category": args.category, "originalFilesAccounted": len(results),
               "originalBytes": sum(x["sourceBytes"] for x in results),
               "statusCounts": statuses, "sourceTrinityPackProgress": {
                   "nextPack": progress.get("nextPack"),
                   "totalPacks": progress.get("totalPacks"),
                   "state": progress.get("state")},
               "allNativeSourcesPresent": progress.get("state") == "COMPLETE",
               "fullyConverted": (progress.get("state") == "COMPLETE"
                                  and statuses["EXTRACTED_ONLY"] == 0
                                  and statuses["STRUCTURE_ONLY"] == 0
                                  and statuses["UNSUPPORTED"] == 0
                                  and statuses["FAILED"] == 0)}
    write_inventory(inventory, results)
    atomic(summary_path, json_bytes(summary))
    if args.publish:
        import runpy
        publish = runpy.run_path(str(repo / "scripts/Run-ZA-FullExtract.py"))["git_commit_and_push"]
        files = [inventory, summary_path]
        files.extend(dest / y["path"] for row in results for y in row["outputs"])
        publish(repo, [x.relative_to(repo).as_posix() for x in files],
                "data(za): auditable virtual conversion " + args.category, False)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if statuses["FAILED"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
