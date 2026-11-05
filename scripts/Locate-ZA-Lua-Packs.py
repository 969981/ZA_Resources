#!/usr/bin/env python3
"""Locate exact ZA v2.0.2 Lua bytecode archive records in native TRPFD indexes.

Reads the existing M1 CSV indexes. Does NOT touch private ROM files or guess
an unmatched name. An output path hit proves only TRPFD membership and pack index.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "Unpack/v2.0.2/romfs/arc/data.trpfs/_index"
DEFAULT_REPORT = INDEX / "lua_pack_locations.json"
TARGETS = {
    "dll_util": "script/lua/bin/release/dll_util/dll_util.blua",
    "event_ik": "script/lua/bin/release/event_ik/event_ik.blua",
    "main": "script/lua/bin/release/main/main.blua",
    "main_dynamic": "script/lua/bin/release/main_dynamic/main_dynamic.blua",
}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize(name):
    return name.replace("\\", "/").lstrip("/").lower()


def build(index):
    file_index = index / "file_index.tsv.gz"
    pack_index = index / "pack_index.tsv"
    desc = index / "descriptor_summary.json"
    if not all(p.is_file() for p in (file_index, pack_index, desc)):
        raise FileNotFoundError("Native M1 descriptor index is incomplete")
    meta = json.loads(desc.read_text(encoding="utf-8"))
    if int(meta.get("descriptorFiles", 0)) < 1:
        raise ValueError("Invalid native descriptor file count")
    pack_rows = {}
    with pack_index.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            pack_rows[int(row["pack_index"])] = row
    found = {name: [] for name in TARGETS}
    total_rows = 0
    with gzip.open(file_index, "rt", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            total_rows += 1
            name = normalize(row["virtual_path"])
            if not name:
                continue
            for key, target in TARGETS.items():
                if name == target or name.endswith("/" + target):
                    index_no = int(row["pack_index"])
                    if index_no not in pack_rows:
                        raise ValueError(f"File references nonexistent pack {index_no}")
                    p = pack_rows[index_no]
                    if row["pack_name"] != p["pack_name"]:
                        raise ValueError(f"TRPFD inconsistent pack name at {index_no}")
                    found[key].append({
                        "hash": row["hash"],
                        "virtual_path": row["virtual_path"],
                        "pack_index": index_no,
                        "pack_name": row["pack_name"],
                        "packed_bytes": int(p["packed_bytes"]),
                        "pack_file_count": int(p["referenced_files"]),
                        "status": "CONFIRMED_NATIVE_TRPFD_INDEX"
                    })
    if total_rows != int(meta["descriptorFiles"]):
        raise ValueError(f"TRPFD index rows {total_rows} != descriptor summary {meta['descriptorFiles']}")
    expected = {"dll_util": 12145, "event_ik": 12146, "main": 12147, "main_dynamic": 12148}
    pack_names = {
        "dll_util": "arc/scriptluabinreleasedll_utildll_util.blua.trpak",
        "event_ik": "arc/scriptluabinreleaseevent_ikevent_ik.blua.trpak",
        "main": "arc/scriptluabinreleasemainmain.blua.trpak",
        "main_dynamic": "arc/scriptluabinreleasemain_dynamicmain_dynamic.blua.trpak",
    }
    if int(meta["descriptorFiles"]) != 238546 or int(meta["packCount"]) != 13181:
        raise ValueError("Unexpected ZA v2.0.2 native descriptor counts")
    if meta.get("sourceSha256", "").upper() != "D1BEB3763DEAB33691C5930E026006278F4586DAC094F8D0EA2494ECB6F851F8":
        raise ValueError("Unexpected ZA TRPFD SHA256")
    for key in TARGETS:
        if len(found[key]) != 1:
            raise ValueError(f"Expected one native Lua path for {key}, found {len(found[key])}")
        if found[key][0]["pack_index"] != expected[key] or found[key][0]["pack_name"] != pack_names[key]:
            raise ValueError(f"Native Lua pack identity mismatch for {key}")
        if found[key][0]["pack_file_count"] != 1:
            raise ValueError(f"Unexpected multi-file Lua pack {key}")
    report = {
        "game": "Pokémon Legends Z-A v2.0.2",
        "source": "verified ZA v2.0.2 native TRPFD descriptor index (NOT extracted Lua bytecode)",
        "file_index_sha256": sha256(file_index),
        "pack_index_sha256": sha256(pack_index),
        "descriptor_summary_sha256": sha256(desc),
        "descriptor_files_scanned": total_rows,
        "pack_count": int(meta["packCount"]),
        "version": "v2.0.2",
        "target_pack_indices": [12145,12146,12147,12148],
        "target_packed_bytes": 1463128,
        "targets": {
            k: {
                "expected_path": TARGETS[k],
                "matches": found[k],
                "located": bool(found[k]),
                "unique_match": len(found[k]) == 1
            } for k in TARGETS
        },
        "all_unique": all(len(v) == 1 for v in found.values()),
        "bytecode_extracted": False,
        "source_note": "The indexed script paths require actual TRPFS extraction and Lua header verification"
    }
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--index", type=Path, default=INDEX)
    p.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    p.add_argument("--verify-only", action="store_true")
    args = p.parse_args()
    report = build(args.index.resolve())
    encoded = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if args.verify_only:
        if not args.output.is_file() or args.output.read_bytes() != encoded:
            raise SystemExit("Missing/stale native pack-location report")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
    print(json.dumps({k: {"matches":v["matches"],"located":v["located"]}
                      for k,v in report["targets"].items()}, indent=2))
    print(f"Scanned {report['descriptor_files_scanned']} native ZA indexed files, four unique Lua targets={report['all_unique']}")


if __name__ == "__main__":
    main()
