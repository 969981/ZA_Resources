#!/usr/bin/env python3
"""Conservative receiver-register provenance for verified ZA Lua54 field calls.

INPUT: original ZA v2.0.2 four Lua chunks, SHA-256 checked against the
published native manifest, plus the verified native closure-context TSV.
OUTPUT: only source+proto+PC+register and bounded *lexical* register provenance.
Neither enclosing closure ownership nor GETFIELD source proves the actual
runtime receiver's class, original name, or execution.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "Unpack/v2.0.2/romfs/arc/data.trpfs"
INDEX = BASE / "_index"
NATIVE = INDEX / "lua-native"
CORE = ROOT / "scripts/_vendor/Analyze-SV-Lua54.py"
NAMES = ("dll_util", "event_ik", "main", "main_dynamic")
COLUMNS = (
    "source", "proto_id", "parent_proto_id", "called_hash_token",
    "owner_kind", "owner_class_hash", "owner_field_hash",
    "field_pc", "call_pc", "field_opcode", "receiver_register",
    "receiver_origin_kind", "receiver_origin_path", "receiver_origin_pc",
    "evidence", "runtime_receiver_class_confirmed",
)
EVIDENCE = "NATIVE_LUA54_LOCAL_RECEIVER_REGISTER_PROVENANCE"


def load_core():
    spec = importlib.util.spec_from_file_location("za_receiver_lua54", CORE)
    if spec is None or spec.loader is None:
        raise ValueError("Native Lua 5.4 parser not found")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def branch_targets(code):
    """Prevent carrying a source across an incoming control-flow join."""
    leaders = {0}
    jumps = {"FORLOOP", "FORPREP", "TFORPREP", "TFORLOOP"}
    skip = {"EQ", "LT", "LE", "EQK", "EQI", "LTI", "LEI",
            "GTI", "GEI", "TEST", "TESTSET", "LFALSESKIP"}
    for pc, (op, a, b, c, k, bx, ax) in enumerate(code):
        if op == "JMP":
            target = pc + 1 + ax - ((1 << 25) - 1) // 2
        elif op in jumps:
            target = pc + 1 + bx - ((1 << 17) - 1) // 2
        elif op in skip:
            target = pc + 2
        else:
            continue
        if 0 <= target < len(code):
            leaders.add(target)
    return leaders


def decode_key(constants, key_index):
    if not 0 <= key_index < len(constants):
        return None
    raw = constants[key_index]
    if raw is None:
        return None
    try:
        value = raw.decode("ascii")
    except UnicodeDecodeError:
        return None
    return value if len(value) <= 90 else None


def receiver_origin(code, consts, field_pc, max_window=32, leaders=None):
    """Prove only intra-block local data flow into B of a field instruction.

    Values map register -> (lexical source path, assignment pc). Unhandled
    instructions, control-flow boundaries, and side effects invalidate all
    sources. An unresolved source is NEVER replaced by an inferred class.
    """
    if not (1 <= max_window <= 256) or not 0 <= field_pc < len(code):
        raise ValueError("Invalid window or field PC")
    leaders = branch_targets(code) if leaders is None else leaders
    origins = {}
    begin = max(0, field_pc - max_window)
    for pc in range(begin, field_pc):
        if pc in leaders:
            origins.clear()
        op, a, b, c, k, bx, ax = code[pc]
        if op == "MOVE":
            value = origins.get(b)
            origins.pop(a, None)
            if value:
                origins[a] = value
        elif op == "GETUPVAL":
            origins[a] = (f"UPVALUE[{b}]", pc)
        elif op == "GETTABUP":
            name = decode_key(consts, c)
            origins[a] = (f"UPVALUE[{b}].{name}", pc) if name else (f"UPVALUE[{b}].<?>", pc)
        elif op == "NEWTABLE":
            origins[a] = (f"NEW_TABLE@{pc}", pc)
        elif op == "GETFIELD":
            base = origins.get(b)
            key = decode_key(consts, c)
            origins.pop(a, None)
            if base and key and base[0].count(".") < 3:
                origins[a] = (base[0] + "." + key, pc)
        elif op == "SELF":
            base = origins.get(b)
            origins.pop(a, None)
            origins.pop(a + 1, None)
            if base:
                origins[a + 1] = base
                name = decode_key(consts, c) if k else None
                if name and base[0].count(".") < 3:
                    origins[a] = (base[0] + "." + name, pc)
        elif op == "LOADK":
            key = decode_key(consts, bx)
            origins.pop(a, None)
            if key:
                origins[a] = ("CONSTANT:" + key, pc)
        elif op == "GETTABLE":
            base, index = origins.get(b), origins.get(c)
            origins.pop(a, None)
            if base and index and index[0].startswith("CONSTANT:"):
                origins[a] = (base[0] + "." + index[0][9:], pc)
        elif op == "EXTRAARG" and pc > 0 and code[pc-1][0] == "NEWTABLE":
            pass
        else:
            origins.clear()

    op, a, b, c, k, bx, ax = code[field_pc]
    if op == "GETTABUP":
        return b, "UPVALUE_DIRECT", f"UPVALUE[{b}]", field_pc
    if op not in ("GETFIELD", "SELF", "GETTABLE"):
        raise ValueError("Not a supported field receiver opcode")
    value = origins.get(b)
    if value is None:
        return b, "UNRESOLVED_REGISTER", "", -1
    path, source_pc = value
    kind = ("UPVALUE_PATH" if path.startswith("UPVALUE[")
            else "LOCAL_TABLE_PATH" if path.startswith("NEW_TABLE@")
            else "CONSTANT_PATH" if path.startswith("CONSTANT:")
            else "UNRESOLVED_REGISTER")
    return b, kind, path, source_pc


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as inp:
        return list(csv.DictReader(inp, delimiter="\t"))


def run(manifest_path, summary_path, virtual, context_path, out, max_window=32):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if manifest.get("version") != "v2.0.2" or manifest.get("target_pack_indices") != [12145, 12146, 12147, 12148] or manifest.get("all_unique") is not True:
        raise ValueError("Unexpected native pack manifest")
    if summary.get("version") != "v2.0.2" or summary.get("native_files_parsed") != 4:
        raise ValueError("Four verified original ZA chunks are required")
    rows = read_rows(context_path)
    if len(rows) != 1488 or sum(r["owner_class_hash"] != "" for r in rows) != 1461:
        raise ValueError("Closure-context baseline changed; revalidate join first")
    core = load_core()
    calls_by_source = {name: [] for name in NAMES}
    for record in rows:
        calls_by_source[record["source"]].append(record)

    output, verified_files = [], {}
    for source in NAMES:
        matches = manifest["targets"][source]["matches"]
        if len(matches) != 1:
            raise ValueError(f"Nonunique native Lua pack: {source}")
        target = matches[0]
        rel = target["virtual_path"].replace("\\", "/")
        if rel != f"script/lua/bin/release/{source}/{source}.blua":
            raise ValueError(f"Unsafe Lua path: {rel}")
        raw = (virtual / rel).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        pinned = summary["files"][source]
        if pinned["sha256"].lower() != digest or pinned["bytes"] != len(raw) or pinned["status"] != "PARSED_NATIVE_LUA54" or pinned["source_pack_index"] != target["pack_index"]:
            raise ValueError(f"Native source SHA or pack mismatch: {source}")
        parsed = core.Lua54(raw)
        parsed.parse()
        verified_files[source] = {"sha256": digest, "prototypes": len(parsed.protos)}
        per_proto = {}
        for record in calls_by_source[source]:
            pid = int(record["proto_id"])
            if not 0 <= pid < len(parsed.protos):
                raise ValueError(f"Bad Prototype ID: {source}/{pid}")
            proto = parsed.protos[pid]
            if str(proto["parent"]) != record["parent_proto_id"]:
                raise ValueError("Native parent Prototype mismatch")
            if pid not in per_proto:
                code = core.instructions(raw, proto)
                per_proto[pid] = (code, branch_targets(code), proto["constants"])
            code, leaders, consts = per_proto[pid]
            pc, callpc = int(record["field_pc"]), int(record["call_pc"])
            if not (0 <= pc < callpc < len(code) and
                    code[pc][0] == record["field_opcode"] and
                    code[callpc][0] in ("CALL", "TAILCALL")):
                raise ValueError("Native opcode/PC no longer matches closure context")
            reg, kind, path, source_pc = receiver_origin(code, consts, pc, max_window, leaders)
            output.append({
                "source": source, "proto_id": pid,
                "parent_proto_id": proto["parent"],
                "called_hash_token": record["called_hash_token"],
                "owner_kind": record["owner_kind"],
                "owner_class_hash": record["owner_class_hash"],
                "owner_field_hash": record["owner_field_hash"],
                "field_pc": pc, "call_pc": callpc,
                "field_opcode": record["field_opcode"],
                "receiver_register": reg, "receiver_origin_kind": kind,
                "receiver_origin_path": path, "receiver_origin_pc": source_pc,
                "evidence": EVIDENCE, "runtime_receiver_class_confirmed": "NO",
            })

    output.sort(key=lambda r: (NAMES.index(r["source"]), r["proto_id"], r["field_pc"], r["called_hash_token"]))
    report = {
        "version": "v2.0.2", "evidence": EVIDENCE,
        "max_window": max_window,
        "inputs_sha256": {
            "manifest": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "summary": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            "closure_context": hashlib.sha256(context_path.read_bytes()).hexdigest(),
        },
        "native_files": verified_files,
        "all_field_call_edges": len(output),
        "root_closure_context_calls": sum(bool(row["owner_class_hash"]) for row in output),
        "origin_kinds": dict(sorted(Counter(row["receiver_origin_kind"] for row in output).items())),
        "source_opcodes": dict(sorted(Counter(row["field_opcode"] for row in output).items())),
        "runtime_receiver_classes_confirmed": 0,
        "original_names_recovered": 0,
        "warning": "Only bounded local register/Upvalue source, not runtime receiver class or name. Empty origin means unsafe or untraced.",
    }
    out.mkdir(parents=True, exist_ok=True)
    with (out / "native-unknown-receiver-register-provenance.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader(); writer.writerows(output)
    (out / "native-unknown-receiver-register-summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=INDEX / "lua_pack_locations.json")
    ap.add_argument("--summary", type=Path, default=NATIVE / "native-lua-summary.json")
    ap.add_argument("--virtual", type=Path, default=BASE / "virtual")
    ap.add_argument("--context", type=Path, default=NATIVE / "native-unknown-call-closure-context.tsv")
    ap.add_argument("--out", type=Path, default=NATIVE)
    ap.add_argument("--max-window", type=int, default=32)
    args = ap.parse_args()
    print(json.dumps(run(args.manifest, args.summary, args.virtual,
                         args.context, args.out, args.max_window),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
