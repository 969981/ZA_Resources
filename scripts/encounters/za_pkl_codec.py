#!/usr/bin/env python3
"""Read, export, edit, rebuild, diff and validate PKHeX Legends: Z-A PKL files.

ZA *.pkl is NOT Python pickle. It is a little-endian BinLinker16 with
8-byte EncounterSlot9a records. No unsafe pickle import or code execution.
Editing affects a PKHeX encounter resource, never game RomFS or a save file.

All commands that produce files use exclusive-create: original files are never
overwritten, even if a caller accidentally passes an input as --out.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct

MAGIC = b"za"
SLOT = struct.Struct("<HBBBBBB")
FIELDS = ("Species", "Form", "Gender", "LevelMin", "LevelMax", "IsAlpha", "Shiny")
SHINY_LABELS = {0: "Random", 1: "Never", 2: "Always"}
SHINY_CODES = {label: code for code, label in SHINY_LABELS.items()}
FORMAT = "PKHeX-ZA-BinLinker16"
FORMAT_VERSION = 1


class PKLFormatError(ValueError):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def exact_int(value, name, lo, hi):
    if type(value) is not int or not lo <= value <= hi:
        raise PKLFormatError(f"{name} must be integer in {lo}..{hi}; received {value!r}")
    return value


def validate_slot(s):
    if type(s) is not dict or set(s) != set(FIELDS):
        raise PKLFormatError(f"Each slot must contain exactly {FIELDS}, got {s!r}")
    species = exact_int(s["Species"], "Species", 1, 65535)
    form = exact_int(s["Form"], "Form", 0, 255)
    gender = exact_int(s["Gender"], "Gender", -1, 255)
    if gender not in (-1, 0, 1, 2, 255):
        raise PKLFormatError(f"Invalid gender byte {gender}")
    if gender == -1:
        gender = 255
    low = exact_int(s["LevelMin"], "LevelMin", 1, 100)
    high = exact_int(s["LevelMax"], "LevelMax", low, 100)
    if type(s["IsAlpha"]) is not bool:
        raise PKLFormatError("IsAlpha must be JSON true/false")
    shiny = s["Shiny"]
    if type(shiny) is str:
        if shiny not in SHINY_CODES:
            raise PKLFormatError(f"Shiny must be Random, Never, Always: {shiny!r}")
        shiny = SHINY_CODES[shiny]
    elif type(shiny) is int:
        shiny = exact_int(shiny, "Shiny", 0, 2)
    else:
        raise PKLFormatError(f"Invalid Shiny value {shiny!r}")
    return (species, form, gender, low, high, int(s["IsAlpha"]), shiny)


def read_pkl(data):
    """Strictly decode, preserving area and slot ordering for byte-identical roundtrip."""
    if not isinstance(data, bytes):
        raise TypeError("read_pkl accepts bytes")
    if len(data) < 8 or data[:2] != MAGIC:
        raise PKLFormatError("Not a ZA BinLinker16 file (expected 7a 61 header)")
    count = struct.unpack_from("<H", data, 2)[0]
    header_end = 4 + 2 * (count + 1)
    if count == 0 or header_end > len(data):
        raise PKLFormatError("Invalid/truncated area offset table")
    offsets = struct.unpack_from("<" + "H" * (count + 1), data, 4)
    if offsets[0] != header_end or offsets[-1] != len(data):
        raise PKLFormatError("Noncanonical first/last offsets, unsupported trailer or corruption")
    if any(b <= a for a, b in zip(offsets, offsets[1:])):
        raise PKLFormatError("Offsets must be strictly increasing")
    areas = []
    seen = set()
    for i in range(count):
        start, end = offsets[i], offsets[i+1]
        if end - start < 4 or (end - start - 4) % SLOT.size:
            raise PKLFormatError(f"Area[{i}] has invalid byte length {end - start}")
        location, reserved = struct.unpack_from("<HH", data, start)
        if location == 0 or reserved != 0 or location in seen:
            raise PKLFormatError(f"Area[{i}] invalid/duplicate location or reserved field")
        seen.add(location)
        slots = []
        for pos in range(start + 4, end, SLOT.size):
            species, form, gender, low, high, alpha, shiny = SLOT.unpack_from(data, pos)
            obj = dict(Species=species, Form=form, Gender=gender, LevelMin=low,
                       LevelMax=high, IsAlpha=bool(alpha),
                       Shiny=SHINY_LABELS.get(shiny, shiny))
            if alpha not in (0, 1):
                raise PKLFormatError(f"Area {location} offset {pos}: invalid Alpha byte")
            validate_slot(obj)
            slots.append(obj)
        areas.append({"Location": location, "Slots": slots})
    return areas


def write_pkl(areas):
    if type(areas) is not list or not areas:
        raise PKLFormatError("areas must be a non-empty list")
    if len(areas) > 65535:
        raise PKLFormatError("BinLinker16 area count exceeds ushort")
    count = len(areas)
    first = 4 + 2 * (count + 1)
    if first > 65535:
        raise PKLFormatError("BinLinker16 header offset exceeds ushort")
    body = bytearray()
    offsets = [first]
    seen = set()
    for i, area in enumerate(areas):
        if type(area) is not dict or set(area) != {"Location", "Slots"}:
            raise PKLFormatError(f"Area[{i}] needs exactly Location and Slots")
        location = exact_int(area["Location"], "Location", 1, 65535)
        if location in seen:
            raise PKLFormatError(f"Duplicate Location {location}")
        seen.add(location)
        slots = area["Slots"]
        if type(slots) is not list:
            raise PKLFormatError(f"Location {location}: Slots must be a list")
        body.extend(struct.pack("<HH", location, 0))
        for entry in slots:
            body.extend(SLOT.pack(*validate_slot(entry)))
        offset = first + len(body)
        if offset > 65535:
            raise PKLFormatError("BinLinker16 u16 offset overflow (>65535 bytes)")
        offsets.append(offset)
    result = MAGIC + struct.pack("<H", count)
    result += struct.pack("<" + "H" * len(offsets), *offsets) + body
    # Self-validate encoder: never publish a file our strict decoder rejects.
    read_pkl(bytes(result))
    return bytes(result)


def summary(data):
    areas = read_pkl(data)
    flat = [s for area in areas for s in area["Slots"]]
    return dict(
        sha256=sha256(data), byte_size=len(data), area_count=len(areas),
        slot_count=len(flat),
        alpha_slots=sum(x["IsAlpha"] for x in flat),
        shiny_counts={name: sum(s["Shiny"] == name for s in flat)
                      for name in ("Random", "Never", "Always")},
        location_slot_counts={str(a["Location"]):len(a["Slots"]) for a in areas},
    )


def document(data):
    return dict(
        format=FORMAT, format_version=FORMAT_VERSION,
        source_sha256=sha256(data), source_byte_size=len(data),
        areas=read_pkl(data),
    )


def validate_document(doc):
    if type(doc) is not dict or set(doc) != {
        "format", "format_version", "source_sha256", "source_byte_size", "areas"
    }:
        raise PKLFormatError("JSON must retain format/version/source SHA-256/size/areas fields")
    if doc["format"] != FORMAT or doc["format_version"] != FORMAT_VERSION:
        raise PKLFormatError("Unknown PKL JSON interchange schema/version")
    h = doc["source_sha256"]
    if type(h) is not str or not re.fullmatch(r"[a-fA-F0-9]{64}", h):
        raise PKLFormatError("JSON source_sha256 missing or invalid")
    exact_int(doc["source_byte_size"], "source_byte_size", 8, 65535)
    return doc["areas"]


def save_new(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # 'xb' prevents accidental replacement, including source and input files.
    with path.open("xb") as handle:
        handle.write(payload)


def check_original(original, doc):
    original_bytes = Path(original).read_bytes()
    if sha256(original_bytes) != doc["source_sha256"]:
        raise PKLFormatError("Original PKL SHA-256 differs from JSON source_sha256")
    if len(original_bytes) != doc["source_byte_size"]:
        raise PKLFormatError("Original PKL byte count differs from JSON source_byte_size")
    read_pkl(original_bytes)


def diff(old_data, new_data):
    older, newer = read_pkl(old_data), read_pkl(new_data)
    def counters(areas):
        return Counter((a["Location"],) + validate_slot(s) for a in areas for s in a["Slots"])
    before, after = counters(older), counters(newer)
    added = after - before
    removed = before - after
    def item(t, count):
        return dict(Location=t[0], Species=t[1], Form=t[2], Gender=t[3],
                    LevelMin=t[4], LevelMax=t[5], IsAlpha=bool(t[6]),
                    Shiny=SHINY_LABELS[t[7]], Count=count)
    return dict(
        original_sha256=sha256(old_data), modified_sha256=sha256(new_data),
        byte_identical=old_data == new_data,
        slots_added=sum(added.values()), slots_removed=sum(removed.values()),
        added=[item(k, v) for k,v in sorted(added.items())],
        removed=[item(k, v) for k,v in sorted(removed.items())],
        unchanged_slot_multiset=before == after,
        area_order_changed=[a["Location"] for a in older] !=
                           [a["Location"] for a in newer],
    )


def cli():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="Validate and print PKL header/slot summary")
    inspect.add_argument("input", type=Path)
    inspect.add_argument("--location", type=int, help="Print only location's decoded slots")
    export = sub.add_parser("export", help="Losslessly export PKL to readable/editable JSON")
    export.add_argument("input", type=Path)
    export.add_argument("--out", type=Path, required=True)
    build = sub.add_parser("import", help="Rebuild PKL from JSON (never overwrite original)")
    build.add_argument("input", type=Path)
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--source-pkl", type=Path,
                       help="Require JSON source hash/length to match this original")
    patch = sub.add_parser("patch", help="Edit one slot in a copy, index is zero-based")
    patch.add_argument("input", type=Path)
    patch.add_argument("--out", type=Path, required=True)
    patch.add_argument("--location", type=int, required=True)
    patch.add_argument("--index", type=int, required=True)
    for attr in ("species", "form", "gender", "level-min", "level-max"):
        patch.add_argument("--"+attr, type=int)
    patch.add_argument("--alpha", choices=("true", "false"))
    patch.add_argument("--shiny", choices=tuple(SHINY_CODES))
    compare = sub.add_parser("diff", help="Compare original and edited PKL slots")
    compare.add_argument("original", type=Path)
    compare.add_argument("modified", type=Path)
    compare.add_argument("--out", type=Path, help="Optional JSON diff report (new file only)")
    args = ap.parse_args()

    if args.command == "inspect":
        data = args.input.read_bytes()
        result = summary(data)
        if args.location is not None:
            found = [x for x in read_pkl(data) if x["Location"] == args.location]
            if not found:
                raise PKLFormatError(f"No location {args.location}")
            result["selected_area"] = found[0]
    elif args.command == "export":
        data = args.input.read_bytes()
        result = summary(data)
        save_new(args.out, (json.dumps(document(data), ensure_ascii=False, indent=2)
                            + "\n").encode("utf-8"))
        result["export_json"] = str(args.out)
    elif args.command == "import":
        doc = json.loads(args.input.read_text(encoding="utf-8-sig"))
        areas = validate_document(doc)
        if args.source_pkl:
            check_original(args.source_pkl, doc)
        data = write_pkl(areas)
        save_new(args.out, data)
        result = summary(data)
        result["new_file"] = str(args.out)
        result["source_hash_guard"] = "PASS" if args.source_pkl else "NOT_REQUESTED"
    elif args.command == "patch":
        old_data = args.input.read_bytes()
        areas = read_pkl(old_data)
        found = [x for x in areas if x["Location"] == args.location]
        if not found:
            raise PKLFormatError(f"Location {args.location} missing")
        slots = found[0]["Slots"]
        if args.index < 0 or args.index >= len(slots):
            raise PKLFormatError("Slot index out of bounds")
        changes = {"Species":args.species, "Form":args.form,
                   "Gender":args.gender, "LevelMin":args.level_min,
                   "LevelMax":args.level_max,
                   "IsAlpha":None if args.alpha is None else args.alpha == "true",
                   "Shiny":args.shiny}
        changes = {k:v for k,v in changes.items() if v is not None}
        if not changes:
            raise PKLFormatError("patch requires at least one --species/--shiny/... option")
        slots[args.index].update(changes)
        data = write_pkl(areas)
        save_new(args.out, data)
        result = diff(old_data, data)
        result["new_file"] = str(args.out)
    else:
        original, modified = args.original.read_bytes(), args.modified.read_bytes()
        result = diff(original, modified)
        if args.out is not None:
            save_new(args.out,
                     (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode())
            result["diff_json"] = str(args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        cli()
    except (PKLFormatError, OSError, struct.error, json.JSONDecodeError) as exc:
        raise SystemExit(f"ZA PKL error: {exc}")
