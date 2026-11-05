#!/usr/bin/env python3
"""Join ZA 2.0.2 verified native Lua call records to registered method closures.

Strictly separates *lexical owner* (C→F/C→S closure assignment) from dynamic
receiver. Receiver reconstruction only records bounded, straight-line register
producer instructions. Neither relation confirms an original symbol name.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "Unpack/v2.0.2/romfs/arc/data.trpfs"
INDEX = BASE / "_index/lua-native"
FLOW_SCRIPT = ROOT / "scripts/Trace-ZA-Lua-RegisterFlow.py"
CLOSURE_F = INDEX / "native-c-f-method-edges.tsv"
CLOSURE_S = INDEX / "native-c-s-static-edges.tsv"
CALLS = INDEX / "native-unknown-register-flow-calls.tsv"
SOURCES = ("dll_util", "event_ik", "main", "main_dynamic")
CLASS_KEY = re.compile(r"^C[0-9a-fA-F]{16}$")
SAFE = frozenset(("MOVE", "LOADK", "LOADKX", "EXTRAARG", "GETUPVAL",
                  "GETTABUP", "GETTABLE", "GETFIELD", "SELF", "NEWTABLE",
                  "LOADI", "LOADF", "LOADTRUE", "LOADFALSE"))
OUTPUT_COLS = (
    "source", "hash_token", "proto_id", "field_pc", "call_pc",
    "receiver_register", "receiver_origin_kind", "receiver_origin_trace",
    "receiver_static_class_key", "owner_class_hash", "owner_member_hash",
    "owner_member_kind", "owner_closure_proto_id", "owner_root_pc",
    "owner_grade", "lexical_parent_steps", "receiver_class_confirmed",
    "original_name_confirmed"
)


def load_flow():
    spec = importlib.util.spec_from_file_location("za_lua_owner_flow", FLOW_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Native register-flow analyzer missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tsv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def build_closures(f_rows, s_rows):
    result = defaultdict(list)
    for label, items, child_field, member_field, grade in (
        ("F", f_rows, "child_proto_id", "function_hash", "NATIVE_C_F_CLOSURE_ASSIGNMENT"),
        ("S", s_rows, "closure_proto_id", "s_hash", "NATIVE_C_S_STATIC_CLOSURE_ASSIGNMENT"),
    ):
        for row in items:
            if row["source"] not in SOURCES or not CLASS_KEY.fullmatch(row["class_hash"]):
                raise ValueError("Malformed native class closure edge")
            result[(row["source"], int(row[child_field]))].append({
                "class": row["class_hash"], "member": row[member_field],
                "kind": label, "root_pc": int(row["root_pc"]),
                "child_proto_id": int(row[child_field]), "grade": grade,
            })
    return result


def nearest_owner(source, proto_id, protos, closures):
    steps, pid = 0, proto_id
    while pid >= 0 and steps <= 150:
        found = closures.get((source, pid), [])
        if len(found) == 1:
            return found[0], ("NATIVE_DIRECT_CLOSURE_BODY" if steps == 0
                              else "NATIVE_LEXICAL_CHILD_OF_CLOSURE"), steps
        if len(found) > 1:
            return None, "AMBIGUOUS_CLOSURE_ASSIGNMENTS", steps
        pid = protos[pid]["parent"]
        steps += 1
    return None, "NO_VERIFIED_CLOSURE_OWNER", steps


def token_string(raw):
    if raw is None:
        return ""
    return raw.decode("utf-8", "backslashreplace")[:96]


def receiver_origin(inst, consts, field_pc, reg, branch_entries, max_window=16):
    """Recover a *producer instruction*, not an instance's runtime type.

    Every traversed instruction must have understood register effects; unknown
    instructions and control-flow entries stop tracing. Recursive MOVE/GETFIELD
    follows same-block origins only. Identified C key is a lookup literal only.
    """
    def search(before, wanted, depth, seen):
        if depth > 6 or (before, wanted) in seen:
            return ("DEPTH_LIMIT", [], "")
        seen = seen | {(before, wanted)}
        low = max(0, before - max_window)
        for pc in range(before - 1, low - 1, -1):
            if pc in branch_entries and pc != before - 1 and pc != 0:
                return ("CONTROL_FLOW_BOUNDARY", [], "")
            op, a, b, c, k, bx, ax = inst[pc]
            if op not in SAFE:
                return ("UNKNOWN_OPCODE_BARRIER", [f"{pc}:{op}"], "")
            written = (a == wanted or op == "SELF" and a + 1 == wanted)
            if not written:
                continue
            mark = f"{pc}:{op}(R{a},R{b},R{c},k{k})"
            if op == "MOVE":
                status, steps, literal = search(pc, b, depth+1, seen)
                return ("MOVE_FROM_" + status, [mark] + steps, literal)
            if op == "GETUPVAL":
                return ("DIRECT_UPVALUE_SLOT", [mark], "")
            if op == "GETTABUP":
                literal = token_string(consts[c]) if c < len(consts) else ""
                return ("UPVALUE_KEY_LOOKUP", [mark], literal if CLASS_KEY.fullmatch(literal) else "")
            if op == "GETFIELD":
                literal = token_string(consts[c]) if c < len(consts) else ""
                status, steps, key = search(pc, b, depth+1, seen)
                return ("FIELD_OF_" + status, [mark] + steps,
                        literal if CLASS_KEY.fullmatch(literal) else key)
            if op == "GETTABLE":
                # The key itself may be in a different register, so no class
                # identity is inferred from it by this conservative pass.
                status, steps, key = search(pc, b, depth+1, seen)
                return ("TABLE_VALUE_FROM_" + status, [mark] + steps, key)
            if op == "SELF":
                if wanted == a + 1:
                    status, steps, key = search(pc, b, depth+1, seen)
                    return ("SELF_RECEIVER_COPY_OF_" + status, [mark] + steps, key)
                return ("PRIOR_SELF_FUNCTION_RESULT", [mark], "")
            if op == "LOADK":
                literal = token_string(consts[bx]) if bx < len(consts) else ""
                return ("CONSTANT_LITERAL", [mark], literal if CLASS_KEY.fullmatch(literal) else "")
            if op == "LOADKX":
                literal = ""
                if pc+1 < len(inst) and inst[pc+1][0] == "EXTRAARG":
                    idx = inst[pc+1][6]
                    literal = token_string(consts[idx]) if idx < len(consts) else ""
                return ("EXTENDED_CONSTANT_LITERAL", [mark], literal if CLASS_KEY.fullmatch(literal) else "")
            if op == "NEWTABLE":
                return ("LOCAL_NEWTABLE", [mark], "")
            return ("SCALAR_OR_LITERAL_REGISTER", [mark], "")
        return ("SOURCE_OUTSIDE_WINDOW", [], "")
    grade, steps, class_key = search(field_pc, reg, 0, set())
    return grade, " <- ".join(steps), class_key


def process_call(row, source, lua, inst, closures, flow, window=16):
    pid, field_pc, call_pc = (int(row[x]) for x in ("proto_id", "field_pc", "call_pc"))
    proto = lua.protos[pid]
    if pid < 0 or field_pc < 0 or call_pc >= len(inst) or field_pc >= call_pc:
        raise ValueError("Malformed source call instruction range")
    field = inst[field_pc]
    call = inst[call_pc]
    if field[0] != row["field_opcode"] or call[0] != row["call_opcode"] or (
        call[0] not in ("CALL", "TAILCALL")
    ):
        raise ValueError("Native call and stored opcode disagree")
    if field[1] != int(row["field_register"]) or call[1] != int(row["call_register"]):
        raise ValueError("Native call register disagreement")
    expected = row["hash_token"].encode("ascii")
    consts = proto["constants"]
    op, a, b, c, k, bx, ax = field
    if op in ("GETFIELD", "GETTABUP") or op == "SELF" and k == 1:
        if c >= len(consts) or consts[c] != expected:
            raise ValueError("Native constant reference disagreement")
    elif op in ("GETTABLE", "SELF") and (op == "GETTABLE" or k == 0):
        key_pc = int(row["key_load_pc"])
        key = inst[key_pc]
        idx = key[5] if key[0] == "LOADK" else (
            inst[key_pc+1][6] if key[0] == "LOADKX" and inst[key_pc+1][0] == "EXTRAARG"
            else -1
        )
        if idx < 0 or idx >= len(consts) or consts[idx] != expected:
            raise ValueError("Register key not tied to original constant")
    else:
        raise ValueError("Unsupported field load opcode in native flow")
    owner, owner_grade, steps = nearest_owner(source, pid, lua.protos, closures)
    receiver_reg = -1
    if op == "GETTABUP":
        origin = "DIRECT_UPVALUE_TABLE_SLOT"
        chain = f"GETTABUP(B={b})"
        class_key = ""
    else:
        receiver_reg = b
        origin, chain, class_key = receiver_origin(
            inst, consts, field_pc, b, flow.branch_target_pcs(inst), window)
    owner = owner or {}
    return (
        source, row["hash_token"], pid, field_pc, call_pc, receiver_reg,
        origin, chain, class_key, owner.get("class", ""),
        owner.get("member", ""), owner.get("kind", ""),
        owner.get("child_proto_id", ""), owner.get("root_pc", ""),
        owner_grade, steps, "NO", "NO"
    )


def run(pack_report=BASE/"_index/lua_pack_locations.json",
        native_summary=INDEX/"native-lua-summary.json",
        virtual=BASE/"virtual", flows=CALLS, f_edges=CLOSURE_F,
        s_edges=CLOSURE_S, out=INDEX, window=16):
    flow = load_flow()
    core = flow.load_direct().load_core()
    manifest = json.loads(pack_report.read_text(encoding="utf-8"))
    summary = json.loads(native_summary.read_text(encoding="utf-8"))
    if (manifest.get("version") != "v2.0.2" or manifest.get("all_unique") is not True or
        manifest.get("target_pack_indices") != [12145, 12146, 12147, 12148] or
        summary.get("native_files_parsed") != 4 or summary.get("version") != "v2.0.2"):
        raise ValueError("Native file provenance not verified")
    rows = tsv(flows)
    if len(rows) != 1488:
        raise ValueError("Expected 1,488 pinned native register-flow edges")
    closure = build_closures(tsv(f_edges), tsv(s_edges))
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["source"]].append(row)
    report, matches = {}, []
    for name in SOURCES:
        entry = manifest["targets"][name]["matches"]
        if len(entry) != 1:
            raise ValueError("Ambiguous original pack " + name)
        rel = entry[0]["virtual_path"].replace("\\", "/")
        if rel != f"script/lua/bin/release/{name}/{name}.blua":
            raise ValueError("Unexpected game-native path")
        raw = (virtual / rel).read_bytes()
        expected = summary["files"][name]
        if (len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"] or
            expected["status"] != "PARSED_NATIVE_LUA54" or
            expected["source_pack_index"] != entry[0]["pack_index"]):
            raise ValueError("Native Lua bytes differ: " + name)
        lua = core.Lua54(raw)
        lua.parse()
        inst_map = {p["id"]: core.instructions(raw, p) for p in lua.protos}
        if len(lua.protos) != expected["prototypes"]:
            raise ValueError("Native prototype count mismatch")
        for row in grouped[name]:
            pid = int(row["proto_id"])
            if pid >= len(lua.protos):
                raise ValueError("Invalid proto ID")
            matches.append(process_call(row, name, lua, inst_map[pid], closure, flow, window))
        report[name] = {"sha256": expected["sha256"], "proto_count": len(lua.protos),
                        "flow_calls": len(grouped[name])}
    grade = Counter(row[14] for row in matches)
    receiver = Counter(row[6] for row in matches)
    result = {
        "game": "Pokemon Legends Z-A", "version": "v2.0.2",
        "source_native_summary_sha256": hashlib.sha256(native_summary.read_bytes()).hexdigest(),
        "source_call_edges_sha256": hashlib.sha256(flows.read_bytes()).hexdigest(),
        "window": window, "sources": report, "call_edges_scanned": len(matches),
        "direct_registered_closure_calls": grade["NATIVE_DIRECT_CLOSURE_BODY"],
        "lexically_nested_closure_calls": grade["NATIVE_LEXICAL_CHILD_OF_CLOSURE"],
        "ambiguous_closure_calls": grade["AMBIGUOUS_CLOSURE_ASSIGNMENTS"],
        "without_registered_closure": grade["NO_VERIFIED_CLOSURE_OWNER"],
        "unique_direct_owner_classes": len({row[9] for row in matches if row[14] == "NATIVE_DIRECT_CLOSURE_BODY"}),
        "receiver_origin_grades": dict(receiver),
        "receiver_classes_confirmed": 0, "original_names_recovered": 0,
        "warning": "Registered closure is the CALLER's lexical owner, not necessarily the CALLEE receiver class. Upvalue slots and literal C keys never certify runtime instance type."
    }
    if result["direct_registered_closure_calls"] != 1461:
        raise ValueError("Pinned 1,461 direct closure ownership regression")
    out.mkdir(parents=True, exist_ok=True)
    with (out/"native-closure-caller-receiver.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(OUTPUT_COLS)
        w.writerows(matches)
    (out/"native-closure-caller-receiver-summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack-report", type=Path, default=BASE/"_index/lua_pack_locations.json")
    p.add_argument("--native-summary", type=Path, default=INDEX/"native-lua-summary.json")
    p.add_argument("--virtual", type=Path, default=BASE/"virtual")
    p.add_argument("--calls", type=Path, default=CALLS)
    p.add_argument("--f-edges", type=Path, default=CLOSURE_F)
    p.add_argument("--s-edges", type=Path, default=CLOSURE_S)
    p.add_argument("--out", type=Path, default=INDEX)
    p.add_argument("--window", type=int, default=16)
    a=p.parse_args()
    print(json.dumps(run(a.pack_report,a.native_summary,a.virtual,a.calls,
                         a.f_edges,a.s_edges,a.out,a.window), ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
