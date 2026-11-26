#!/usr/bin/env python3
"""ZA v2.0.2 BFBS+BIN real data exporter (stdlib only).

Decodes actual FlatBuffers reflection schemas, not merely vtable bounds.
Unsupported union / vector64 / array types fail explicitly.
Input ROM assets are read-only. Output is deterministic and auditable.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import gzip
import hashlib
import json
import struct
import traceback
from pathlib import Path

VERSION = "za-reflection-export-1"
SOURCE_ROOT = Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual")
TARGETS = {
    "encounter": "world/ik_data/field/pokemon/encount_data/encount_data/encount_data_array",
    "spawner": "world/ik_data/field/pokemon_spawner/pokemon_spawner_data/pokemon_spawner_data_array",
    "pokemon": "world/ik_data/field/pokemon/pokemon_data/pokemon_data/pokemon_data_array",
    "wild_zone": "world/ik_data/field/zone/wild_zone_data/wild_zone",
    "field_wild_zone": "world/ik_data/field/area/field_wild_zone/field_wild_zone_array",
    "field_location": "world/ik_data/field/area/field_location/field_location_array",
    "field_scene_area": "world/ik_data/field/area/field_scene_area/field_scene_area_array",
    "spawn_transform": "world/ik_data/field/spawner_transform_data/pokemon_spawner_transform/pokemon_spawner_transform/pokemon_spawner_transform_array",
    "area_jump": "world/ik_data/field/area_jump/field_area_jump_point/field_area_jump_point_array",
    "oyabun_setting": "world/ik_data/field/oyabun/oyabun_setting/oyabun_setting",
    "oyabun_waza": "world/ik_data/field/oyabun/oyabun_waza/oyabun_waza",
    "waza_attribute": "world/ik_data/field/waza_attribute/waza_attribute_data/waza_attribute_data",
    "pokemon_drop": "world/ik_data/field/pokemon/pokemon_drop_item_table/pokemon_drop_item_table_data/pokemon_drop_item_table_data_array",
    "item_ball": "world/ik_data/field/item_ball/item_ball_item_data/item_ball_item_data/item_ball_item_data_array",
    "item_ball_spawner": "world/ik_data/field/item_ball/item_ball_spawner_data/item_ball_spawner_data/item_ball_spawner_data_array",
    "item_type": "world/ik_data/field/item/item_type_data/item_type_data",
    "trainer": "world/ik_data/trainer/trdata/trdata_array",
    "trainer_env": "world/ik_data/trainer/trenv/trenv_array",
    "capture": "world/ik_data/capture/capture_data/capture_data",
    "battle_setting": "world/ik_data/battle/battle_setting/battle_setting",
}
SCALAR = {
    1: ("B", 1), 2: ("?", 1), 3: ("b", 1), 4: ("B", 1),
    5: ("h", 2), 6: ("H", 2), 7: ("i", 4), 8: ("I", 4),
    9: ("q", 8), 10: ("Q", 8), 11: ("f", 4), 12: ("d", 8),
}
TYPE_NAMES = {
    0: "None", 1: "UType", 2: "Bool", 3: "Byte", 4: "UByte",
    5: "Short", 6: "UShort", 7: "Int", 8: "UInt", 9: "Long",
    10: "ULong", 11: "Float", 12: "Double", 13: "String",
    14: "Vector", 15: "Obj", 16: "Union", 17: "Array",
    18: "Vector64",
}


class DecodeError(ValueError):
    pass


class Buffer:
    def __init__(self, data: bytes):
        self.data = data
        self.size = len(data)

    def check(self, pos: int, size: int):
        if pos < 0 or size < 0 or pos + size > self.size:
            raise DecodeError(f"out of bounds: pos={pos} size={size} file={self.size}")

    def read(self, fmt: str, pos: int):
        n = struct.calcsize("<" + fmt)
        self.check(pos, n)
        return struct.unpack_from("<" + fmt, self.data, pos)[0]

    def u8(self, pos): return self.read("B", pos)
    def u16(self, pos): return self.read("H", pos)
    def u32(self, pos): return self.read("I", pos)
    def i32(self, pos): return self.read("i", pos)
    def scalar(self, ty, pos):
        if ty not in SCALAR:
            raise DecodeError(f"unsupported scalar type {TYPE_NAMES.get(ty, ty)}")
        return self.read(SCALAR[ty][0], pos)

    def field(self, table, field_id):
        self.check(table, 4)
        vtable = table - self.i32(table)
        vsize = self.u16(vtable)
        self.check(vtable, vsize)
        ix = 4 + field_id * 2
        if ix + 2 > vsize:
            return None
        relative = self.u16(vtable + ix)
        if relative == 0:
            return None
        pos = table + relative
        self.check(pos, 1)
        return pos

    def follow(self, pos):
        target = pos + self.u32(pos)
        self.check(target, 4)
        return target

    def field_ref(self, table, fid):
        p = self.field(table, fid)
        return self.follow(p) if p is not None else None

    def string(self, pos):
        ref = self.follow(pos)
        length = self.u32(ref)
        if length > 100_000_000:
            raise DecodeError("string too long")
        self.check(ref + 4, length)
        return self.data[ref + 4:ref + 4 + length].decode("utf-8", "strict")

    def vector(self, table, fid):
        start = self.field_ref(table, fid)
        if start is None:
            return []
        n = self.u32(start)
        if n > 2_000_000:
            raise DecodeError(f"vector too long: {n}")
        return [start + 4, n]

    def root(self):
        if self.size < 8:
            raise DecodeError("not a FlatBuffer")
        root = self.u32(0)
        self.check(root, 4)
        return root


class Reflection:
    def __init__(self, data: bytes):
        self.b = Buffer(data)
        if data[4:8] != b"BFBS":
            raise DecodeError("not a BFBS reflection schema")
        root = self.b.root()
        vec = self.b.vector(root, 0)
        if not vec:
            raise DecodeError("reflection has no objects")
        start, count = vec
        self.b.check(start, count * 4)
        self.offsets = [self.b.follow(start + i * 4) for i in range(count)]
        self.objects = []
        for obj in self.offsets:
            name = self.b.string(self.b.field(obj, 0))
            fields = []
            fv = self.b.vector(obj, 1)
            if fv:
                p, n = fv
                self.b.check(p, n * 4)
                for j in range(n):
                    f = self.b.follow(p + j * 4)
                    ty = self.b.field_ref(f, 1)
                    if ty is None:
                        raise DecodeError(f"missing reflected type: {name}")
                    fields.append({
                        "name": self.b.string(self.b.field(f, 0)),
                        "id": self._u16_field(f, 2),
                        "offset": self._u16_field(f, 3),
                        "base": self._u8_field(ty, 0),
                        "element": self._u8_field(ty, 1),
                        "index": self._i32_field(ty, 2, -1),
                    })
            self.objects.append({
                "name": name,
                "is_struct": bool(self._u8_field(obj, 2)),
                "bytesize": self._i32_field(obj, 4, 0),
                "fields": fields,
            })
        rt = self.b.field_ref(root, 4)
        if rt is None or rt not in self.offsets:
            raise DecodeError("missing or invalid root table reflection")
        self.root_index = self.offsets.index(rt)

    def _u8_field(self, table, i, default=0):
        p = self.b.field(table, i)
        return self.b.u8(p) if p is not None else default

    def _u16_field(self, table, i, default=0):
        p = self.b.field(table, i)
        return self.b.u16(p) if p is not None else default

    def _i32_field(self, table, i, default=0):
        p = self.b.field(table, i)
        return self.b.i32(p) if p is not None else default


class Decoder:
    def __init__(self, schema: Reflection, payload: bytes, max_depth=48):
        self.schema = schema
        self.b = Buffer(payload)
        self.max_depth = max_depth
        self.visits = 0

    def decode(self):
        root_obj = self.schema.objects[self.schema.root_index]
        if root_obj["is_struct"]:
            raise DecodeError("struct cannot be root table")
        return self.object(self.b.root(), self.schema.root_index, 0)

    def object(self, at, index, depth):
        if depth > self.max_depth:
            raise DecodeError(f"max depth {self.max_depth} exceeded")
        if index < 0 or index >= len(self.schema.objects):
            raise DecodeError(f"invalid object type index {index}")
        self.visits += 1
        if self.visits > 5_000_000:
            raise DecodeError("too many object visits")
        ob = self.schema.objects[index]
        result = {}
        for field in ob["fields"]:
            pos = at + field["offset"] if ob["is_struct"] else self.b.field(at, field["id"])
            if pos is None:
                continue  # absent field: don't conflate default with explicit value
            ty, el, sub = field["base"], field["element"], field["index"]
            if ty in SCALAR:
                result[field["name"]] = self.b.scalar(ty, pos)
            elif ty == 13:
                result[field["name"]] = self.b.string(pos)
            elif ty == 15:
                target = pos if self.schema.objects[sub]["is_struct"] else self.b.follow(pos)
                result[field["name"]] = self.object(target, sub, depth + 1)
            elif ty == 14:
                vec = self.b.follow(pos)
                n = self.b.u32(vec)
                if n > 2_000_000:
                    raise DecodeError(f"oversized vector ({n}) in {field['name']}")
                start = vec + 4
                if el in SCALAR:
                    width = SCALAR[el][1]
                    self.b.check(start, n * width)
                    values = [self.b.scalar(el, start + i * width) for i in range(n)]
                elif el == 13:
                    self.b.check(start, n * 4)
                    values = [self.b.string(start + i * 4) for i in range(n)]
                elif el == 15:
                    if sub < 0 or sub >= len(self.schema.objects):
                        raise DecodeError(f"invalid vector object index {sub}")
                    nested = self.schema.objects[sub]
                    width = nested["bytesize"] if nested["is_struct"] else 4
                    if width <= 0:
                        raise DecodeError("invalid struct bytesize")
                    self.b.check(start, n * width)
                    values = [
                        self.object(start + i * width if nested["is_struct"] else self.b.follow(start + i * width),
                                    sub, depth + 1)
                        for i in range(n)
                    ]
                else:
                    raise DecodeError(f"unsupported vector element {TYPE_NAMES.get(el, el)}")
                result[field["name"]] = values
            else:
                raise DecodeError(f"unsupported reflected type {TYPE_NAMES.get(ty, ty)} in {field['name']}")
        return result


def flatten_primary(document):
    """Expose actual root records without inventing semantic joins."""
    if not isinstance(document, dict):
        return [], "not_object"
    for key in ("values", "root", "table"):
        val = document.get(key)
        if isinstance(val, list):
            return val, key
    return [document], "single_object"


def summary_structure(doc, max_samples):
    records, key = flatten_primary(doc)
    group_counts = {}
    # For DBArray: top-level objects may each wrap another root vector.
    for row in records:
        if isinstance(row, dict):
            for k, v in row.items():
                if isinstance(v, list):
                    group_counts[k] = group_counts.get(k, 0) + len(v)
    return {
        "rootKey": key, "rootRecordCount": len(records),
        "nestedArrayElementCounts": group_counts,
        "sampleRecords": records[:max_samples],
    }


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def write_json(path, data, gz=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    if gz:
        with gzip.open(path, "wb", compresslevel=6) as stream:
            stream.write(payload)
    else:
        path.write_bytes(payload)


def run_one(args):
    key, stem, root, out, samples, csv_rows = args
    bfbs_path = root / (stem + ".bfbs")
    bin_path = root / (stem + ".bin")
    row = {"name": key, "source": stem, "status": "FAILED", "error": ""}
    try:
        if not bin_path.is_file() or not bfbs_path.is_file():
            raise FileNotFoundError(f"missing schema/binary: {bfbs_path} / {bin_path}")
        binary, raw_schema = bin_path.read_bytes(), bfbs_path.read_bytes()
        row.update({"bytes": len(binary), "binarySha256": sha(binary),
                    "schemaSha256": sha(raw_schema), "schemaBytes": len(raw_schema)})
        schema = Reflection(raw_schema)
        decoder = Decoder(schema, binary)
        result = decoder.decode()
        preview = summary_structure(result, samples)
        records, root_key = flatten_primary(result)
        write_json(out / (key + ".json.gz"), result, True)
        write_json(out / (key + ".preview.json"), preview)
        # Avoid inventing ID/foreign key semantics. Nested values remain JSON in CSV.
        with (out / (key + ".records.csv")).open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.writer(stream)
            writer.writerow(["index", "row_json"])
            for i, record in enumerate(records[:csv_rows]):
                writer.writerow([i, json.dumps(record, ensure_ascii=False, separators=(",", ":"))])
        row.update({
            "status": "DECODED_REFLECTION",
            "schemaRoot": schema.objects[schema.root_index]["name"],
            "objectTypes": len(schema.objects), "decodedObjects": decoder.visits,
            "rootKey": root_key, "rootRecordCount": len(records),
            "nestedArrayElementCounts": preview["nestedArrayElementCounts"],
            "previewPath": key + ".preview.json",
            "dataPath": key + ".json.gz",
            "csvPath": key + ".records.csv",
        })
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["traceback"] = traceback.format_exc(limit=3)
    return row


def cli():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=Path(".za-work/za-data"))
    ap.add_argument("--only", nargs="*", choices=sorted(TARGETS), help="select a few named tables")
    ap.add_argument("--all-pairs", action="store_true", help="scan all BFBS/BIN pairs (can be slow)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--csv-max-rows", type=int, default=50000)
    ap.add_argument("--require-all", action="store_true")
    ns = ap.parse_args()
    root = (ns.repo / SOURCE_ROOT).resolve()
    out = (ns.repo / ns.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        ap.error(f"missing source directory: {root}")
    if ns.all_pairs:
        selected = {}
        for f in root.rglob("*.bfbs"):
            stem = f.relative_to(root).as_posix()[:-5]
            if (root / (stem + ".bin")).is_file():
                selected["file_" + hashlib.sha256(stem.encode()).hexdigest()[:16]] = stem
    elif ns.only:
        selected = {k: TARGETS[k] for k in ns.only}
    else:
        selected = TARGETS
    jobs = [(k, p, root, out, max(0, ns.samples), max(0, ns.csv_max_rows))
            for k, p in selected.items()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(ns.workers, 16))) as pool:
        result = list(pool.map(run_one, jobs))
    report = {
        "version": VERSION,
        "game": "ZA v2.0.2",
        "count": len(jobs),
        "succeeded": sum(x["status"] == "DECODED_REFLECTION" for x in result),
        "failed": sum(x["status"] != "DECODED_REFLECTION" for x in result),
        "files": result,
        "warning": "Reflection decoding only: field names are raw; enum semantics, shiny locks and IDs require cross-validation.",
    }
    write_json(out / "manifest.json", report)
    with (out / "manifest.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        fields = ["name", "status", "bytes", "rootRecordCount", "schemaRoot", "binarySha256", "source", "error"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result)
    for x in result:
        print(f"{x['name']:<22} {x['status']:<22} rows={x.get('rootRecordCount', '-')} {x.get('error', '')}", flush=True)
    print(f"RESULT: {report['succeeded']}/{report['count']} decoded; output={out}", flush=True)
    if report["failed"] and ns.require_all:
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
