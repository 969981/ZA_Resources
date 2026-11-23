#!/usr/bin/env python3
"""Triage 58 unmatched Trinity points and 586 unlocated ZA Spawners.

Inputs are versioned CSV ledgers from za_encounter_crosswalk.py and the
unchanged raw PokemonSpawnerData array. Emits evidence-rated candidate
classifications, never a claim of in-game spawnability.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
from za_resource_inspect import FB


def load_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    if not rows:
        raise ValueError("No triage records to write")
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def scene_category(name):
    if name.startswith("test_"):
        return "test_object"
    if name.startswith("spn_boss_"):
        return "boss_scene_object"
    if name.startswith("spn_outzone_"):
        return "outzone_scene_object"
    if name.startswith("spn_a"):
        return "wild_zone_scene_object"
    return "other_scene_object"


def spawner_category(name):
    if name.startswith("id_zdm_"):
        return "dimension_pool_not_selected"
    if name.startswith("btl_"):
        return "battle_named_spawner"
    if name.startswith("id_sub"):
        return "quest_named_spawner"
    if name.startswith("spn_boss_"):
        return "boss_follower_or_helper"
    if name.startswith("id_spn"):
        return "generic_or_zone_named_spawner"
    return "other_unlocated_spawner"


def candidate_battle_id(scene_name):
    # ONLY a candidate: no raw field links the scene object's name to this ID.
    if not scene_name.startswith("spn_boss_") or not scene_name.endswith("_object"):
        return ""
    return "btl_" + scene_name.removesuffix("_object")



def raw_battles(path):
    """Read wild_btl_data_global.bin fields observed by
    Scan-ZA-Rare-ARM64.py: battle id=0, actor id=1, event id=9, context=14.
    Only exact actor-id joins are considered direct evidence.
    """
    content = Path(path).read_bytes()
    f = FB(content)
    result = []
    for i, battle in enumerate(f.tables(f.root(), 0)):
        result.append(dict(
            index=i, battle_id=f.string(battle, 0),
            actor_id=f.string(battle, 1), event_id=f.string(battle, 9),
            context_id=f.string(battle, 14)))
    return result, hashlib.sha256(content).hexdigest()


def raw_appearances(path):
    """Use schema PokemonSpawnerDataDBArray.fbs; retrieve required
    AppearanceSpawnerObjectInfoList.ObjectName and CreateScenePath.
    """
    content = Path(path).read_bytes()
    f = FB(content)
    records = defaultdict(list)
    for group in f.tables(f.root(), 0):
        for sp in f.tables(group, 0):
            sid = f.string(sp, 0)
            for a in f.tables(sp, 1):
                records[sid].append({
                    "object_name": f.string(a, 0),
                    "create_scene_path": f.string(a, 1),
                    "battle_area_id": f.string(a, 4),
                    "dungeon_name": f.string(a, 2),
                    "tags": "|".join(strings(f, a, 5)),
                })
    return records, hashlib.sha256(content).hexdigest()


def strings(f, obj, index):
    p, size = f.vec(obj, index)
    output = []
    for i in range(size):
        start = f.link(p + i * 4)
        n = f.u32(start)
        output.append(bytes(f.data[start + 4:start + 4 + n]).decode("utf8", "replace"))
    return output


def classify(scene_points, spawners, edges, raw=None, battles=None):
    by_source_name = defaultdict(list)
    for sp in spawners:
        for name in sp["object_names"].split("|"):
            if name:
                by_source_name[name].append(sp["id"])
    by_id = {sp["id"]: sp for sp in spawners}
    battle_by_actor = defaultdict(list)
    for row in battles or []:
        if row["actor_id"]:
            battle_by_actor[row["actor_id"]].append(row)
    scene_names = {p["name"] for p in scene_points}
    by_edges = defaultdict(list)
    for edge in edges:
        by_edges[edge["spawner_id"]].append(edge)

    missing_scenes = []
    for p in scene_points:
        if p["name"] in by_source_name:
            continue
        c = candidate_battle_id(p["name"])
        candidate = c if c in by_id else ""
        state = "CANDIDATE" if candidate else "UNKNOWN"
        family = scene_category(p["name"])
        missing_scenes.append(dict(
            object_name=p["name"], scene_path=p["scene"],
            family=family, x=p["x"], y=p["y"], z=p["z"],
            candidate_spawner_id=candidate, evidence=state,
            explanation=("boss naming pattern ONLY, not an ObjectName link" if candidate
                         else "no exact object-to-spawner reference in audited table"),
            location_candidates=p["locations"], location_distance=p["nearest_distance"],
        ))

    missing_spawners = []
    for sp in spawners:
        if int(sp["scene_placements"]) or int(sp["hyperspace_refs"]):
            continue
        sid = sp["id"]
        ar = (raw or {}).get(sid, [])
        unique_path = sorted({e["create_scene_path"] for e in ar if e["create_scene_path"]})
        area_ids = sorted({e["battle_area_id"] for e in ar if e["battle_area_id"]})
        named_scene = any(e["object_name"] in scene_names for e in ar)
        edge = by_edges.get(sid, [])
        fixed = sorted({e["official_template"] for e in edge if e["official_template"]})
        family = spawner_category(sid)
        battle_refs = battle_by_actor.get(sid, [])
        evidence = ("CONFIRMED_STATIC_BATTLE_TABLE_LINK" if battle_refs else
                    "CONFIRMED_STATIC_PKHEX_TEMPLATE" if fixed else
                    "CANDIDATE" if family != "other_unlocated_spawner" else "UNKNOWN")
        missing_spawners.append(dict(
            spawner_id=sid, family=family, evidence=evidence,
            classification_scope=("exact battle.actor_id -> PokemonSpawnerData.Id" if battle_refs
                                  else "official PKHeX template id match" if fixed
                                  else "prefix/transform/scene-path static investigation"),
            appearance_objects=sp["object_names"],
            raw_create_scene_paths="|".join(unique_path),
            raw_battle_area_ids="|".join(area_ids),
            direct_battle_table_refs=len(battle_refs),
            direct_battle_ids="|".join(sorted({x["battle_id"] for x in battle_refs})),
            direct_battle_event_ids="|".join(sorted({x["event_id"] for x in battle_refs if x["event_id"]})),
            raw_object_name_in_known_scene=int(named_scene),
            transform_name_matches=sp["transform_name_matches"],
            linked_encounter_ids="|".join(sorted({e["encounter_id"] for e in edge})),
            linked_encounter_edges=len(edge),
            official_template="|".join(fixed),
            spawner_condition_array_count=sp["spawner_conditions"],
            maxcount_enabled=sp["maxcount_enabled"],
            explanation=("not in selected Trinity points and not referenced by "
                         "dimension_wild_pokemon; runtime placement NOT disproven"),
        ))
    return missing_scenes, missing_spawners


def summary(missing_scenes, missing_spawners, paths, raw_sha, battle_sha=None, battle_rows=0):
    return dict(
        version="v2.0.2",
        evidence="DERIVED_STATIC_NO_RUNTIME_PROOF",
        counts=dict(unmatched_scene_objects=len(missing_scenes),
                    unlocated_spawners=len(missing_spawners),
                    scene_boss_name_candidates=sum(bool(x["candidate_spawner_id"])
                                                   for x in missing_scenes),
                    unlocated_transform_name_matches=sum(
                        int(x["transform_name_matches"]) > 0 for x in missing_spawners),
                    unlocated_with_pkhex_template=sum(
                        bool(x["official_template"]) for x in missing_spawners),
                    unlocated_with_exact_battle_actor_link=sum(
                        bool(x["direct_battle_table_refs"]) for x in missing_spawners),
                    original_battle_table_rows=battle_rows),
        scene_families=dict(Counter(x["family"] for x in missing_scenes)),
        spawner_families=dict(Counter(x["family"] for x in missing_spawners)),
        raw_create_scene_paths_nonempty=sum(
            bool(x["raw_create_scene_paths"]) for x in missing_spawners),
        source_files=[dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                      for p in paths],
        raw_spawner_sha256=raw_sha,
        raw_battle_sha256=battle_sha,
        caveats=[
            "No match in pkNX-selected scene files does not mean spawn is impossible",
            "Prefix-derived family is CANDIDATE, not in-game behavior",
            "Scene-to-battle naming candidates lack exact game-field references",
            "CreateScenePath is preserved raw and is not an actual spawn callback",
            "Battle table actor-id join confirms configuration, not runtime dispatch",
            "PKHeX exact template classifications apply to encounter IDs, not all spawners",
        ],
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ledger", type=Path, required=True,
                   help="Directory containing crosswalk CSVs")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--spawner-bin", type=Path,
                   help="Optional original PokemonSpawnerDataDBArray .bin")
    p.add_argument("--battle-bin", type=Path,
                   help="Optional original wild_btl_data_global.bin for exact ActorId links")
    p.add_argument("--strict", action="store_true",
                   help="Require pinned v2.0.2 gap counts 58 / 586")
    args = p.parse_args()
    files = [args.ledger / x for x in
             ("za_scene_points.csv", "za_spawners.csv", "za_spawner_encounter_edges.csv")]
    raw, raw_sha = raw_appearances(args.spawner_bin) if args.spawner_bin else (None, None)
    battles, battle_sha = raw_battles(args.battle_bin) if args.battle_bin else ([], None)
    missing_scenes, missing_spawners = classify(
        *(load_csv(path) for path in files), raw=raw, battles=battles)
    if args.strict and (len(missing_scenes), len(missing_spawners)) != (58, 586):
        raise ValueError(f"Unexpected v2.0.2 gaps: {len(missing_scenes)}, {len(missing_spawners)}")
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "za_unmatched_scene_objects.csv", missing_scenes)
    write_csv(args.output / "za_unlocated_spawners.csv", missing_spawners)
    result = summary(missing_scenes, missing_spawners, files, raw_sha,
                     battle_sha, len(battles))
    (args.output / "za_gap_triage_summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
