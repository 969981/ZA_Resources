#!/usr/bin/env python3
"""Summarize all ZA v2.0.2 ItemType×Pocket combinations from exported ItemData.

Does not infer gameplay permissions. Labels are explicitly marked as analyst
classifications, not recovered game enum names. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

LABELS = {
    (0,4): "重要/剧情/任务道具",
    (1,5): "树果",
    (2,0): "恢复 HP、状态与复活物品",
    (2,2): "能力培养（营养饮料/羽毛/糖果/薄荷）",
    (3,2): "瓶盖、兑换货币与特殊素材",
    (3,3): "出售用贵重物与素材",
    (3,4): "卡娜莉玩偶（可收集类）",
    (4,1): "精灵球",
    (5,6): "招式学习器",
    (7,2): "一般携带物、进化石、形态用物品",
    (7,7): "Mega 石",
    (9,2): "进化用特殊道具及化石",
}
COLS = ("Id", "NameZH", "NameEN", "ItemType", "Pocket",
        "ResearchMeaningZH", "SlotMaxNum", "CanNotHold", "InternalName",
        "WorkFormChange", "Price", "PriceMegaShard", "MachineIndex", "MachineWaza")


def group_items(source: Path, destination: Path) -> dict:
    with source.open("r", encoding="utf-8-sig", newline="") as file:
        data = list(csv.DictReader(file))
    if not data:
        raise ValueError(f"empty data: {source}")
    groups = defaultdict(list)
    for row in data:
        key = (int(row["ItemType"]), int(row["Pocket"]))
        groups[key].append(row)
    ids = [int(r["Id"]) for r in data]
    if len(ids) != len(set(ids)):
        raise ValueError("ItemData primary keys not unique")
    for rows in groups.values():
        rows.sort(key=lambda r: int(r["Id"]))
    if len(data) == 535 and set(groups) != set(LABELS):
        raise ValueError("v2.0.2 unexpectedly changed: verify all type/pocket keys")
    export = []
    for key in sorted(groups):
        for r in groups[key]:
            row = {k: r.get(k, "") for k in COLS}
            row["ResearchMeaningZH"] = LABELS.get(key, "UNKNOWN")
            export.append(row)
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / "za-v2.0.2-items-grouped.csv").open(
            "w", encoding="utf-8-sig", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=COLS)
        writer.writeheader()
        writer.writerows(export)
    stats = {
        "version": "v2.0.2",
        "sourceCsv": source.as_posix(),
        "total": len(data),
        "groupCount": len(groups),
        "itemTypeCounts": dict(sorted(Counter(int(r["ItemType"]) for r in data).items())),
        "pocketCounts": dict(sorted(Counter(int(r["Pocket"]) for r in data).items())),
        "groups": [
            {
                "itemType": t,
                "pocket": p,
                "count": len(groups[t,p]),
                "researchLabelZH": LABELS.get((t,p), "UNKNOWN"),
                "evidence": "DERIVED_FROM_NAMES_NOT_NATIVE_ENUM",
                "items": [
                    {
                        "id": int(r["Id"]),
                        "nameZH": r["NameZH"],
                        "nameEN": r["NameEN"],
                        "slotMaxNum": int(r["SlotMaxNum"]),
                        "canNotHold": r["CanNotHold"].lower() == "true",
                    }
                    for r in groups[t,p]
                ],
            }
            for (t,p) in sorted(groups)
        ],
        "notes": [
            "The labels are research interpretations of real item names, not recovered official enum identifiers.",
            "Use numeric ID as primary key; some Chinese display names repeat.",
        ],
    }
    (destination / "za-v2.0.2-itemtype-pocket-groups.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=Path(".za-work/items/za-v2.0.2-items-all-fields.csv"))
    parser.add_argument("--output", type=Path, default=Path(".za-work/items"))
    args = parser.parse_args()
    summary = group_items(args.input, args.output)
    print(json.dumps({
        "total": summary["total"], "groups": summary["groupCount"],
        "itemTypeCounts": summary["itemTypeCounts"],
        "pocketCounts": summary["pocketCounts"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
