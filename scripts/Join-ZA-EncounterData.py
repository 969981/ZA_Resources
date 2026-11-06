#!/usr/bin/env python3
"""Join authenticated ZA v2.0.2 BFBS exports into searchable CSV datasets.

This script is schema-driven for the raw decoder and deliberately conservative
for semantic joining: encounter references use exact encountDataId keys, while
zone IDs inferred from names are labeled as inference, never a native foreign key.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
from collections import Counter
from pathlib import Path

ZONE_PATTERN = re.compile(r"a\d{4}_w\d{2}")


def load(out, name):
    with gzip.open(out / (name + ".json.gz"), "rt", encoding="utf-8") as f:
        return json.load(f)


def rows(doc):
    for name in ("values", "root"):
        if isinstance(doc.get(name), list):
            return doc[name]
    return [doc]


def nested_rows(doc):
    for group in rows(doc):
        if isinstance(group, dict) and isinstance(group.get("root"), list):
            yield from group["root"]
        else:
            yield group


def compact(obj):
    if obj is None:
        return ""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def pick(d, k):
    if not isinstance(d, dict):
        return ""
    v = d.get(k)
    return "" if v is None else v


def emit(path, fields, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def build(out):
    encounters = list(nested_rows(load(out, "encounter")))
    spawners = list(nested_rows(load(out, "spawner")))
    transforms = list(nested_rows(load(out, "spawn_transform")))
    zones = rows(load(out, "field_wild_zone"))
    trainers = rows(load(out, "trainer"))
    drops = list(nested_rows(load(out, "pokemon_drop")))
    balls = list(nested_rows(load(out, "item_ball")))
    map_zone = {z["zoneID"]: z for z in zones if z.get("zoneID")}
    encounter_index = {e["id"]: e for e in encounters if e.get("id")}
    if len(encounter_index) != len(encounters):
        raise ValueError("duplicate or missing encounter IDs")
    tr_counts = Counter(t.get("Name") for t in transforms)
    tr_index = {t.get("Name"): t for t in transforms if t.get("Name")}

    enc_fields = [
        "encounterId", "speciesId", "formNo", "minLevel", "maxLevel",
        "rareRaw", "sexRaw", "natureRaw", "abilityRaw", "talentScale",
        "talentVNum", "oyabunProbability", "oyabunAdditionalLevel",
        "ivHp", "ivAtk", "ivDef", "ivSpAtk", "ivSpDef", "ivAgi",
        "wazaListJson", "itemDropInfoJson", "activationConditionsJson",
    ]
    flat_enc = []
    for e in encounters:
        iv = e.get("talentValue") or {}
        flat_enc.append({
            "encounterId": e["id"], "speciesId": pick(e, "devNo"),
            "formNo": pick(e, "formNo"), "minLevel": pick(e, "minLevel"),
            "maxLevel": pick(e, "maxLevel"), "rareRaw": pick(e, "rare"),
            "sexRaw": pick(e, "sex"), "natureRaw": pick(e, "seikaku"),
            "abilityRaw": pick(e, "tokusei"), "talentScale": pick(e, "talentScale"),
            "talentVNum": pick(e, "talentVNum"),
            "oyabunProbability": pick(e, "oyabunProbability"),
            "oyabunAdditionalLevel": pick(e, "oyabunAdditionalLevel"),
            "ivHp": pick(iv, "hp"), "ivAtk": pick(iv, "atk"),
            "ivDef": pick(iv, "def"), "ivSpAtk": pick(iv, "spAtk"),
            "ivSpDef": pick(iv, "spDef"), "ivAgi": pick(iv, "agi"),
            "wazaListJson": compact(e.get("wazaList")),
            "itemDropInfoJson": compact(e.get("itemDropInfoList")),
            "activationConditionsJson": compact(e.get("activationCondition")),
        })
    emit(out / "ZA_encounters_flat.csv", enc_fields, flat_enc)

    missing_ids = set()
    refs_count = 0
    referenced = set()
    positions_matched = 0
    positions_total = 0
    spawn_flat = []
    linked = []
    for sp in spawners:
        ident = sp.get("id", "")
        transform_rows = []
        for item in sp.get("appearanceSpawnerObjectInfoList", []):
            name = item.get("objectName", "")
            positions_total += 1
            found = tr_index.get(name)
            if found is not None:
                positions_matched += 1
            pos = (found or {}).get("Position") or {}
            rot = (found or {}).get("Rotation") or {}
            transform_rows.append({
                "objectName": name, "transformFound": found is not None,
                "x": pos.get("X"), "y": pos.get("Y"), "z": pos.get("Z"),
                "rotation": rot,
            })
            spawn_flat.append({
                "spawnerId": ident, "objectName": name,
                "matchedTransform": int(found is not None),
                "x": pick(pos, "X"), "y": pick(pos, "Y"), "z": pick(pos, "Z"),
                "rotationJson": compact(rot),
            })
        zone_match = ZONE_PATTERN.search(ident)
        zone = zone_match.group(0) if zone_match else ""
        zone_result = map_zone.get(zone) if zone else None
        for entry in sp.get("encountDataInfoList", []):
            rid = entry.get("encountDataId", "")
            refs_count += 1
            referenced.add(rid)
            e = encounter_index.get(rid)
            if e is None:
                missing_ids.add(rid)
            linked.append({
                "spawnerId": ident,
                "encounterId": rid,
                "speciesId": pick(e, "devNo"),
                "formNo": pick(e, "formNo"),
                "minLevel": pick(e, "minLevel"),
                "maxLevel": pick(e, "maxLevel"),
                "oyabunProbabilityRaw": pick(e, "oyabunProbability"),
                "oyabunAdditionalLevelRaw": pick(e, "oyabunAdditionalLevel"),
                "encounterWeightRaw": pick(entry, "weight"),
                "maxCount": pick(entry, "maxCount"),
                "zoneIdInferredFromSpawnerName": zone,
                "zoneNameInferred": (zone_result or {}).get("areaInfo", {}).get("areaName", ""),
                "spawnPositionsJson": compact(transform_rows),
                "activationConditionJson": compact(entry.get("activationCondition")),
                "refMatch": int(e is not None),
                "zoneMatchingMethod": "id_regex_heuristic" if zone else "unknown",
            })
    linked_fields = [
        "spawnerId", "encounterId", "speciesId", "formNo", "minLevel",
        "maxLevel", "oyabunProbabilityRaw", "oyabunAdditionalLevelRaw",
        "encounterWeightRaw", "maxCount", "zoneIdInferredFromSpawnerName",
        "zoneNameInferred", "spawnPositionsJson", "activationConditionJson",
        "refMatch", "zoneMatchingMethod",
    ]
    emit(out / "ZA_spawner_encounter_join.csv", linked_fields, linked)
    emit(out / "ZA_spawn_points.csv",
         ["spawnerId", "objectName", "matchedTransform", "x", "y", "z", "rotationJson"],
         spawn_flat)

    zone_flat = [{
        "zoneID": z.get("zoneID", ""),
        "areaName": z.get("areaInfo", {}).get("areaName", ""),
        "placeNameKey": z.get("areaInfo", {}).get("subAreaName", ""),
        "fastTravelFlagId": z.get("areaInfo", {}).get("fastTravelFlagId", ""),
        "layer": pick(z, "layer"), "bgm": z.get("areaInfo", {}).get("bgm", ""),
    } for z in zones]
    emit(out / "ZA_zones.csv",
         ["zoneID", "areaName", "placeNameKey", "fastTravelFlagId", "layer", "bgm"],
         zone_flat)

    party = []
    for t in trainers:
        for i in range(1, 7):
            p = t.get("poke" + str(i), {})
            if not isinstance(p, dict) or not p.get("devId"):
                continue
            party.append({
                "trainerId": t.get("trid", ""), "slot": i,
                "speciesId": p.get("devId", ""),
                "level": pick(p, "level"), "ballId": pick(p, "ballId"),
                "rareTypeRaw": pick(p, "rareType"),
                "natureRaw": pick(p, "seikaku"),
                "movesJson": compact({k: p.get(k) for k in ("waza1", "waza2", "waza3", "waza4")}),
            })
    emit(out / "ZA_trainer_parties.csv",
         ["trainerId", "slot", "speciesId", "level", "ballId",
          "rareTypeRaw", "natureRaw", "movesJson"], party)

    loot = []
    for kind, table in (("pokemon_drop", drops), ("field_item_ball", balls)):
        for row in table:
            for n, item in enumerate(row.get("itemLotteryDataList", [])):
                loot.append({
                    "sourceType": kind, "tableId": row.get("id", ""),
                    "entryIndex": n, "itemId": pick(item, "itemId"),
                    "maxCount": pick(item, "maxCount"),
                    "weightRaw": pick(item, "weight"),
                    "conditionJson": compact(item.get("activationCondition")),
                })
    emit(out / "ZA_item_lottery.csv",
         ["sourceType", "tableId", "entryIndex", "itemId", "maxCount",
          "weightRaw", "conditionJson"], loot)

    report = {
        "encounterRecords": len(encounters),
        "encounterUniqueIds": len(encounter_index),
        "spawnerRecords": len(spawners),
        "spawnerEncounterReferences": refs_count,
        "uniqueReferencedEncounterIds": len(referenced),
        "allReferencesResolved": not missing_ids,
        "unresolvedEncounterIds": sorted(missing_ids),
        "unreferencedEncounterRecords": len(set(encounter_index) - referenced),
        "positionObjects": positions_total,
        "positionTransformMatched": positions_matched,
        "uniqueTransformNames": len(tr_index),
        "duplicateTransformNames": sum(n > 1 for n in tr_counts.values()),
        "zonesWithNames": len(zone_flat),
        "trainerEntries": len(trainers),
        "trainerPartyPokemonWithDevId": len(party),
        "itemLotteryEntries": len(loot),
        "disclaimer": "Derived ID-regex zone matching is heuristic; omitted FlatBuffer scalar fields and flags need separate default-value/semantic validation. No shiny-lock conclusion.",
    }
    (out / "ZA_relation_summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if missing_ids:
        raise ValueError(f"unresolved encounter refs: {len(missing_ids)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path(".za-work/za-data"))
    args = ap.parse_args()
    build(args.input)


if __name__ == "__main__":
    main()
