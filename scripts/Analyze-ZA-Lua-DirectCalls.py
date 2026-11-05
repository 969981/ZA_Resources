#!/usr/bin/env python3
"""Locate *adjacent* native Lua 5.4 field-read -> CALL/TAILCALL edges.

Reads four already-extracted, SHA-256 verified ZA 2.0.2 .blua files.
Only directly adjacent instructions with the same function register count.
Never infer an original identifier name, receiver class, or dynamic call path.
No raw game bytes are copied into derived TSV/JSON reports.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LUA_ROOT = ROOT / "Unpack/v2.0.2/romfs/arc/data.trpfs/virtual"
INDEX_ROOT = ROOT / "Unpack/v2.0.2/romfs/arc/data.trpfs/_index"
NATIVE = INDEX_ROOT / "lua-native"
UNKNOWN = ROOT / "tools/PokeDocs-Supplement/ZA/Hashlists/Lua/unresolved-symbol-index.tsv"
CORE = ROOT / "scripts/_vendor/Analyze-SV-Lua54.py"
KINDS = ("s", "f", "e")
SOURCES = ("dll_util", "event_ik", "main", "main_dynamic")
COLUMNS = (
    "source", "hash_token", "proto_id", "parent_proto_id",
    "field_pc", "field_offset_hex", "field_opcode", "key_constant_index",
    "call_pc", "call_offset_hex", "call_opcode", "function_register_a",
    "evidence"
)
GRADE = "NATIVE_LUA54_ADJACENT_FIELD_CALL_EDGE"

def load_core(path: Path = CORE):
    spec = importlib.util.spec_from_file_location("za_lua54_direct_core", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing pinned Lua54 parser")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def unknown_tokens(path: Path = UNKNOWN) -> set[bytes]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    counts = Counter(row["kind"] for row in rows)
    if counts != Counter({"s": 116, "f": 43, "e": 3}):
        raise ValueError(f"Unexpected unverified ZA symbol corpus: {counts}")
    result = set()
    for row in rows:
        kind = row["kind"]
        val = row["hash"]
        if kind not in KINDS or not re.fullmatch(r"0x[0-9a-fA-F]{16}", val):
            raise ValueError("Malformed unresolved original hash row")
        result.add((kind.upper() + val[2:].upper()).encode("ascii"))
    if len(result) != 162:
        raise ValueError("Duplicate unresolved ZA symbols")
    return result

def edges(raw: bytes, source: str, targets: set[bytes], core):
    """Require GETFIELD/GETTABUP/SELF(when k==1), followed by CALL(A==A).

    An adjacent opcode pair proves local register-defined call target if the
    parser ABI is correct. It does NOT prove the name or runtime receiver type.
    """
    lua = core.Lua54(raw)
    lua.parse()
    out = []
    for proto in lua.protos:
        instructions = core.instructions(raw, proto)
        consts = proto["constants"]
        for pc in range(len(instructions) - 1):
            op, a, b, c, k, bx, ax = instructions[pc]
            call, call_a, *_ = instructions[pc + 1]
            if call not in ("CALL", "TAILCALL") or call_a != a:
                continue
            if op in ("GETFIELD", "GETTABUP"):
                keyidx = c
            elif op == "SELF" and k == 1:
                keyidx = c
            else:
                continue
            if keyidx >= len(consts):
                continue
            token = consts[keyidx]
            if token not in targets:
                continue
            code_offset = proto["code_offset"]
            out.append([
                source, token.decode("ascii"), proto["id"], proto["parent"],
                pc, f"0x{code_offset + pc * 4:X}", op, keyidx,
                pc + 1, f"0x{code_offset + (pc + 1) * 4:X}", call,
                a, GRADE
            ])
    return len(lua.protos), out

def analyze(index: Path = INDEX_ROOT / "lua_pack_locations.json",
            native_summary: Path = NATIVE / "native-lua-summary.json",
            virtual: Path = LUA_ROOT, out: Path = NATIVE,
            unknown_index: Path = UNKNOWN):
    targets = unknown_tokens(unknown_index)
    manifest = json.loads(index.read_text(encoding="utf-8"))
    summary = json.loads(native_summary.read_text(encoding="utf-8"))
    if (manifest.get("version") != "v2.0.2" or
        manifest.get("target_pack_indices") != [12145, 12146, 12147, 12148] or
        not manifest.get("all_unique")):
        raise ValueError("ZA native pack manifest identity mismatch")
    if (summary.get("version") != "v2.0.2" or
        summary.get("native_files_parsed") != 4):
        raise ValueError("Native ZA Lua 5.4 complete verification required")
    core = load_core()
    reports, all_edges = {}, []
    for source in SOURCES:
        match = manifest["targets"][source]["matches"]
        if len(match) != 1:
            raise ValueError("Duplicate/missing native source pack")
        row = match[0]
        rel = row["virtual_path"].replace("\\", "/")
        parts = Path(rel).parts
        if (rel.startswith("/") or ".." in parts or ":" in rel or
            not rel.endswith("/" + source + ".blua")):
            raise ValueError("Unsafe native path " + rel)
        f = virtual / rel
        raw = f.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        known = summary["files"][source]
        if (known["status"] != "PARSED_NATIVE_LUA54" or
            known["sha256"].lower() != digest or
            known["bytes"] != len(raw) or
            known["source_pack_index"] != row["pack_index"]):
            raise ValueError("Native source not the previously verified file: " + source)
        nproto, records = edges(raw, source, targets, core)
        reports[source] = {
            "sha256": digest, "bytes": len(raw), "prototypes": nproto,
            "direct_call_edges": len(records),
        }
        all_edges.extend(records)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "native-unknown-direct-call-edges.tsv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(all_edges)
    result = {
        "game": "Pokemon Legends Z-A", "version": "v2.0.2",
        "source_index_sha256": hashlib.sha256(index.read_bytes()).hexdigest(),
        "native_summary_sha256": hashlib.sha256(native_summary.read_bytes()).hexdigest(),
        "files": reports,
        "adjacent_field_call_edges": len(all_edges),
        "unique_unresolved_hashes_called": len({r[1] for r in all_edges}),
        "edge_grade": GRADE,
        "native_symbol_names_confirmed": 0,
        "warning": "Adjacent native field-read and CALL provide a local opcode link; original names, class receivers and non-adjacent calls remain unknown."
    }
    (out / "native-unknown-direct-call-summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack-report", type=Path, default=INDEX_ROOT / "lua_pack_locations.json")
    p.add_argument("--native-summary", type=Path, default=NATIVE / "native-lua-summary.json")
    p.add_argument("--virtual-root", type=Path, default=LUA_ROOT)
    p.add_argument("--unknown-index", type=Path, default=UNKNOWN)
    p.add_argument("--out", type=Path, default=NATIVE)
    a = p.parse_args()
    print(json.dumps(analyze(a.pack_report, a.native_summary, a.virtual_root,
                             a.out, a.unknown_index), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
