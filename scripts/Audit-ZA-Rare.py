#!/usr/bin/env python3
"""Audit ZA v2.0.2 encounter rare integers and event candidates without claiming shiny locks.

Only original rareRaw integer classes and encounter source names are evidence.
Shiny state remains UNKNOWN until main.elf game generation/rare branch is traced.
"""
from __future__ import annotations
import argparse
import collections
import csv
import json
from pathlib import Path

ROOT = Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/_tables")
EXAMPLES = {
    "sub_119_diancie": "side_event_diancie",
    "sub_120_mewtwo": "side_event_mewtwo",
    "m10_x": "story_xerneas",
    "m10_y": "story_yveltal",
    "m04_zygarde10": "story_zygarde_form",
    "ect_boss_0718_01": "zygarde_boss",
    "ect_a0102_w01_v01_z179_Qst074": "quest_mareep_exception",
}
EXPECTED = {0x1FFFFFFF: 281, 0x2FFFFFFF: 1, 0x3FFFFFFF: 1684}


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(path: Path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        w.writerows(rows)



def context_bucket(encounter_id: str) -> str:
    """Label from the *name prefix*, NOT a proven runtime encounter type."""
    import re
    if encounter_id.startswith("btl_ect_boss"):
        return "boss_battle_named"
    if encounter_id.startswith("ect_boss"):
        return "boss_config_named"
    if encounter_id.startswith("sub_"):
        return "side_quest_named"
    if re.match(r"^m\d+", encounter_id):
        return "story_named"
    if encounter_id.startswith("ect_outzone"):
        return "outzone_named"
    if encounter_id.startswith(("ect_zdm", "ect_d")):
        return "dimension_named"
    if encounter_id.startswith("ect_a") and "_w" in encounter_id:
        return "wildzone_named"
    return "other_named"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    args = ap.parse_args()
    base = args.repo.resolve() / ROOT
    enc = read(base / "encounters/ZA_encounters_flat.csv")
    names = {int(r["id"]): r["zhNameOrText"] for r in
             read(base / "names/ZA_species_names_zh.csv") if r["id"] != ""}
    found = collections.Counter()
    rows, selected = [], []
    for r in enc:
        number = int(r["rareRaw"])
        found[number] += 1
        sid = int(r["speciesId"])
        tag = EXAMPLES.get(r["encounterId"], "")
        mask = number & 0x0FFFFFFF
        row = [
            r["encounterId"], sid, names.get(sid, ""), r["formNo"],
            r["minLevel"], r["maxLevel"], number, f"0x{number:08X}",
            number >> 28, f"0x{mask:07X}",
            r["ivHp"], r["ivAtk"], r["ivDef"], r["ivSpAtk"],
            r["ivSpDef"], r["ivAgi"], r["wazaListJson"],
            tag, "unknown", "not_traced_in_main_elf",
        ]
        rows.append(row)
        if tag:
            selected.append(row)
    if found != EXPECTED:
        raise ValueError("2.0.2 rare distribution unexpectedly changed: " + str(found))
    if len(selected) != len(EXAMPLES):
        raise ValueError(f"Missing event candidate: {len(selected)} / {len(EXAMPLES)}")
    fields = [
        "encounterId", "speciesId", "speciesZh", "formNo",
        "minLevel", "maxLevel", "rareRaw", "rareHex",
        "highNibble", "low28MaskHex", "ivHp", "ivAtk", "ivDef",
        "ivSpAtk", "ivSpDef", "ivAgi", "wazaListJson",
        "exampleTag", "shinyLocked", "runtimeProof",
    ]
    write(base / "encounters/ZA_rare_static_audit.csv", fields, rows)
    write(base / "encounters/ZA_special_event_examples.csv", fields, selected)

    # Strict encounter ID join to the already-audited spawner reference table.
    # This does not prove any game-side invocation or shiny mechanism.
    joined = read(base / "encounters/ZA_spawner_encounter_join.csv")
    by_encounter = collections.defaultdict(list)
    for record in joined:
        by_encounter[record["encounterId"]].append(record)
    if sum(map(len, by_encounter.values())) != len(joined):
        raise ValueError("Rare/spawner reference count mismatch")

    matrix = collections.Counter()
    named_refs = collections.Counter()
    for record in enc:
        bucket = context_bucket(record["encounterId"])
        key = (bucket, record["rareRaw"])
        matrix[key] += 1
        named_refs[key] += len(by_encounter[record["encounterId"]])

    matrix_rows = []
    for (bucket, raw), count in sorted(matrix.items()):
        examples = [r["encounterId"] for r in enc
                    if context_bucket(r["encounterId"]) == bucket and r["rareRaw"] == raw][:5]
        matrix_rows.append([
            bucket, f"0x{int(raw):08X}", count, named_refs[(bucket, raw)],
            " | ".join(examples), "encounter_id_prefix_heuristic",
            "unverified_static_category",
        ])
    write(base / "encounters/ZA_rare_context_matrix.csv",
          ["namePrefixGroup", "rareHex", "encounterRecords",
           "spawnerReferences", "exampleEncounterIds",
           "groupingMethod", "runtimeSemantics"], matrix_rows)

    # Resolve specific named events with their real spawner IDs. Do not
    # silently rewrite the event label into a game-script caller.
    focus_rows = []
    for record in enc:
        identifier = record["encounterId"]
        if identifier not in EXAMPLES:
            continue
        hits = by_encounter[identifier]
        focus_rows.append([
            identifier, EXAMPLES[identifier],
            record["speciesId"], names.get(int(record["speciesId"]), ""),
            record["rareRaw"], f"0x{int(record['rareRaw']):08X}",
            record["minLevel"], record["maxLevel"],
            len(hits),
            " | ".join(sorted({h["spawnerId"] for h in hits})),
            " | ".join(sorted({h["zoneIdInferredFromSpawnerName"] for h in hits
                               if h["zoneIdInferredFromSpawnerName"]})),
            record["wazaListJson"],
            "/".join(record[k] or "(missing)" for k in (
                "ivHp", "ivAtk", "ivDef", "ivSpAtk", "ivSpDef", "ivAgi")),
            "unknown", "no_verified_main_rva",
        ])
    if len(focus_rows) != len(EXAMPLES):
        raise ValueError("Missing named special-event examples in focus join")
    write(base / "encounters/ZA_rare_event_spawner_crosscheck.csv",
          ["encounterId", "case", "speciesId", "speciesZh",
           "rareRaw", "rareHex", "minLevel", "maxLevel",
           "spawnerReferenceCount", "spawnerIds", "zoneHeuristic",
           "presetMovesJson", "ivRawSixStats",
           "shinyLocked", "runtimeProof"], focus_rows)

    summary = {
        "version": "2.0.2", "evidence": "static encounter BFBS decode",
        "status": "shiny-lock unknown / runtime branch not yet located",
        "encounterTotal": len(rows),
        "rareGroups": [
            {"rareHex": f"0x{k:08X}", "count": count,
             "highNibble": k >> 28, "low28MaskHex": f"0x{k&0xFFFFFFF:07X}"}
            for k, count in sorted(found.items())
        ],
        "selectedCaseIds": list(EXAMPLES),
        "contextMatrixRows": len(matrix_rows),
        "contextByNamePrefixOnly": [
            {"namePrefixGroup": bucket, "rareHex": f"0x{int(raw):08X}",
             "encounterRecords": count,
             "spawnerReferences": named_refs[(bucket, raw)]}
            for (bucket, raw), count in sorted(matrix.items())
        ],
        "specialEventSpawnerEvidence": [
            {"encounterId": row[0], "spawnerRefs": row[8], "spawnerIds": row[9]}
            for row in focus_rows
        ],
        "important": "Rare mode clustering is not shiny-lock proof. No inferred main+RVA.",
    }
    (base / "_audit/ZA_rare_static_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "SUCCESS", "events": len(selected),
                      "classes": summary["rareGroups"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
