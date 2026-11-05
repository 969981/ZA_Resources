#!/usr/bin/env python3
"""Auditable ZA 2.0.2 closure-prototype to field-call join.

Joins existing *native* TSV evidence by (source, child_proto_id) and
(source, call.proto_id). This establishes the enclosing root closure of a
local field -> CALL edge, NOT the runtime receiver of the field, an executed
call graph, or the original hash name. No game binaries are modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "Unpack/v2.0.2/romfs/arc/data.trpfs/_index/lua-native"
INPUTS = (
    "native-c-f-method-edges.tsv",
    "native-c-s-static-edges.tsv",
    "native-unknown-register-flow-calls.tsv",
)
DETAIL = "native-unknown-call-closure-context.tsv"
PRIORITY = "native-unknown-class-call-priority.tsv"
SUMMARY = "native-unknown-call-closure-summary.json"
DETAIL_COLUMNS = (
    "source", "proto_id", "parent_proto_id", "called_hash_token",
    "field_pc", "field_offset_hex", "call_pc", "call_offset_hex",
    "field_opcode", "owner_kind", "owner_class_hash", "owner_field_hash",
    "owner_root_pc", "owner_assignment_pc", "join_status",
    "receiver_identity_confirmed", "original_name_confirmed",
)
PRIORITY_COLUMNS = (
    "source", "owner_kind", "owner_class_hash", "owner_field_hash",
    "called_hash_token", "call_count", "example_proto_id", "example_field_pc",
    "example_call_pc", "receiver_identity_confirmed",
)
SOURCES = {"event_ik", "main", "dll_util", "main_dynamic"}


def read_rows(path: Path, expected: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if not reader.fieldnames or any(name not in reader.fieldnames for name in expected):
            raise ValueError(f"Missing required columns in {path}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"Empty native evidence: {path}")
    return rows


def integer(value: str, label: str) -> int:
    try:
        result = int(value)
    except (ValueError, TypeError) as error:
        raise ValueError(f"Invalid {label}: {value!r}") from error
    if result < 0:
        raise ValueError(f"Negative {label}: {value!r}")
    return result


def token(value: str, kind: str) -> bool:
    return len(value) == 17 and value[0] == kind and all(
        char in "0123456789ABCDEF" for char in value[1:]
    )


def dump_tsv(columns: tuple[str, ...], rows: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, delimiter="\t",
                            lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def build(index: Path) -> tuple[dict[str, str], dict]:
    paths = {name: index / name for name in INPUTS}
    inputs = {name: paths[name].read_bytes() for name in INPUTS}
    f_rows = read_rows(paths[INPUTS[0]],
                       ("source", "class_hash", "function_hash", "root_pc",
                        "assignment_pc", "child_proto_id"))
    s_rows = read_rows(paths[INPUTS[1]],
                       ("source", "class_hash", "s_hash", "root_pc",
                        "settable_pc", "closure_proto_id"))
    calls = read_rows(paths[INPUTS[2]],
                      ("source", "hash_token", "proto_id", "parent_proto_id",
                       "field_pc", "field_offset_hex", "call_pc", "call_offset_hex",
                       "field_opcode"))

    owner: dict[tuple[str, int], dict[str, str]] = {}
    for kind, rows, proto_field, hash_field, assignment_field in (
        ("F", f_rows, "child_proto_id", "function_hash", "assignment_pc"),
        ("S", s_rows, "closure_proto_id", "s_hash", "settable_pc"),
    ):
        for row in rows:
            source = row["source"]
            proto = integer(row[proto_field], "child prototype")
            if source not in SOURCES or not token(row["class_hash"], "C") or not token(row[hash_field], kind):
                raise ValueError("Malformed native closure row")
            key = (source, proto)
            if key in owner:
                raise ValueError(f"Ambiguous root closure ownership: {key}")
            owner[key] = {
                "owner_kind": kind, "owner_class_hash": row["class_hash"],
                "owner_field_hash": row[hash_field],
                "owner_root_pc": str(integer(row["root_pc"], "root PC")),
                "owner_assignment_pc": str(integer(row[assignment_field], "assignment PC")),
            }

    details: list[dict] = []
    unmatched: list[dict] = []
    priority: dict[tuple[str, ...], dict] = {}
    joined_protos: set[tuple[str, int]] = set()
    seen_calls: set[tuple[str, int, int, int, str]] = set()
    counts = Counter()
    for call in calls:
        source = call["source"]
        proto = integer(call["proto_id"], "call proto ID")
        parent = int(call["parent_proto_id"])
        field = integer(call["field_pc"], "field PC")
        pc = integer(call["call_pc"], "call PC")
        field_hash = call["hash_token"]
        if source not in SOURCES or not token(field_hash, field_hash[0] if field_hash else "?") or field_hash[0] not in "SFE":
            raise ValueError("Malformed native field call row")
        if parent < -1 or pc <= field:
            raise ValueError("Invalid call parent or PC order")
        call_id = (source, proto, field, pc, field_hash)
        if call_id in seen_calls:
            raise ValueError(f"Duplicate native field call: {call_id}")
        seen_calls.add(call_id)
        key = (source, proto)
        scope = owner.get(key)
        if scope is not None and parent != 0:
            raise ValueError(f"Root-closure ownership has non-root parent: {key}/{parent}")
        status = ("NATIVE_ROOT_CLOSURE_PROTO_JOIN_ONLY" if scope is not None
                  else "UNMATCHED_NESTED_PROTO" if parent > 0
                  else "UNMATCHED_ROOT_OR_OTHER_PROTO")
        record = {
            "source": source, "proto_id": proto, "parent_proto_id": parent,
            "called_hash_token": field_hash, "field_pc": field,
            "field_offset_hex": call["field_offset_hex"], "call_pc": pc,
            "call_offset_hex": call["call_offset_hex"],
            "field_opcode": call["field_opcode"],
            **(scope or {field: "" for field in
                          ("owner_kind", "owner_class_hash", "owner_field_hash",
                           "owner_root_pc", "owner_assignment_pc")}),
            "join_status": status, "receiver_identity_confirmed": "NO",
            "original_name_confirmed": "NO",
        }
        details.append(record)
        counts[status] += 1
        if scope is None:
            unmatched.append({
                "source": source, "proto_id": proto, "parent_proto_id": parent,
                "called_hash_token": field_hash, "field_pc": field, "call_pc": pc,
                "status": status,
            })
            continue
        joined_protos.add(key)
        group = (source, scope["owner_kind"], scope["owner_class_hash"],
                 scope["owner_field_hash"], field_hash)
        if group not in priority:
            priority[group] = {
                "source": source, "owner_kind": scope["owner_kind"],
                "owner_class_hash": scope["owner_class_hash"],
                "owner_field_hash": scope["owner_field_hash"],
                "called_hash_token": field_hash, "call_count": 0,
                "example_proto_id": proto, "example_field_pc": field,
                "example_call_pc": pc, "receiver_identity_confirmed": "NO",
            }
        priority[group]["call_count"] += 1

    sorted_priority = sorted(priority.values(), key=lambda row: (
        -row["call_count"], row["source"], row["owner_class_hash"],
        row["owner_field_hash"], row["called_hash_token"]))
    report = {
        "version": "v2.0.2",
        "sources": {name: hashlib.sha256(inputs[name]).hexdigest() for name in INPUTS},
        "closure_edges_F": len(f_rows), "closure_edges_S": len(s_rows),
        "distinct_root_closure_proto_keys": len(owner),
        "field_call_edges": len(calls),
        "matched_root_closure_calls": counts["NATIVE_ROOT_CLOSURE_PROTO_JOIN_ONLY"],
        "matched_distinct_proto_keys": len(joined_protos),
        "unmatched_nested_proto_calls": counts["UNMATCHED_NESTED_PROTO"],
        "unmatched_root_or_other_calls": counts["UNMATCHED_ROOT_OR_OTHER_PROTO"],
        "unmatched_calls": len(unmatched),
        "matched_owner_kinds": dict(Counter(
            row["owner_kind"] for row in details if row["owner_kind"])),
        "distinct_owner_class_hashes_with_calls": len({
            row["owner_class_hash"] for row in details if row["owner_class_hash"]
        }),
        "class_method_called_hash_groups": len(priority),
        "unmatched_details": unmatched,
        "original_names_recovered": 0,
        "receiver_classes_confirmed": 0,
        "warning": (
            "source+proto_id joins the enclosing root-level closure definition "
            "only. It does not establish that a call's field receiver is the "
            "owner class, nor runtime execution, original name, or dynamic dispatch."
        ),
    }
    artifacts = {
        DETAIL: dump_tsv(DETAIL_COLUMNS, details),
        PRIORITY: dump_tsv(PRIORITY_COLUMNS, sorted_priority),
        SUMMARY: json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    }
    return artifacts, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=NATIVE)
    parser.add_argument("--out", type=Path, default=NATIVE)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    outputs, report = build(args.index)
    if args.check:
        for name, data in outputs.items():
            if not (args.out / name).exists() or (args.out / name).read_text(encoding="utf-8") != data:
                raise SystemExit(f"Missing/stale owner-join output: {args.out / name}")
    else:
        args.out.mkdir(parents=True, exist_ok=True)
        for name, data in outputs.items():
            (args.out / name).write_text(data, encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "unmatched_details"},
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
