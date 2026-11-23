#!/usr/bin/env python3
"""Read-only Z-A v2.0.2 encounter/Spawner/Dimension/Trinity FlatBuffers explorer.

No dependencies beyond Python standard library. Does not modify any source.
Results are source-level observations, not PKHeX encounter templates.
"""
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path


class FlatBufferError(ValueError):
    pass


class FB:
    def __init__(self, data):
        self.data = memoryview(data)

    def scalar(self, offset, fmt):
        try:
            return struct.unpack_from("<" + fmt, self.data, offset)[0]
        except (struct.error, ValueError) as ex:
            raise FlatBufferError(f"out-of-bounds {fmt} at 0x{offset:X}") from ex

    def u8(self, offset):
        return self.scalar(offset, "B")

    def u16(self, offset):
        return self.scalar(offset, "H")

    def u32(self, offset):
        return self.scalar(offset, "I")

    def i32(self, offset):
        return self.scalar(offset, "i")

    def f32(self, offset):
        return self.scalar(offset, "f")

    def root(self):
        result = self.u32(0)
        if result >= len(self.data):
            raise FlatBufferError("invalid root offset")
        return result

    def field(self, table, index):
        vtable = table - self.i32(table)
        if vtable < 0 or vtable + 4 > len(self.data):
            raise FlatBufferError(f"invalid vtable at 0x{vtable:X}")
        size = self.u16(vtable)
        ofs = 4 + 2 * index
        if ofs + 2 > size:
            return None
        displacement = self.u16(vtable + ofs)
        return table + displacement if displacement else None

    def link(self, ptr):
        dest = ptr + self.u32(ptr)
        if dest >= len(self.data):
            raise FlatBufferError(f"out-of-bounds uoffset at 0x{ptr:X}")
        return dest

    def obj(self, table, index):
        p = self.field(table, index)
        return self.link(p) if p is not None else None

    def number(self, table, index, kind="i32", default=0):
        p = self.field(table, index)
        return getattr(self, kind)(p) if p is not None else default

    def vec(self, table, index):
        p = self.field(table, index)
        if p is None:
            return None, 0
        v = self.link(p)
        n = self.u32(v)
        if n > 1_000_000 or v + 4 + n * 4 > len(self.data):
            raise FlatBufferError(f"invalid vector length at 0x{v:X}")
        return v + 4, n

    def tables(self, table, index):
        v, count = self.vec(table, index)
        return [self.link(v + i * 4) for i in range(count)]

    def string(self, table, index):
        p = self.field(table, index)
        if p is None:
            return ""
        target = self.link(p)
        length = self.u32(target)
        end = target + 4 + length
        if end > len(self.data):
            raise FlatBufferError("invalid string length")
        return bytes(self.data[target + 4:end]).decode("utf-8", errors="replace")

    def blob(self, table, index):
        p = self.field(table, index)
        if p is None:
            return b""
        target = self.link(p)
        length = self.u32(target)
        end = target + 4 + length
        if end > len(self.data):
            raise FlatBufferError("invalid byte vector length")
        return bytes(self.data[target + 4:end])

    def vec3(self, table, index):
        p = self.field(table, index)
        if p is None:
            return None
        return [round(self.f32(p + i * 4), 6) for i in range(3)]


def groups(fb):
    return [entry for db in fb.tables(fb.root(), 0) for entry in fb.tables(db, 0)]


def summarize_encount(fb, limit):
    rows = groups(fb)
    shiny = Counter()
    samples = []
    for row in rows:
        rare = fb.number(row, 6)
        shiny[f"0x{rare:08X}"] += 1
        if len(samples) < limit:
            samples.append({
                "id": fb.string(row, 0),
                "dev_no": fb.number(row, 1),
                "form": fb.number(row, 5),
                "level": [fb.number(row, 2), fb.number(row, 3)],
                "sex": fb.number(row, 4),
                "rare_raw": f"0x{rare:08X}",
                "alpha_probability": fb.number(row, 11, "f32"),
            })
    return {"db_count": len(fb.tables(fb.root(), 0)), "encounter_count": len(rows),
            "shiny_raw": dict(shiny), "samples": samples}


def summarize_spawner(fb, limit):
    rows = groups(fb)
    items = []
    for row in rows[:limit]:
        appearances = []
        for ap in fb.tables(row, 1):
            appearance = fb.obj(ap, 8)
            appearances.append({
                "name": fb.string(ap, 0),
                "scene": fb.string(ap, 1),
                "min_count": fb.number(appearance, 0) if appearance is not None else None,
                "max_count": fb.number(appearance, 1) if appearance is not None else None,
            })
        encounters = []
        for enc in fb.tables(row, 5):
            repop = fb.obj(enc, 11)
            encounters.append({
                "encount_data_id": fb.string(enc, 0), "weight": fb.number(enc, 1),
                "max_count": fb.number(enc, 2), "additional_level": fb.number(enc, 3),
                "time_condition": fb.number(enc, 6),
                "weather_condition": fb.number(enc, 7),
                "repop_after_captured": fb.number(repop, 0) if repop is not None else None,
                "repop_after_defeated": fb.number(repop, 1) if repop is not None else None,
            })
        cool = fb.obj(row, 4)
        items.append({
            "id": fb.string(row, 0), "appearances": appearances,
            "cooldown_condition": fb.number(cool, 0) if cool is not None else None,
            "cooldown_time": fb.number(cool, 1, "f32") if cool is not None else None,
            "encounters": encounters,
        })
    return {"db_count": len(fb.tables(fb.root(), 0)), "spawner_count": len(rows),
            "samples": items}


def summarize_transform(fb, limit):
    rows = groups(fb)
    # The numeric Position/Rotation representation requires byte-level
    # schema/bfbs cross-check. Do not assert coordinates using guessed offsets.
    samples = []
    for row in rows[:limit]:
        samples.append({
            "name": fb.string(row, 0),
            "position_field_hex": (bytes(fb.data[fb.field(row, 1):fb.field(row, 1) + 12]).hex()
                                   if fb.field(row, 1) is not None else None),
            "rotation_field_hex": (bytes(fb.data[fb.field(row, 2):fb.field(row, 2) + 12]).hex()
                                   if fb.field(row, 2) is not None else None),
            "attach_transform_enable": bool(fb.number(row, 3, "u8")),
        })
    return {"db_count": len(fb.tables(fb.root(), 0)), "transform_count": len(rows),
            "position_decoding": "UNVERIFIED: raw bytes, not coordinates", "samples": samples}


def summarize_dimension(fb, limit):
    poke = groups(fb)
    ranks = patterns = refs = 0
    unique_ids = set()
    samples = []
    for t in poke:
        for rank in fb.tables(t, 1):
            ranks += 1
            for pattern in fb.tables(rank, 1):
                patterns += 1
                for item in fb.tables(pattern, 2):
                    refs += 1
                    sid = fb.string(item, 0)
                    unique_ids.add(sid)
                    if len(samples) < limit:
                        samples.append({
                            "poke_type": fb.number(t, 0), "rank": fb.number(rank, 0),
                            "pattern": fb.number(pattern, 0),
                            "pattern_weight": fb.number(pattern, 1),
                            "spawner_id": sid, "spawner_weight": fb.number(item, 1),
                        })
    return {"db_count": len(fb.tables(fb.root(), 0)), "poke_types": len(poke),
            "rank_items": ranks, "pattern_items": patterns,
            "spawner_references": refs, "unique_spawner_ids": len(unique_ids),
            "samples": samples}


def summarize_scene(fb, limit):
    root = fb.root()
    entries = fb.tables(root, 4)
    stats = Counter()
    points = []
    child_count = 0

    def inspect(entry, nested=False):
        nonlocal child_count
        objtype = fb.string(entry, 0)
        stats[objtype] += 1
        children = fb.tables(entry, 2)
        child_count += len(children)
        if objtype == "trinity_ObjectTemplate":
            raw = fb.blob(entry, 1)
            sub = FB(raw)
            template = sub.root()
            if sub.string(template, 4) == "trinity_SceneObject":
                scene = FB(sub.blob(template, 5))
                obj = scene.root()
                pos = scene.obj(obj, 1)
                if len(points) < limit:
                    points.append({
                        "object_template_name": sub.string(template, 0),
                        "shape": scene.string(obj, 0),
                        "translation_xyz": scene.vec3(pos, 2) if pos is not None else None,
                        "nested": nested,
                    })
        for child in children:
            inspect(child, True)

    for e in entries:
        inspect(e)
    return {"scene_name": fb.string(root, 0), "top_level_objects": len(entries),
            "direct_and_recursive_child_links": child_count,
            "types_including_subobjects": dict(stats), "samples": points}


KINDS = {
    "encount_data_array.bin": summarize_encount,
    "pokemon_spawner_data_array.bin": summarize_spawner,
    "pokemon_spawner_transform_array.bin": summarize_transform,
    "dimension_wild_pokemon_array.bin": summarize_dimension,
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path, help="Local original .bin or .trscn")
    ap.add_argument("--kind", choices=["encount", "spawner", "transform", "dimension", "scene"],
                    help="Override detection")
    ap.add_argument("--limit", type=int, default=10, help="Maximum sample rows")
    ap.add_argument("--out", type=Path, help="Optional JSON report destination")
    args = ap.parse_args()
    if args.limit < 0:
        ap.error("--limit must be nonnegative")
    data = args.source.read_bytes()
    detected = KINDS.get(args.source.name)
    fn = {
        "encount": summarize_encount, "spawner": summarize_spawner,
        "transform": summarize_transform, "dimension": summarize_dimension,
        "scene": summarize_scene,
    }[args.kind] if args.kind else (
        summarize_scene if args.source.suffix.lower() == ".trscn" else detected)
    if fn is None:
        ap.error("unknown source format: supply --kind")
    report = fn(FB(data), args.limit)
    report.update(source=str(args.source), source_sha256=hashlib.sha256(data).hexdigest(),
                  source_size=len(data), file_type=args.kind or args.source.name)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    try:
        main()
    except (FlatBufferError, OSError, struct.error) as exc:
        raise SystemExit(f"Error: {exc}")
