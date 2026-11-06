#!/usr/bin/env python3
"""Read-only Z-A trade-related native ELF string and AArch64 xref triage.

This deliberately reports candidate strings and address references only, NOT
proven Link Trade function entrypoints, held-item predicates, or bypasses.
Relies on the repository's verified ELF parser and disassembler-lite.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/Probe-ZA-Lua-Host-ELF.py"
spec = importlib.util.spec_from_file_location("za_host_elf", HELPER)
assert spec and spec.loader
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)

TERMS = re.compile(
    rb"(?i)(?:LinkTrade|NetTrade|PokemonTrade|PokeTrade|Trading|"
    rb"Trade|Exchang(?:e|ing)|HeldItem|HoldItem|ItemHold|"
    rb"TradeCheck|TradeError|LinkPlay|LinkCommunication)"
)


def run(repo: Path, out: Path) -> dict:
    manifest = json.loads((repo / "Unpack/v2.0.2/exefs/exefs-manifest.json").read_text("utf-8"))
    item = manifest["modules"]["main"]
    path = repo / "Unpack/v2.0.2/exefs/main/main.elf"
    binary = path.read_bytes()
    sha = hashlib.sha256(binary).hexdigest()
    if len(binary) != item["elfSize"] or sha != item["elfSha256"]:
        raise ValueError("main.elf does not match verified v2.0.2 manifest")
    elf = host.ELF64(binary)
    host.TERMS = TERMS
    hits, total, truncated = host.scan_strings(elf, "main", limit=3000)
    xrefs = host.scan_adr_xrefs(elf, "main", hits, limit=3000)
    symbols = elf.symbols()
    summary = {
        "source": str(path.relative_to(repo)),
        "sourceSha256": sha,
        "sourceBytes": len(binary),
        "matchedStrings": total,
        "stringsTruncated": truncated,
        "scannedStringRows": len(hits),
        "exactInstructionReferences": len(xrefs),
        "matchedSymbols": len(symbols),
        "interpretation": "CANDIDATE ONLY - static ASCII names and ADR/ADRP+ADD, not trade validation proof",
        "caution": "No runtime comparison was performed. An unmatched function may be stripped or indirect.",
    }
    out.mkdir(parents=True, exist_ok=True)
    with (out / "trade-string-candidates.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(host.HIT_COLS)
        w.writerows(hits)
    with (out / "trade-adr-xrefs.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(host.XREF_COLS)
        w.writerows(xrefs)
    (out / "trade-probe-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("TOP MATCHED STRINGS:")
    for row in hits[:60]:
        print(" | ".join((row[4],row[2],row[6][:110])))
    print("TOP EXACT STRING XREFS:")
    for row in xrefs[:60]:
        print(" | ".join((row[3],row[1],row[5],row[2][:100])))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=Path(".za-work/trade-native"))
    args = parser.parse_args()
    run(args.repo.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
