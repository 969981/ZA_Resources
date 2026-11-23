#!/usr/bin/env python3
"""Trace ZA event trigger Command 53 -> battle ID -> actor/Spawner -> Encounter ID.

Evidence levels: exact FlatBuffers fields are STATIC_CONFIRMED; actual
event dispatch, task predicates, spawn execution and PKM legality remain
UNKNOWN_RUNTIME. All source bytes are read-only.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

from za_resource_inspect import FB, FlatBufferError
from za_encounter_crosswalk import vec_strings
from za_gap_triage import raw_battles


def read_trigger(data, relative_path):
    f = FB(data)
    triggers = f.tables(f.root(), 0)
    entries = []
    command_counts = Counter()
    for trigger_index, trig in enumerate(triggers):
        start = f.obj(trig, 0)
        if start is None:
            continue
        activation = f.tables(start, 2)
        for ai, act in enumerate(activation):
            conditions = []
            for ei, element in enumerate(f.tables(act, 0)):
                for pi, param in enumerate(f.tables(element, 0)):
                    conditions.append({
                        "element": ei, "param": pi, "name": f.string(param, 0),
                        "op": f.number(param, 1),
                        "arguments": vec_strings(f, param, 2),
                    })
            for ci, command_group in enumerate(f.tables(act, 1)):
                for ei, cmd in enumerate(f.tables(command_group, 0)):
                    code = f.number(cmd, 0)
                    command_counts[code] += 1
                    if code != 53:
                        continue
                    params = vec_strings(f, cmd, 1)
                    entries.append({
                        "source": relative_path,
                        "trigger_index": trigger_index,
                        "start_type_raw": f.number(start, 0, "u32"),
                        "start_params": json.dumps(vec_strings(f, start, 1),
                                                   ensure_ascii=False, separators=(",", ":")),
                        "activation_index": ai,
                        "command_group": ci,
                        "command_index": ei,
                        "command_raw": code,
                        "battle_id": params[0] if params else "",
                        "all_command_params": json.dumps(params, ensure_ascii=False,
                                                         separators=(",", ":")),
                        "activation_conditions": json.dumps(conditions, ensure_ascii=False,
                                                            separators=(",", ":")),
                    })
    return entries, command_counts, len(triggers)


def join_links(links, battles, edges):
    by_battle = defaultdict(list)
    for b in battles:
        if b["battle_id"]:
            by_battle[b["battle_id"]].append(b)
    by_sp = defaultdict(set)
    for edge in edges:
        by_sp[edge["spawner_id"]].add(edge["encounter_id"])
    output = []
    for row in links:
        found = by_battle.get(row["battle_id"], ())
        if not found:
            output.append({
                **row, "exact_battle_matches": 0, "exact_actor_id": "",
                "exact_event_id": "", "encounter_ids": "",
                "evidence": "UNKNOWN_BATTLE_ID",
            })
        else:
            for b in found:
                actor = b["actor_id"]
                result = {
                    **row, "exact_battle_matches": len(found), "exact_actor_id": actor,
                    "exact_event_id": b["event_id"],
                    "encounter_ids": "|".join(sorted(by_sp.get(actor, ()))),
                    "evidence": ("STATIC_EXACT_BATTLE_ACTOR_ENCOUNTER" if by_sp.get(actor)
                                 else "STATIC_EXACT_BATTLE_ACTOR" if actor
                                 else "UNKNOWN_ACTOR"),
                }
                output.append(result)
    return output


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"No rows to publish: {path}")
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def execute(virtual_root, battle_path, ledger_path, out, strict=False):
    battles, battle_sha = raw_battles(battle_path)
    with Path(ledger_path).open(newline="", encoding="utf-8") as f:
        edges = list(csv.DictReader(f))
    trigger_root = Path(virtual_root) / "ik_event/bin/trigger"
    if not trigger_root.is_dir():
        raise FileNotFoundError(trigger_root)
    files = sorted(trigger_root.rglob("*.bin"))
    if not files:
        raise ValueError("No original trigger .bin files")
    all_links = []
    source_manifest = []
    histogram = Counter()
    error_samples = []
    trigger_total = 0
    for path in files:
        data = path.read_bytes()
        rel = path.relative_to(virtual_root).as_posix()
        try:
            entries, counts, num_triggers = read_trigger(data, rel)
            all_links.extend(entries)
            histogram.update(counts)
            trigger_total += num_triggers
            status = "PARSED"
            error = ""
        except (FlatBufferError, IndexError, ValueError, TypeError) as exc:
            status = "PARSE_FAILED"
            error = f"{type(exc).__name__}: {str(exc)[:250]}"
            error_samples.append({"path": rel, "error": error})
        source_manifest.append({
            "file": rel, "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "status": status, "command53_entries": len(entries) if status == "PARSED" else 0,
            "parse_error": error,
        })
    joined = join_links(all_links, battles, edges)
    if strict:
        targets = {x["battle_id"] for x in joined}
        if not {"btl_sub_119", "btl_sub_120"} <= targets:
            raise ValueError("EX1/EX2 trigger Battle53 evidence missing")
        if error_samples:
            raise ValueError(f"{len(error_samples)} trigger files could not parse")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "za_trigger_battle_links.csv", joined)
    write_csv(out / "za_trigger_source_manifest.csv", source_manifest)
    summary = {
        "version": "v2.0.2",
        "status": "STATIC_EXACT_TRIGGER_BATTLE_ACTOR_NO_RUNTIME_EXECUTION",
        "counts": {
            "trigger_source_files": len(files),
            "trigger_files_parsed": len(files) - len(error_samples),
            "trigger_files_failed": len(error_samples),
            "raw_trigger_rows_parsed": trigger_total,
            "command_53_references": len(all_links),
            "joined_link_rows": len(joined),
            "exact_battle_matches": sum(z["exact_battle_matches"] > 0 for z in joined),
            "distinct_battle_ids": len({x["battle_id"] for x in all_links if x["battle_id"]}),
            "distinct_spawner_ids": len({x["exact_actor_id"] for x in joined if x["exact_actor_id"]}),
            "linked_to_encounter_ids": sum(bool(x["encounter_ids"]) for x in joined),
        },
        "command_counts": {str(k): v for k,v in histogram.most_common()},
        "failed_files": error_samples[:50],
        "battle_original_sha256": battle_sha,
        "evidence_limits": [
            "Command 53 uses an ID pointing to the wild-battle table; runtime dispatch unverified",
            "An exact battle.actor_id -> spawner.Id -> EncountDataId chain is static evidence only",
            "Trigger ActivationCondition is an input predicate; not evaluated during audit",
            "Battle/event IDs not found in this table might belong to other battle assets",
            "Only parsed trigger binaries count; failures retained in manifest",
        ],
    }
    (out / "za_trigger_battle_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--virtual-root", type=Path, required=True)
    p.add_argument("--battle-bin", type=Path, required=True)
    p.add_argument("--edges", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()
    result = execute(args.virtual_root, args.battle_bin, args.edges,
                     args.output, strict=args.strict)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
