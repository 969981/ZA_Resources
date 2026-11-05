#!/usr/bin/env python3
"""Conservative intrablock Lua 5.4 register-flow evidence for ZA v2.0.2.

No recovered original names or inferred receiver types. This intentionally follows
only known-safe register transfers, constant loads, and field reads. Unknown
instructions, branches, calls, and side effects end the straight-line segment.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "Unpack/v2.0.2/romfs/arc/data.trpfs"
NATIVE = BASE / "_index/lua-native"
DIRECT = ROOT / "scripts/Analyze-ZA-Lua-DirectCalls.py"
NAMES = ("dll_util", "event_ik", "main", "main_dynamic")
CALL_GRADE = "NATIVE_LUA54_STRAIGHT_LINE_REGISTER_CALL"
KEY_GRADE = "NATIVE_LUA54_REGISTER_KEY_TABLE_REFERENCE"
CALL_COLS = (
    "source", "hash_token", "proto_id", "parent_proto_id", "key_load_pc",
    "field_pc", "field_offset_hex", "field_opcode", "field_register",
    "call_pc", "call_offset_hex", "call_opcode", "call_register", "move_count",
    "evidence",
)
KEY_COLS = (
    "source", "hash_token", "proto_id", "parent_proto_id", "key_load_pc",
    "field_pc", "field_offset_hex", "field_opcode", "key_register", "evidence",
)


def load_direct():
    spec = importlib.util.spec_from_file_location("za_lua_direct_for_flow", DIRECT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Pinned adjacent-call analyzer not found")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def branch_target_pcs(inst):
    """Mark branch entry PCs so copied registers never cross jump targets."""
    leaders = {0}
    jumps_bx = {"FORLOOP", "FORPREP", "TFORPREP", "TFORLOOP"}
    skips = {"EQ", "LT", "LE", "EQK", "EQI", "LTI", "LEI",
             "GTI", "GEI", "TEST", "TESTSET", "LFALSESKIP"}
    for pc, (op, a, b, c, k, bx, ax) in enumerate(inst):
        target = None
        if op == "JMP":
            target = pc + 1 + ax - ((1 << 25) - 1) // 2
        elif op in jumps_bx:
            target = pc + 1 + bx - ((1 << 17) - 1) // 2
        elif op in skips:
            target = pc + 2
        if target is not None and 0 <= target < len(inst):
            leaders.add(target)
    return leaders


def trace_proto(inst, consts, wanted, source, proto, max_window=16):
    """Follow a bounded local register provenance, never crossing unsafe opcodes.

    Field provenance: (hash, key_load_pc, field_pc, opcode, origin_register, moves).
    Constant-key provenance: (hash, LOADK pc). Neither reveals runtime types.
    """
    if max_window < 1 or max_window > 256:
        raise ValueError("max_window must be 1..256")
    values = {}
    keys = {}
    calls, keyed = [], []
    pc = 0
    incoming_branches = branch_target_pcs(inst)
    code_offset = proto["code_offset"]

    def target(index):
        if 0 <= index < len(consts) and consts[index] in wanted:
            return consts[index].decode("ascii")
        return None

    def overwrite(reg):
        values.pop(reg, None)
        keys.pop(reg, None)

    def age_out(at_pc):
        for reg, val in list(values.items()):
            if at_pc - val[2] > max_window:
                del values[reg]
        for reg, val in list(keys.items()):
            if at_pc - val[1] > max_window:
                del keys[reg]

    while pc < len(inst):
        if pc in incoming_branches:
            values.clear()
            keys.clear()
        age_out(pc)
        op, a, b, c, k, bx, ax = inst[pc]

        if op in ("LOADK", "LOADKX"):
            idx, skip = bx, 0
            if op == "LOADKX":
                if pc + 1 >= len(inst) or inst[pc + 1][0] != "EXTRAARG":
                    values.clear()
                    keys.clear()
                    pc += 1
                    continue
                idx, skip = inst[pc + 1][6], 1
            overwrite(a)
            token = target(idx)
            if token:
                keys[a] = (token, pc)
            pc += 1 + skip
            continue

        if op == "MOVE":
            value, key = values.get(b), keys.get(b)
            overwrite(a)
            if value is not None:
                token, key_pc, field_pc, field_op, origin, moves = value
                values[a] = (token, key_pc, field_pc, field_op, origin, moves + 1)
            if key is not None:
                keys[a] = key
            pc += 1
            continue

        if op in ("GETFIELD", "GETTABUP", "SELF", "GETTABLE"):
            key = None
            if op in ("GETFIELD", "GETTABUP"):
                token = target(c)
                if token:
                    key = (token, "")
            elif op == "SELF":
                if k == 1:
                    token = target(c)
                    if token:
                        key = (token, "")
                else:
                    key = keys.get(c)
            elif op == "GETTABLE":
                key = keys.get(c)
            if key and op in ("GETTABLE", "SELF") and (op == "GETTABLE" or k == 0):
                keyed.append((source, key[0], proto["id"], proto["parent"], key[1],
                              pc, f"0x{code_offset + 4 * pc:X}", op, c, KEY_GRADE))
            overwrite(a)
            if op == "SELF":
                overwrite(a + 1)
            if key:
                values[a] = (key[0], key[1], pc, op, a, 0)
            pc += 1
            continue

        if op == "SETTABLE":
            key = keys.get(b)
            if key:
                keyed.append((source, key[0], proto["id"], proto["parent"], key[1],
                              pc, f"0x{code_offset + 4 * pc:X}", op, b, KEY_GRADE))
            values.clear()
            keys.clear()
            pc += 1
            continue

        if op in ("CALL", "TAILCALL"):
            val = values.get(a)
            if val is not None:
                token, key_pc, field_pc, field_op, origin, moves = val
                calls.append((source, token, proto["id"], proto["parent"], key_pc,
                              field_pc, f"0x{code_offset + 4 * field_pc:X}", field_op,
                              origin, pc, f"0x{code_offset + 4 * pc:X}", op, a,
                              moves, CALL_GRADE))
            values.clear()
            keys.clear()
            pc += 1
            continue

        # Unknown instruction, branch, metamethod, table write, or side effect.
        values.clear()
        keys.clear()
        pc += 1
    return calls, keyed


def write_tsv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)


def run(pack_report, native_summary, virtual_root, unknown_index, baseline, out,
        max_window=16):
    direct = load_direct()
    core = direct.load_core()
    wanted = direct.unknown_tokens(unknown_index)
    manifest = json.loads(pack_report.read_text(encoding="utf-8"))
    summary = json.loads(native_summary.read_text(encoding="utf-8"))
    if (manifest.get("version") != "v2.0.2" or
        manifest.get("target_pack_indices") != [12145, 12146, 12147, 12148] or
        manifest.get("all_unique") is not True or
        summary.get("version") != "v2.0.2" or
        summary.get("native_files_parsed") != 4):
        raise ValueError("Expected complete pinned native ZA v2.0.2 extraction")
    reports, calls, keyed = {}, [], []
    for name in NAMES:
        matches = manifest["targets"][name]["matches"]
        if len(matches) != 1:
            raise ValueError("Missing/ambiguous native Lua pack: " + name)
        row = matches[0]
        rel = row["virtual_path"].replace("\\", "/")
        if (rel.startswith("/") or ":" in rel or ".." in rel.split("/") or
            rel != f"script/lua/bin/release/{name}/{name}.blua"):
            raise ValueError("Unsafe or unexpected native Lua virtual path: " + rel)
        raw = (virtual_root / rel).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        pinned = summary["files"][name]
        if (pinned["status"] != "PARSED_NATIVE_LUA54" or
            pinned["sha256"].lower() != digest or pinned["bytes"] != len(raw) or
            pinned["source_pack_index"] != row["pack_index"]):
            raise ValueError("Original native Lua bytes differ from pinned evidence: " + name)
        parsed = core.Lua54(raw)
        parsed.parse()
        for proto in parsed.protos:
            c, k = trace_proto(core.instructions(raw, proto), proto["constants"],
                               wanted, name, proto, max_window)
            calls.extend(c)
            keyed.extend(k)
        reports[name] = {"sha256": digest, "prototypes": len(parsed.protos)}

    # The earlier adjacent-only scan is a comparison, not a required superset:
    # incoming branch targets can invalidate an apparently adjacent relation.
    with baseline.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    expected = {(r["source"], r["hash_token"], int(r["proto_id"]),
                 int(r["field_pc"]), int(r["call_pc"])) for r in rows}
    actual = {(r[0], r[1], r[2], r[5], r[9]) for r in calls}
    if len(rows) != 566 or len(expected) != len(rows):
        raise ValueError("Pinned adjacent-call baseline missing, duplicated or modified")
    excluded = sorted(expected - actual)
    calls.sort(key=lambda r: (NAMES.index(r[0]), r[2], r[9], r[5], r[1]))
    keyed.sort(key=lambda r: (NAMES.index(r[0]), r[2], r[5], r[1]))
    report = {
        "game": "Pokemon Legends Z-A",
        "version": "v2.0.2",
        "files": reports,
        "input_native_summary_sha256": hashlib.sha256(native_summary.read_bytes()).hexdigest(),
        "input_baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
        "max_window": max_window,
        "baseline_adjacent_edges": len(rows),
        "baseline_adjacent_retained": len(expected & actual),
        "baseline_excluded_by_conservative_control_flow": len(excluded),
        "baseline_excluded_sample": [list(row) for row in excluded[:12]],
        "dataflow_call_edges": len(calls),
        "new_nonadjacent_or_register_key_call_edges": len(actual - expected),
        "distinct_called_unresolved_hashes": len({r[1] for r in calls}),
        "register_key_table_references": len(keyed),
        "distinct_register_key_tokens": len({r[1] for r in keyed}),
        "evidence": [CALL_GRADE, KEY_GRADE],
        "original_names_recovered": 0,
        "receiver_classes_confirmed": 0,
        "warning": "Only local straight-line register dependencies; unknown instructions and jumps clear state. No original names or receiver types inferred.",
    }
    out.mkdir(parents=True, exist_ok=True)
    write_tsv(out / "native-unknown-register-flow-calls.tsv", CALL_COLS, calls)
    write_tsv(out / "native-unknown-register-key-uses.tsv", KEY_COLS, keyed)
    (out / "native-unknown-register-flow-summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-report", type=Path, default=BASE / "_index/lua_pack_locations.json")
    parser.add_argument("--native-summary", type=Path, default=NATIVE / "native-lua-summary.json")
    parser.add_argument("--virtual-root", type=Path, default=BASE / "virtual")
    parser.add_argument("--unknown-index", type=Path, default=ROOT / "tools/PokeDocs-Supplement/ZA/Hashlists/Lua/unresolved-symbol-index.tsv")
    parser.add_argument("--baseline", type=Path, default=NATIVE / "native-unknown-direct-call-edges.tsv")
    parser.add_argument("--out", type=Path, default=NATIVE)
    parser.add_argument("--max-window", type=int, default=16)
    args = parser.parse_args()
    print(json.dumps(run(args.pack_report, args.native_summary, args.virtual_root,
                         args.unknown_index, args.baseline, args.out, args.max_window),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
