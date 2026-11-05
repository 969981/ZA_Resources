#!/usr/bin/env python3
"""Build gftool-compatible GFPAKHashCache.bin from pinned PokeDocs hash lists.

Binary layout matches GFTool.Core/Cache/GFPakHashCache.cs:
uint64_le count, then repeated uint64_le hash + .NET BinaryWriter UTF-8 string.
No ROM, Oodle DLL, or network request is needed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

HASH_RE = re.compile(r"^(?:0[xX])?([0-9a-fA-F]{1,16})$")


def read_hashlists(files):
    mapping = {}
    stats = {"lines": 0, "invalid": 0, "duplicates": 0, "conflicts": 0}
    for file in files:
        with Path(file).open("r", encoding="utf-8-sig", errors="strict") as handle:
            for line in handle:
                stats["lines"] += 1
                text = line.strip()
                if not text or text.startswith("#"):
                    continue
                pieces = text.split()
                if len(pieces) < 2:
                    stats["invalid"] += 1
                    continue
                match = HASH_RE.fullmatch(pieces[0])
                if not match:
                    stats["invalid"] += 1
                    continue
                h = int(match.group(1), 16)
                name = pieces[1]
                if h in mapping:
                    if mapping[h] == name:
                        stats["duplicates"] += 1
                    else:
                        stats["conflicts"] += 1
                    continue  # Deterministic, first-list-wins.
                mapping[h] = name
    return mapping, stats


def write_7bit_int(f, length):
    while length >= 0x80:
        f.write(bytes(((length & 0x7f) | 0x80,)))
        length >>= 7
    f.write(bytes((length,)))


def create_cache(output, mapping):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(output.name + ".za-writing")
    with tmp.open("wb") as f:
        f.write(struct.pack("<Q", len(mapping)))
        for key, name in sorted(mapping.items()):
            f.write(struct.pack("<Q", key))
            string_data = name.encode("utf-8")
            write_7bit_int(f, len(string_data))
            f.write(string_data)
    tmp.replace(output)
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hashlist", action="append", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    if args.output.exists() and not args.overwrite:
        ap.error("Output already exists. Use --overwrite explicitly.")
    for f in args.hashlist:
        if not f.is_file():
            ap.error(f"Missing hashlist: {f}")
    m, stats = read_hashlists(args.hashlist)
    if not m:
        ap.error("No hash rows parsed from supplied lists.")
    result = create_cache(args.output, m)
    digest = hashlib.sha256(result.read_bytes()).hexdigest()
    report = {"entries": len(m), "stats": stats, "inputs": [str(p) for p in args.hashlist],
              "output": str(result), "size": result.stat().st_size, "sha256": digest}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
