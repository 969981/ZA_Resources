#!/usr/bin/env python3
"""Inventory tracked ZA image resources without reading game asset blobs."""
import argparse
import collections
import csv
import json
import re
import subprocess
from pathlib import Path

ROOT = "Unpack/v2.0.2/romfs"
VIRTUAL = "arc/data.trpfs/virtual/"
PART = re.compile(r"\.7z\.(\d+)$", re.I)
FORMATS = {".bntx", ".arc", ".dds", ".png", ".jpg", ".jpeg", ".tga",
           ".ktx", ".ktx2", ".webp", ".bmp", ".bflim", ".bffnt", ".bfotf",
           ".bfcpx", ".bflan", ".bflyt", ".truiv",
           ".trmdl", ".trmmt", ".trmsh", ".trmtr", ".trmbf", ".trskl"}

def git(*args):
    return subprocess.check_output(["git", *args])

def category(path):
    if path.startswith("ui/tex/"):
        return "ui/tex/" + path.split("/")[2]
    if path.startswith("ui/data/"):
        return "ui/data"
    if path.startswith("ik_pokemon/data/") and "/icon/" in path:
        return "pokemon_icon"
    if path.startswith("ik_pokemon/"):
        return "pokemon_other"
    if path.startswith("ik_chara/"):
        return "character"
    return path.split("/", 1)[0]

def inventory(data):
    grouped = collections.defaultdict(list)
    for entry in data.split(b"\0"):
        if not entry:
            continue
        meta, rawpath = entry.split(b"\t", 1)
        mode, kind, oid, size = meta.decode("ascii").split()
        if kind != "blob":
            continue
        path = rawpath.decode("utf-8", "surrogateescape")
        prefix = ROOT + "/"
        if not path.startswith(prefix):
            continue
        relative = path[len(prefix):]
        if relative.startswith("arc/data.trpfs/virtual_converted/") or "/_index/" in relative or relative.startswith("_index/"):
            continue
        layer = "virtual" if relative.startswith(VIRTUAL) else "romfs_other"
        logical = relative[len(VIRTUAL):] if layer == "virtual" else relative
        part = PART.search(logical)
        original = logical[:part.start()] if part else logical
        extension = Path(original).suffix.lower()
        if extension not in FORMATS:
            continue
        grouped[(layer, original)].append((path, oid, int(size), int(part.group(1)) if part else None))
    rows = []
    for (layer, original), entries in sorted(grouped.items()):
        entries.sort(key=lambda e: (e[3] or 0, e[0]))
        parts = [e[3] for e in entries if e[3] is not None]
        raw = [e for e in entries if e[3] is None]
        state = "RAW" if len(raw) == 1 and not parts else "ARCHIVE_PARTS"
        if parts and (raw or parts != list(range(1, max(parts) + 1))):
            state = "AMBIGUOUS_OR_GAPPED"
        rows.append(dict(layer=layer, path=original, category=category(original),
                         extension=Path(original).suffix.lower(), representation=state,
                         git_blob_sha=raw[0][1] if state == "RAW" else "",
                         stored_bytes=sum(e[2] for e in entries),
                         stored_paths=[e[0] for e in entries],
                         stored_blob_shas=[e[1] for e in entries],
                         mapping_status="UNKNOWN"))
    return rows

def summarize(rows):
    groups = collections.defaultdict(list)
    for row in rows:
        groups[(row["layer"], row["category"], row["extension"])].append(row)
    return [dict(layer=k[0], category=k[1], extension=k[2], logical_paths=len(v),
                 raw_paths=sum(r["representation"] == "RAW" for r in v),
                 distinct_raw_git_blobs=len({r["git_blob_sha"] for r in v if r["git_blob_sha"]}),
                 archive_or_ambiguous_paths=sum(r["representation"] != "RAW" for r in v),
                 stored_bytes=sum(r["stored_bytes"] for r in v))
            for k, v in sorted(groups.items())]

def self_test():
    def entry(path, oid="a"*40, size=10):
        return ("100644 blob %s %s\t%s/%s\0" % (oid, size, ROOT, path)).encode()
    d = entry(VIRTUAL+"ui/tex/icon_item/item_0001.bntx")
    d += entry(VIRTUAL+"ui/tex/icon_item/item_0002.bntx")
    d += entry(VIRTUAL+"ik_pokemon/data/pm0001/pm0001_00_00/icon/test.bntx")
    d += entry(VIRTUAL+"ui/data/box/a.arc.7z.001") + entry(VIRTUAL+"ui/data/box/a.arc.7z.002")
    d += entry(VIRTUAL+"ui/data/box/b.arc.7z.002")
    d += entry("arc/data.trpfs/virtual_converted/x.png")
    rows = inventory(d)
    assert len(rows) == 5
    assert sum(r["category"] == "pokemon_icon" for r in rows) == 1
    assert any(r["representation"] == "AMBIGUOUS_OR_GAPPED" for r in rows)
    item = next(r for r in summarize(rows) if r["category"] == "ui/tex/icon_item")
    assert item["logical_paths"] == 2 and item["distinct_raw_git_blobs"] == 1
    assert next(r for r in rows if r["path"].endswith("a.arc"))["stored_bytes"] == 20
    print("synthetic inventory tests passed")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ref", default="HEAD")
    p.add_argument("--out", type=Path, default=Path(".za-work/image-audit"))
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return
    ref = git("rev-parse", args.ref+"^{commit}").decode().strip()
    rows = inventory(git("ls-tree", "-rlz", ref, "--", ROOT))
    if not rows:
        raise SystemExit("No resources found; check source ref")
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out/"inventory.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=True)+"\n")
    summary = summarize(rows)
    with (args.out/"summary.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    candidates = [r for r in rows if r["category"] == "pokemon_icon" or r["category"] in {"ui/tex/icon_item", "ui/tex/icon_donut"}]
    with (args.out/"mapping-candidates.jsonl").open("w", encoding="utf-8") as f:
        for row in candidates:
            f.write(json.dumps(row, ensure_ascii=True)+"\n")
    info = dict(source_commit=ref, scope=ROOT, logical_paths=len(rows),
                pokemon_icon_bntx=sum(r["category"]=="pokemon_icon" and r["extension"]==".bntx" for r in rows),
                full_tree_inventory=True, descriptor_reconciled=False,
                archive_members_scanned=False, bntx_headers_parsed=False,
                pixels_decoded=False, id_mappings_confirmed=False,
                note="Git path and blob metadata only; extension-based candidates, not verified formats or decoded images.")
    (args.out/"audit.json").write_text(json.dumps(info, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(info, indent=2))

if __name__ == "__main__":
    main()
