#!/usr/bin/env python3
"""Decode ZA v2.0.2 personal learnsets and Simplified Chinese game message tables.

All values originate from the user's ROM resources; no third-party name lists.
Personal field 0: two u16 (species, form); field 1: present flag;
field 25: vector of 4-byte structs (u16 move, u8 learn, u8 unlock).
Source schema inference corroborated by https://decryptu.github.io/pokeldn/za.html.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import json
import re
import struct
from pathlib import Path

VIRTUAL = Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual")
OUT = Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/_tables")
FIELDS = (
    ("monsname", "names/ZA_species_names_zh.csv"),
    ("wazaname", "names/ZA_move_names_zh.csv"),
    ("itemname", "names/ZA_item_names_zh.csv"),
    ("place_name", "names/ZA_place_names_zh.csv"),
    ("zukan_comment_A", "pokedex/ZA_pokedex_comment_A_zh.csv"),
    ("zukan_comment_B", "pokedex/ZA_pokedex_comment_B_zh.csv"),
    ("wazainfo", "battle/ZA_move_descriptions_zh.csv"),
)
NAME_PATTERNS = {
    "monsname": re.compile(r"^MONSNAME_(\d+)$"),
    "wazaname": re.compile(r"^WAZANAME_(\d+)$"),
    "itemname": re.compile(r"^ITEMNAME_(\d+)$"),
}
REMAP = {0xE07F: "\u202f", 0xE08D: "\u2026",
         0xE08E: "\u2642", 0xE08F: "\u2640"}


def check(data: bytes, offset: int, width: int) -> None:
    if offset < 0 or width < 0 or offset + width > len(data):
        raise ValueError(f"out-of-range access: {offset}+{width} / {len(data)}")


def u8(d, p):
    check(d, p, 1)
    return d[p]


def u16(d, p):
    check(d, p, 2)
    return struct.unpack_from("<H", d, p)[0]


def u32(d, p):
    check(d, p, 4)
    return struct.unpack_from("<I", d, p)[0]


def i32(d, p):
    check(d, p, 4)
    return struct.unpack_from("<i", d, p)[0]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_csv(path: Path, headers, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def parse_tbl(data: bytes):
    if data[:4] != b"AHTB":
        raise ValueError("invalid text label magic")
    count = u32(data, 4)
    if count < 1 or count > 100000:
        raise ValueError("invalid .tbl label count")
    pos = 8
    labels = []
    for _ in range(count):
        check(data, pos, 10)
        h = struct.unpack_from("<Q", data, pos)[0]
        length = u16(data, pos + 8)
        pos += 10
        check(data, pos, length)
        labels.append((data[pos:pos+length].rstrip(b"\x00").decode("cp1252"),
                       f"{h:016x}"))
        pos += length
    if pos != len(data):
        raise ValueError("trailing bytes in .tbl")
    return labels


def parse_text_chars(values):
    out = []
    i = 0
    while i < len(values):
        c = values[i]
        i += 1
        if c == 0:
            break
        if c == 0x10:
            if i + 1 >= len(values):
                out.append("[TRUNCATED_VAR]")
                break
            count, kind = values[i:i+2]
            i += 2
            argn = max(0, count - 1)
            if kind == 0xBE00:
                out.append("\\r")
            elif kind == 0xBE01:
                out.append("\\c")
            elif kind == 0xFF01:
                # Retain opaque Ruby control parameters without assuming a stable layout.
                out.append("[RUBY]")
                if i + 2 <= len(values):
                    n, m = values[i:i+2]
                    i += 2 + n + m + n
            else:
                args = values[i:i+argn]
                i += argn
                out.append("[VAR:%04X:%s]" % (kind, ",".join("%04X" % a for a in args)))
            continue
        if c == 0x0A:
            out.append("\\n")
        elif c in REMAP:
            out.append(REMAP[c])
        elif c < 0x20:
            out.append(f"[CTRL:{c:04X}]")
        else:
            out.append(chr(c))
    return "".join(out)


def parse_dat(data: bytes):
    if len(data) < 20 or u16(data, 0) != 1 or u32(data, 8) != 0:
        raise ValueError("invalid message .dat section header")
    count = u16(data, 2)
    total = u32(data, 4)
    offset = u32(data, 12)
    if offset + total != len(data) or u32(data, offset) != total:
        raise ValueError("invalid section length or data boundary")
    if count > 50000:
        raise ValueError("absurd text count")
    check(data, offset + 4, count * 8)
    text = []
    for index in range(count):
        rec = offset + 4 + index * 8
        pos = offset + i32(data, rec)
        unit_count = u16(data, rec + 4)
        check(data, pos, unit_count * 2)
        key = (0x7C89 + 0x2983 * index) & 0xFFFF
        values = []
        for j in range(unit_count):
            values.append(u16(data, pos + 2 * j) ^ key)
            key = ((key << 3) | (key >> 13)) & 0xFFFF
        text.append(parse_text_chars(values))
    return text


def parse_personal(data: bytes):
    root = u32(data, 0)
    vt = root - i32(data, root)
    if u16(data, vt) < 6:
        raise ValueError("bad personal root vtable")
    root_vec_field = root + u16(data, vt + 4)
    vec = root_vec_field + u32(data, root_vec_field)
    count = u32(data, vec)
    if count != 1445:
        raise ValueError(f"Unexpected ZA 2.0.2 personal entries: {count}")
    check(data, vec + 4, count * 4)
    personal = []
    learnsets = []
    keys = set()
    for i in range(count):
        ptr = vec + 4 + 4 * i
        tab = ptr + u32(data, ptr)
        vtable = tab - i32(data, tab)
        vsize = u16(data, vtable)
        osize = u16(data, vtable + 2)
        if vsize < 6 or vsize > 256 or osize > 512:
            raise ValueError(f"invalid personal entry vtable at {i}")
        check(data, tab, osize)
        def field(f):
            offset = 4 + f * 2
            return (tab + u16(data, vtable + offset)
                    if offset + 2 <= vsize and u16(data, vtable + offset)
                    else None)
        a0 = field(0)
        if a0 is None:
            raise ValueError(f"missing species/form at personal row {i}")
        species, form = u16(data, a0), u16(data, a0 + 2)
        if (species, form) in keys:
            raise ValueError(f"duplicate species/form: {species},{form}")
        keys.add((species, form))
        a1 = field(1)
        present = u8(data, a1) if a1 is not None else 0
        a25 = field(25)
        entries = 0
        if a25 is not None:
            items = a25 + u32(data, a25)
            entries = u32(data, items)
            if entries > 1000:
                raise ValueError("suspicious move vector length")
            check(data, items + 4, entries * 4)
            for j in range(entries):
                p = items + 4 + j * 4
                move, level, unlock = u16(data, p), u8(data, p + 2), u8(data, p + 3)
                if not 0 < move <= 920:
                    raise ValueError(f"Invalid move ID {move} at {species}/{form}")
                category = ("special_253" if level == 253 else
                            "special_254" if level == 254 else
                            "regular_level")
                learnsets.append((species, form, present, j, move, level, unlock, category))
        personal.append((i, species, form, present, entries))
    if len(learnsets) != 20234 or sum(r[3] == 1 for r in personal) != 594:
        raise ValueError("personal data differs from verified 2.0.2 counts")
    return personal, learnsets


def export(repo: Path, output: Path):
    langroot = repo / VIRTUAL / "ik_message/dat/Simp_Chinese/common"
    manifest = {"version": "ZA 2.0.2", "language": "Simp_Chinese", "inputs": {},
                "notes": ["Message ID mapping validated from .tbl label order.",
                          "Form learnsets from personal field 25; 253/254 are special codes.",
                          "Only present flag 1 means personal entry present in current game."]}
    decoded = {}
    for table, target in FIELDS:
        datpath = langroot / (table + ".dat")
        tblpath = langroot / (table + ".tbl")
        raw_dat, raw_tbl = datpath.read_bytes(), tblpath.read_bytes()
        names, values = parse_tbl(raw_tbl), parse_dat(raw_dat)
        if len(names) != len(values) + 1 or not names[-1][0].endswith("_max"):
            raise ValueError(f"message label/value count mismatch in {table}")
        rows = []
        for i, (value, (name, labelhash)) in enumerate(zip(values, names)):
            m = NAME_PATTERNS[table].fullmatch(name) if table in NAME_PATTERNS else None
            numeric = int(m.group(1)) if m else ""
            if m and numeric != i:
                raise ValueError(f"non-indexed label in {table} at {i}: {name}")
            rows.append((numeric, name, value, i, labelhash))
        decoded[table] = rows
        write_csv(output / target, ["id", "label", "zhNameOrText", "lineIndex", "labelHash64"], rows)
        manifest["inputs"][table] = {
            "count": len(rows), "labelCount": len(names),
            "sourceDat": str(datpath.relative_to(repo)), "datSha256": sha(raw_dat),
            "sourceTbl": str(tblpath.relative_to(repo)), "tblSha256": sha(raw_tbl),
            "extraMaxLabel": names[-1][0],
        }
    if len(decoded["monsname"]) != 1026 or len(decoded["wazaname"]) != 921 or len(decoded["itemname"]) != 2685:
        raise ValueError("unexpected Chinese name table sizes")
    species = {int(v[0]): v[2] for v in decoded["monsname"] if v[0] != ""}
    moves = {int(v[0]): v[2] for v in decoded["wazaname"] if v[0] != ""}
    # Lock an unmistakable, direct alignment from the user's game binaries.
    if species.get(1) != "妙蛙种子" or species.get(3) != "妙蛙花" or moves.get(1) != "拍击":
        raise ValueError("Chinese message IDs do not match validated ROM baseline")
    raw = (repo / VIRTUAL / "avalon/data/personal_array.bin").read_bytes()
    personal, learnsets = parse_personal(raw)
    write_csv(output / "pokedex/ZA_personal_species_forms.csv",
              ["recordIndex", "speciesId", "formNo", "presentFlag", "learnsetEntries"],
              personal)
    joined = [(s, species.get(s, ""), f, present, idx, mid, moves.get(mid, ""),
               learn, unlock, category) for s, f, present, idx, mid, learn, unlock, category in learnsets]
    write_csv(output / "battle/ZA_levelup_learnsets_zh.csv",
              ["speciesId", "speciesZh", "formNo", "personalPresent", "entryIndex",
               "moveId", "moveZh", "learnLevelRaw", "unlockLevelRaw", "learnCategory"],
              joined)
    manifest["inputs"]["personal_array"] = {
        "source": str((repo / VIRTUAL / "avalon/data/personal_array.bin").relative_to(repo)),
        "sha256": sha(raw), "totalBytes": len(raw), "rows": len(personal),
        "presentForms": sum(row[3] == 1 for row in personal),
        "distinctPresentSpecies": len({r[1] for r in personal if r[3]}),
        "learnsetEntries": len(learnsets),
    }
    manifest["outputs"] = {"speciesTranslated": len(species), "moveTranslated": len(moves),
                           "levelupMoves": len(joined),
                           "learnLevel253": sum(x[7] == 253 for x in joined),
                           "learnLevel254": sum(x[7] == 254 for x in joined)}
    out = output / "_audit/ZA_core_dex_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "SUCCESS", "personalRows": len(personal),
                      "presentForms": manifest["inputs"]["personal_array"]["presentForms"],
                      "learnsetRows": len(joined), "nameCount": len(species),
                      "moveNameCount": len(moves), "placeNames": len(decoded["place_name"]),
                      "commentsA": len(decoded["zukan_comment_A"]),
                      "commentsB": len(decoded["zukan_comment_B"])}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    repo = args.repo.resolve()
    out = args.out if args.out.is_absolute() else repo / args.out
    export(repo, out.resolve())


if __name__ == "__main__":
    main()
