#!/usr/bin/env python3
"""Probe schema-less ZA v2.0.2 EXL FlatBuffers.

This is structural, not semantic parsing. Exports record offsets and vtable
slot bytes without assigning field names, enum types, or item/dex meanings.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path

SOURCES = {
    "pokedex": "world/exl/pokedex_contents_data/pokedex_contents_data/pokedex_contents_data.bin",
    "dex_distribution": "world/exl/pokedex_sp_distribution_data/pokedex_sp_distribution_data/pokedex_sp_distribution_data.bin",
    "items": "world/exl/item_data/item_data/item_data.bin",
    "shops": "world/exl/shop/shop_item_lineup/shop_item_lineup.bin",
}
ROOT = Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual")


class FlatBuffer:
    def __init__(self, data):
        self.data = data

    def require(self, off, length):
        if not (0 <= off <= len(self.data) and 0 <= length <= len(self.data) - off):
            raise ValueError(f"out-of-range: {off}+{length} len={len(self.data)}")

    def u16(self, p):
        self.require(p, 2)
        return struct.unpack_from("<H", self.data, p)[0]

    def u32(self, p):
        self.require(p, 4)
        return struct.unpack_from("<I", self.data, p)[0]

    def i32(self, p):
        self.require(p, 4)
        return struct.unpack_from("<i", self.data, p)[0]

    def target(self, p):
        r = p + self.u32(p)
        self.require(r, 4)
        return r

    def slots(self, table):
        self.require(table, 4)
        vt = table - self.i32(table)
        vsize = self.u16(vt)
        objsize = self.u16(vt + 2)
        if vsize < 4 or vsize > 4096 or objsize < 4 or objsize > 65535:
            raise ValueError(f"invalid vtable metadata: vt={vt}, size={vsize}, object={objsize}")
        self.require(vt, vsize)
        self.require(table, objsize)
        slots = {}
        for fid in range((vsize - 4) // 2):
            offset = self.u16(vt + 4 + fid * 2)
            if offset:
                if offset >= objsize:
                    raise ValueError(f"field {fid} invalid offset {offset}/{objsize}")
                slots[fid] = offset
        return {"vtable": vt, "vtableBytes": vsize, "objectBytes": objsize, "fieldOffsets": slots}

    def table(self, addr, index):
        info = self.slots(addr)
        slots = info["fieldOffsets"]
        field_bytes = {}
        for k, shift in slots.items():
            p = addr + shift
            # Raw slice only (typed decode would need a schema).
            raw = self.data[p:min(addr + info["objectBytes"], p + 8)].hex()
            field_bytes[str(k)] = {"offsetInObject": shift, "rawHex": raw}
        return {
            "recordIndex": index, "tableOffset": addr, "vtableOffset": info["vtable"],
            "objectBytes": info["objectBytes"], "presentFields": field_bytes,
        }

    def parse_root_vector(self):
        root = self.u32(0)
        fields = self.slots(root)["fieldOffsets"]
        if 0 not in fields:
            raise ValueError("root table has no field-0 vector")
        vec = self.target(root + fields[0])
        n = self.u32(vec)
        if n > 1_000_000:
            raise ValueError(f"unreasonably large root vector: {n}")
        self.require(vec + 4, n * 4)
        records = [self.table(self.target(vec + 4 + i * 4), i) for i in range(n)]
        return root, vec, records


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--out", type=Path, default=Path(".za-work/za-data"))
    p.add_argument("--require-all", action="store_true")
    a = p.parse_args()
    root = a.repo / ROOT
    out = a.repo / a.out
    out.mkdir(parents=True, exist_ok=True)
    report = {"version": "ZA v2.0.2", "evidence": "STRUCTURE_ONLY", "files": {}}
    for name, relative in SOURCES.items():
        f = root / relative
        try:
            raw = f.read_bytes()
            parser = FlatBuffer(raw)
            table, vec, rows = parser.parse_root_vector()
            result = {
                "data": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw), "rootOffset": table,
                "vectorOffset": vec, "rootRecordCount": len(rows),
                "records": rows,
                "warning": "Raw field offsets/bytes only. No schema, no typed semantic or ID interpretation.",
            }
            (out / ("EXL_" + name + "_raw.json")).write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            with (out / ("EXL_" + name + "_raw.csv")).open("w", newline="", encoding="utf-8-sig") as handle:
                w = csv.writer(handle)
                w.writerow(["recordIndex", "tableOffset", "vtableOffset", "objectBytes", "presentFieldsJson"])
                for rec in rows:
                    w.writerow([
                        rec["recordIndex"], rec["tableOffset"], rec["vtableOffset"],
                        rec["objectBytes"], json.dumps(rec["presentFields"], separators=(",", ":")),
                    ])
            report["files"][name] = {
                "status": "STRUCTURE_ONLY", "rows": len(rows), "sha256": result["sha256"]
            }
            print(f"{name}: {len(rows)} raw records (NO field schema)")
        except Exception as exc:
            report["files"][name] = {"status": "FAILED", "error": str(exc)}
            print(f"{name}: FAILED: {exc}")
    (out / "EXL_raw_summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if a.require_all and any(x["status"] != "STRUCTURE_ONLY" for x in report["files"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
