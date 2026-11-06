#!/usr/bin/env python3
"""Export Pokémon Legends: Z-A v2.0.2 ItemData FlatBuffers without dependencies.

Usage:
  python scripts/Export-ZA-Items.py --repo . --version v2.0.2 --output .za-work/items
Original game resources are read-only; this script does not change them.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import struct
from collections import Counter
from pathlib import Path


def schema_fields(schema: str) -> list[tuple[str, str]]:
    match = re.search(r"\btable\s+ItemData\s*\{(.*?)\n\}", schema, re.S)
    if not match:
        raise ValueError("ItemData table missing from schema")
    fields = re.findall(r"^\s*(\w+)\s*:\s*(\w+)(?:\s*\([^;\n]*\))?\s*;", match.group(1), re.M)
    if not fields or fields[0][0] != "Id":
        raise ValueError("unexpected ItemData layout")
    return fields


class FlatReader:
    def __init__(self, data: bytes):
        self.data = data

    def read(self, fmt: str, offset: int):
        size = struct.calcsize(fmt)
        if offset < 0 or offset + size > len(self.data):
            raise ValueError(f"FlatBuffer out of bounds: {offset}+{size}")
        return struct.unpack_from("<" + fmt, self.data, offset)[0]

    def at(self, table: int, index: int) -> int | None:
        vtable = table - self.read("i", table)
        vt_size = self.read("H", vtable)
        entry = vtable + 4 + index * 2
        if entry + 2 > vtable + vt_size:
            return None
        delta = self.read("H", entry)
        return table + delta if delta else None

    def string(self, addr: int) -> str:
        start = addr + self.read("I", addr)
        length = self.read("I", start)
        end = start + 4 + length
        if length > len(self.data) or end > len(self.data):
            raise ValueError("invalid string length")
        return self.data[start + 4:end].decode("utf-8")

    def records(self, fields: list[tuple[str, str]]) -> list[dict]:
        root = self.read("I", 0)
        field = self.at(root, 0)
        if field is None:
            raise ValueError("ItemDataArray.Table missing")
        vector = field + self.read("I", field)
        count = self.read("I", vector)
        if count > 100000 or vector + 4 + count * 4 > len(self.data):
            raise ValueError(f"invalid record count: {count}")
        rows = []
        for i in range(count):
            element = vector + 4 + i * 4
            table = element + self.read("i", element)
            row = {}
            for j, (name, typ) in enumerate(fields):
                loc = self.at(table, j)
                if loc is None:
                    value = "" if typ == "string" else False if typ == "bool" else 0
                elif typ == "string":
                    value = self.string(loc)
                elif typ == "bool":
                    value = bool(self.read("B", loc))
                elif typ in {"int", "ItemType", "WazaID"}:
                    value = self.read("i", loc)
                else:
                    raise ValueError(f"unsupported ItemData field type: {name}={typ}")
                row[name] = value
            rows.append(row)
        return rows


def localizations(path: Path) -> list[str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document["messages"]
    if not isinstance(rows, list) or not all(x.get("index") == i for i, x in enumerate(rows)):
        raise ValueError(f"message indices not sequential: {path}")
    return [x["displayText"] for x in rows]


def group(row: dict) -> str:
    if re.search(r"进化石[ＸＹＺ]?$", row["NameZH"]):
        return "MegaStone"
    if row["NameEN"] in {"Red Orb", "Blue Orb"}:
        return "PrimalOrb"
    return "Other"


CONTROLS = {
    "Master Ball", "Moon Stone", "Fire Stone", "Sitrus Berry",
    "Lucky Egg", "Metal Coat", "Leftovers", "Life Orb", "Focus Sash",
    "Eviolite", "Assault Vest", "Mega Shard",
}


def export(repo: Path, version: str, out: Path) -> dict:
    root = repo / "Unpack" / version / "romfs" / "arc" / "data.trpfs"
    source = root / "virtual/world/exl/item_data/item_data/item_data.bin"
    texts = root / "virtual_converted/ik_message/dat"
    schema_path = repo / "tools/pkNX/FlatBuffers/ZA/Item/Schemas/ItemDataArray.fbs"
    fields = schema_fields(schema_path.read_text(encoding="utf-8"))
    data = source.read_bytes()
    rows = FlatReader(data).records(fields)
    zh = localizations(texts / "Simp_Chinese/common/itemname.dat.json")
    en = localizations(texts / "English/common/itemname.dat.json")
    for r in rows:
        ident = r["Id"]
        r["NameZH"] = zh[ident] if 0 <= ident < len(zh) else ""
        r["NameEN"] = en[ident] if 0 <= ident < len(en) else ""
        r["ResearchGroup"] = group(r)
    rows.sort(key=lambda r: r["Id"])
    ids = [r["Id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate item IDs")
    mega = [r for r in rows if r["ResearchGroup"] == "MegaStone"]
    orbs = [r for r in rows if r["ResearchGroup"] == "PrimalOrb"]
    controls = [r for r in rows if r["NameEN"] in CONTROLS]
    colnames = ["Id", "NameZH", "NameEN", "ResearchGroup"] + [x[0] for x in fields if x[0] != "Id"]
    out.mkdir(parents=True, exist_ok=True)

    def write_csv(filename: str, records: list[dict]):
        with (out / filename).open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=colnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(records)

    write_csv("za-v2.0.2-items-all-fields.csv", rows)
    write_csv("za-v2.0.2-mega-orbs-controls.csv", sorted(mega + orbs + controls, key=lambda r: r["Id"]))
    def common(records):
        return {k: records[0][k] for k, _ in fields
                if records and all(r[k] == records[0][k] for r in records)}
    summary = {
        "version": version, "sourcePath": str(source.relative_to(repo)).replace("\\", "/"),
        "sourceLength": len(data), "fieldCount": len(fields), "recordCount": len(rows),
        "minId": min(ids), "maxId": max(ids), "uniqueIds": len(set(ids)),
        "groups": {"MegaStone": len(mega), "PrimalOrb": len(orbs), "ordinaryControls": len(controls)},
        "itemTypeCounts": dict(sorted(Counter(r["ItemType"] for r in rows).items())),
        "pocketCounts": dict(sorted(Counter(r["Pocket"] for r in rows).items())),
        "megaCommonFields": common(mega), "primalOrbCommonFields": common(orbs),
        "megaIds": [r["Id"] for r in mega], "primalOrbIds": [r["Id"] for r in orbs],
    }
    (out / "za-v2.0.2-item-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--version", default="v2.0.2")
    p.add_argument("--output", type=Path, default=Path(".za-work/items"))
    args = p.parse_args()
    print(json.dumps(export(args.repo.resolve(), args.version, args.output.resolve()),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
