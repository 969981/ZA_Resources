#!/usr/bin/env python3
"""Audit Z-A v2.0.2 Trinity Lua-pack completeness and unresolved S gaps.

A missing token in four verified native Lua constant pools is not necessarily
unused at runtime, nor evidence of an original identifier. No ROM bytes copied.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"Unpack/v2.0.2/romfs/arc/data.trpfs"
NATIVE=BASE/"_index/lua-native"
PACKS=BASE/"_index/pack_index.tsv"
CONSTANTS=NATIVE/"native-unknown-constants.tsv"
HASHES=ROOT/"tools/PokeDocs-Supplement/ZA/Hashlists/Lua/unresolved-symbol-index.tsv"
CROSSWALK=NATIVE/"native-haxe-crosswalk.tsv"
SUMMARY=NATIVE/"native-lua-summary.json"


def read_tsv(p):
    with p.open("r",encoding="utf-8-sig",newline="") as stream:
        return list(csv.DictReader(stream,delimiter="\t"))


def coverage(pack_rows, unresolved, constants):
    packs=[p for p in pack_rows if p["pack_name"].lower().endswith(".blua.trpak")]
    targets={x["kind"].upper()+x["hash"][2:].upper():x for x in unresolved}
    present={r["hash_token"].upper() for r in constants}
    absent=sorted(targets.keys()-present)
    if set(present)-set(targets):
        raise ValueError("Native constants contain untracked unresolved targets")
    return packs, targets, present, absent


def run(packs_path=PACKS, unresolved_path=HASHES, constants_path=CONSTANTS,
        native_summary=SUMMARY, haxe_crosswalk=CROSSWALK, out=NATIVE):
    packs=read_tsv(packs_path)
    unresolved=read_tsv(unresolved_path)
    constants=read_tsv(constants_path)
    baseline=json.loads(native_summary.read_text(encoding="utf-8"))
    if (baseline.get("version")!="v2.0.2" or baseline.get("native_files_parsed")!=4 or
        len(packs)!=13181 or len(unresolved)!=162 or len(constants)!=1365):
        raise ValueError("Pinned ZA Trinity and Lua input corpus mismatch")
    lua_packs,targets,present,missing=coverage(packs,unresolved,constants)
    names=[p["pack_name"] for p in lua_packs]
    if (len(lua_packs)!=4 or
        [int(p["pack_index"]) for p in lua_packs] != [12145,12146,12147,12148] or
        Counter(r["kind"].upper() for r in unresolved)!=Counter({"S":116,"F":43,"E":3})):
        raise ValueError("Unexpected original ZA native Lua package coverage")
    cross={r["kind"].upper()+r["hash"][2:].upper():r for r in read_tsv(haxe_crosswalk)}
    gaps=[]
    for token in missing:
        row=targets[token]
        ref=cross.get(token,{})
        gaps.append({"hash_token":token,"kind":row["kind"],"original_line":row["original_line"],
                     "haxe_first_path":ref.get("haxe_first_path",""),
                     "haxe_first_line":ref.get("haxe_first_line",""),
                     "evidence":"NOT_IN_FOUR_VERIFIED_NATIVE_CONSTANT_POOLS"})
    if len(missing)!=5 or any(not x.startswith("S") for x in missing):
        raise ValueError("Native unresolved token absence changed; require manual scope audit")
    result={"version":"v2.0.2","trinity_total_packs_indexed":len(packs),
            "indexed_blua_packs":len(lua_packs),
            "indexed_blua_entries": [{"pack_index":int(p["pack_index"]),
                                       "pack_name":p["pack_name"]} for p in lua_packs],
            "targets_total":len(targets), "target_tokens_present_in_native_constants":len(present),
            "target_tokens_absent_in_native_constants":len(missing),
            "absent_tokens":gaps,
            "input_pack_index_sha256":hashlib.sha256(packs_path.read_bytes()).hexdigest(),
            "input_native_constants_sha256":hashlib.sha256(constants_path.read_bytes()).hexdigest(),
            "original_names_recovered":0,
            "warning":"Only four .blua.trpak packs exist in this version's published complete Trinity pack index. Five S tokens are absent in their verified native Lua constant pools. This does NOT prove absent in other encodings, binaries, resource versions, or actual runtime. Haxe paths are unverified external hints."}
    out.mkdir(parents=True,exist_ok=True)
    (out/"native-lua-pack-coverage.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack-index",type=Path,default=PACKS)
    p.add_argument("--unknown-index",type=Path,default=HASHES)
    p.add_argument("--constants",type=Path,default=CONSTANTS)
    p.add_argument("--native-summary",type=Path,default=SUMMARY)
    p.add_argument("--haxe-crosswalk",type=Path,default=CROSSWALK)
    p.add_argument("--out",type=Path,default=NATIVE)
    a=p.parse_args()
    print(json.dumps(run(a.pack_index,a.unknown_index,a.constants,
                         a.native_summary,a.haxe_crosswalk,a.out),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
