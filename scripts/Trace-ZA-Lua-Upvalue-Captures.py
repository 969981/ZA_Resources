#!/usr/bin/env python3
"""Trace Z-A v2.0.2 native Lua 5.4 upvalue capture descriptors and closure creation.

An Upvalue chain proves the lexical capture topology of compiled bytecode, NOT
the runtime object identity, a method receiver class, or original source names.
Pinned to the four previously hashed Trinity .blua files; reads only, outputs TSV/JSON.
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
OWNER = ROOT / "scripts/Join-ZA-Lua-Closure-Callers.py"
SOURCES = ("dll_util", "event_ik", "main", "main_dynamic")
C_LOOKUP = re.compile(r"^(\d+):GETTABUP\(R(\d+),R(\d+),R(\d+),k(\d+)\)")
UPVAL = re.compile(r"(?:^| <- )(\d+):GETUPVAL\(R(\d+),R(\d+),R\d+,k\d+\)")
LOOKUP_COLS = (
    "source", "proto_id", "field_pc", "call_pc", "called_hash", "static_c_hash",
    "gettabup_pc", "gettabup_offset_hex", "upvalue_slot", "slot_lineage",
    "capture_origin", "capture_depth", "capture_creation_pcs",
    "capture_register_producers", "caller_class_hash", "caller_member_hash",
    "caller_owner_grade", "runtime_receiver_confirmed",
)
ANOMALY_COLS = (
    "source", "proto_id", "parent_proto_id", "called_hash", "field_pc",
    "owner_grade", "owner_class_hash", "ancestor_closure_proto_id",
    "parent_child_index", "closure_creation_pcs", "creation_site_count",
    "local_upvalue_descriptors", "evidence",
)


def load_owner():
    spec = importlib.util.spec_from_file_location("za_upvalue_owner", OWNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Pinned owner analyzer is missing")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def closure_sites(lua, instr, parent, child_id):
    """Exact OP_CLOSURE Bx=child-index in the child's actual parent bytecode."""
    child = lua.protos[child_id]
    if child["parent"] != parent or parent < 0:
        raise ValueError("Not a direct native Lua prototype parent/child")
    try:
        index = lua.protos[parent]["children"].index(child_id)
    except ValueError as error:
        raise ValueError("Lua child not in parent's indexed children") from error
    pcs = [i for i, code in enumerate(instr[parent])
           if code[0] == "CLOSURE" and code[5] == index]
    return index, pcs


def trace_capture(lua, instr, proto_id, slot, owner, max_window=16):
    """Trace native instack/index/kind descriptors back toward root.

    For a parent-stack register, inspect every verified CLOSURE creation site.
    The register producer is a bounded static hint; no type is inferred.
    """
    parts, creation, producers, visited = [], [], [], set()
    pid, upslot = proto_id, slot
    depth = 0
    while depth <= 150:
        if (pid, upslot) in visited:
            return "CAPTURE_CYCLE", depth, "|".join(parts), ",".join(creation), ";".join(producers)
        visited.add((pid, upslot))
        p = lua.protos[pid]
        if not 0 <= upslot < len(p["upvalues"]):
            raise ValueError(f"Invalid native upvalue slot {pid}:{upslot}")
        if p["parent"] < 0:
            parts.append(f"P{pid}.U{upslot}=EXTERNAL_CHUNK_UPVALUE")
            return "ROOT_EXTERNAL_UPVALUE", depth, "|".join(parts), ",".join(creation), ";".join(producers)
        in_stack, idx, kind = p["upvalues"][upslot]
        parent = p["parent"]
        parent_p = lua.protos[parent]
        child_index, pcs = closure_sites(lua, instr, parent, pid)
        if not pcs:
            # An unreferenced nested proto is compiled but is never created by
            # a visible OP_CLOSURE site in its original lexical parent.
            parts.append(f"P{pid}.U{upslot}(s={in_stack},i={idx},k={kind})=NO_CREATION_SITE")
            return "NO_NATIVE_CLOSURE_SITE", depth, "|".join(parts), ",".join(creation), ";".join(producers)
        site_desc = f"P{parent}.CLOSURE[{child_index}]@{','.join(map(str,pcs))}"
        creation.append(site_desc)
        if in_stack == 0:
            if idx >= len(parent_p["upvalues"]):
                raise ValueError("Invalid parent upvalue reference in native descriptor")
            parts.append(f"P{pid}.U{upslot}(s=0,i={idx},k={kind})->P{parent}.U{idx}")
            pid, upslot = parent, idx
            depth += 1
            continue
        if in_stack != 1:
            raise ValueError("Unexpected Lua upvalue instack flag")
        parts.append(f"P{pid}.U{upslot}(s=1,i={idx},k={kind})->P{parent}.R{idx}")
        flow = owner.load_flow()
        producer_statuses = []
        parent_insts = instr[parent]
        entries = flow.branch_target_pcs(parent_insts)
        captured_upvalues = []
        for pc in pcs:
            grade, chain, class_key = owner.receiver_origin(
                parent_insts, parent_p["constants"], pc, idx, entries, max_window)
            producer_statuses.append(grade)
            producers.append(f"P{parent}@{pc}:R{idx}:{grade}:{chain[:240]}")
            captures = list(UPVAL.finditer(chain))
            if grade.endswith("DIRECT_UPVALUE_SLOT") and captures:
                captured_upvalues.append(int(captures[-1].group(3)))
        if len(pcs) == 1 and len(captured_upvalues) == 1:
            # Parent bytecode proves a register got its current value from
            # GETUPVAL, so we can continue up this lexical chain.
            ancestor_slot = captured_upvalues[0]
            if ancestor_slot >= len(parent_p["upvalues"]):
                raise ValueError("Register producer references invalid parent upvalue slot")
            parts.append(f"P{parent}.R{idx}<-P{parent}.U{ancestor_slot} (bounded instruction flow)")
            pid, upslot = parent, ancestor_slot
            depth += 1
            continue
        if len(pcs) > 1:
            status = "PARENT_STACK_CAPTURE_MULTIPLE_SITES"
        elif any(x in ("CONTROL_FLOW_BOUNDARY","UNKNOWN_OPCODE_BARRIER") for x in producer_statuses):
            status = "PARENT_STACK_CAPTURE_UNPROVEN_PRODUCER"
        else:
            status = "PARENT_STACK_CAPTURE_LOCAL_REGISTER"
        return status, depth+1, "|".join(parts), ",".join(creation), ";".join(producers)
    return "DEPTH_LIMIT", depth, "|".join(parts), ",".join(creation), ";".join(producers)


def trace_static_lookup(row, lua, instr, owner, max_window=16):
    if row["receiver_origin_kind"] != "UPVALUE_KEY_LOOKUP":
        return None
    m = C_LOOKUP.match(row["receiver_origin_trace"])
    if not m:
        raise ValueError("Recorded GETTABUP producer trace is not native-looking")
    pc, dst, upslot, cidx, k = map(int, m.groups())
    pid = int(row["proto_id"])
    proto = lua.protos[pid]
    code = instr[pid]
    if not 0 <= pc < int(row["field_pc"]) <= int(row["call_pc"]) < len(code):
        raise ValueError("Original CALL no longer follows purported GETTABUP")
    op, a, b, c, native_k, bx, ax = code[pc]
    if (op != "GETTABUP" or (a, b, c, native_k) != (dst, upslot, cidx, k)
        or c >= len(proto["constants"])
        or proto["constants"][c] != row["receiver_static_class_key"].encode("ascii")):
        raise ValueError("Original native C lookup key or instruction mismatch")
    status, depth, chain, sites, producers = trace_capture(
        lua, instr, pid, upslot, owner, max_window)
    return (row["source"], pid, row["field_pc"], row["call_pc"],
            row["hash_token"], row["receiver_static_class_key"], pc,
            f"0x{proto['code_offset'] + 4 * pc:X}", upslot,
            chain, status, depth, sites, producers,
            row["owner_class_hash"], row["owner_member_hash"],
            row["owner_grade"], "NO")


def trace_anomaly(row, lua, instr):
    pid = int(row["proto_id"])
    proto = lua.protos[pid]
    parent = proto["parent"]
    if parent == -1:
        index, pcs = -1, []
    else:
        index, pcs = closure_sites(lua, instr, parent, pid)
    desc = ",".join(f"U{i}:s{up[0]}i{up[1]}k{up[2]}"
                    for i,up in enumerate(proto["upvalues"]))
    return (row["source"], pid, parent, row["hash_token"], row["field_pc"],
            row["owner_grade"], row["owner_class_hash"],
            row["owner_closure_proto_id"], index, ",".join(map(str,pcs)),
            len(pcs), desc,
            "NATIVE_LUA54_CLOSURE_SITE_AND_CAPTURE_DESCRIPTORS_ONLY")


def write_tsv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)


def run(native_summary=INDEX/"native-lua-summary.json",
        pack_report=BASE/"_index/lua_pack_locations.json",
        virtual=BASE/"virtual",
        callers=INDEX/"native-closure-caller-receiver.tsv",
        out=INDEX, max_window=16):
    if not 1 <= max_window <= 256:
        raise ValueError("max_window must be 1..256")
    owner = load_owner()
    core = owner.load_flow().load_direct().load_core()
    report = json.loads(native_summary.read_text(encoding="utf-8"))
    manifest = json.loads(pack_report.read_text(encoding="utf-8"))
    if (report.get("native_files_parsed") != 4 or report.get("version") != "v2.0.2"
        or manifest.get("all_unique") is not True or
        manifest.get("target_pack_indices") != [12145,12146,12147,12148]):
        raise ValueError("Pinned native ZA 2.0.2 manifest missing")
    rows = owner.tsv(callers)
    if len(rows) != 1488:
        raise ValueError("The 1,488 verified native CALL records changed")
    groups = defaultdict(list)
    for row in rows:
        groups[row["source"]].append(row)
    lookups, anomalies = [], []
    metadata = {}
    for source in SOURCES:
        entry = manifest["targets"][source]["matches"]
        if len(entry) != 1:
            raise ValueError("Ambiguous Trinity file identity")
        match = entry[0]
        rel = match["virtual_path"].replace("\\","/")
        if rel != f"script/lua/bin/release/{source}/{source}.blua":
            raise ValueError("Unexpected native Lua virtual path")
        raw = (virtual/rel).read_bytes()
        pinned = report["files"][source]
        sha = hashlib.sha256(raw).hexdigest()
        if (len(raw) != pinned["bytes"] or sha != pinned["sha256"] or
            pinned["source_pack_index"] != match["pack_index"] or
            pinned["status"] != "PARSED_NATIVE_LUA54"):
            raise ValueError("Native game bytes not identical to pinned SHA/size/pack")
        lua = core.Lua54(raw)
        lua.parse()
        if len(lua.protos) != pinned["prototypes"]:
            raise ValueError("Original native prototype count changed")
        ins = {p["id"]:core.instructions(raw,p) for p in lua.protos}
        # Validate every CLOSURE child-index target exists before computing capture paths.
        for p in lua.protos:
            for pc, inst in enumerate(ins[p["id"]]):
                if inst[0] == "CLOSURE" and inst[5] >= len(p["children"]):
                    raise ValueError(f"Invalid native closure at {source} P{p['id']} PC{pc}")
        for row in groups[source]:
            if row["receiver_origin_kind"] == "UPVALUE_KEY_LOOKUP":
                lookups.append(trace_static_lookup(row,lua,ins,owner,max_window))
            if row["owner_grade"] != "NATIVE_DIRECT_CLOSURE_BODY":
                anomalies.append(trace_anomaly(row,lua,ins))
        metadata[source]={"sha256":sha,"prototypes":len(lua.protos),
                          "root_upvalues":len(lua.protos[0]["upvalues"])}
    grades = Counter(x[10] for x in lookups)
    anomaly_grades = Counter(x[5] for x in anomalies)
    classes = Counter(x[5] for x in lookups)
    if len(lookups)!=926 or len(anomalies)!=27 or (
        anomaly_grades["NATIVE_LEXICAL_CHILD_OF_CLOSURE"]!=7 or
        anomaly_grades["NO_VERIFIED_CLOSURE_OWNER"]!=20):
        raise ValueError("Original native receiver/closure anomaly corpus changed")
    result={
        "version":"v2.0.2","source_native_summary_sha256":hashlib.sha256(native_summary.read_bytes()).hexdigest(),
        "source_closure_callers_sha256":hashlib.sha256(callers.read_bytes()).hexdigest(),
        "input_sources":metadata,"total_native_call_rows":len(rows),
        "native_static_class_key_lookups":len(lookups),
        "lookup_distinct_prototypes":len({(x[0],x[1]) for x in lookups}),
        "capture_origin_counts":dict(grades),
        "static_class_key_counts":dict(classes),
        "nonderived_closure_calls":len(anomalies),
        "nested_lexical_owner_calls":anomaly_grades["NATIVE_LEXICAL_CHILD_OF_CLOSURE"],
        "unowned_registration_calls":anomaly_grades["NO_VERIFIED_CLOSURE_OWNER"],
        "distinct_unowned_prototypes":len({(x[0],x[1]) for x in anomalies
                                            if x[5]=="NO_VERIFIED_CLOSURE_OWNER"}),
        "receiver_runtime_classes_confirmed":0,"original_symbol_names_recovered":0,
        "warning":"Upvalue descriptors and OP_CLOSURE are byte-accurate lexical capture evidence. Neither EXTERNAL_CHUNK_UPVALUE nor a C hash lookup is proof of runtime receiver type or original symbol name."
    }
    out.mkdir(parents=True,exist_ok=True)
    write_tsv(out/"native-upvalue-capture-lookups.tsv",LOOKUP_COLS,lookups)
    write_tsv(out/"native-closure-unresolved-sites.tsv",ANOMALY_COLS,anomalies)
    (out/"native-upvalue-capture-summary.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-summary",type=Path,default=INDEX/"native-lua-summary.json")
    parser.add_argument("--pack-report",type=Path,default=BASE/"_index/lua_pack_locations.json")
    parser.add_argument("--virtual",type=Path,default=BASE/"virtual")
    parser.add_argument("--callers",type=Path,default=INDEX/"native-closure-caller-receiver.tsv")
    parser.add_argument("--out",type=Path,default=INDEX)
    parser.add_argument("--max-window",type=int,default=16)
    args=parser.parse_args()
    print(json.dumps(run(args.native_summary,args.pack_report,args.virtual,
                         args.callers,args.out,args.max_window),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
