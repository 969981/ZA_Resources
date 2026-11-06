#!/usr/bin/env python3
"""Z-A 2.0.2: exact static AArch64 direct BL/B callsite provenance for Pokémon PKM setters.

Does not claim a function is a generator because it calls a setter. Does NOT assign
runtime-verified main+offset or claim Rare/PID shiny semantics.
No third-party dependencies. Requires SHA-pinned game main.elf (not committed here).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ELF = ROOT / "Unpack/v2.0.2/exefs/main/main.elf"
MANIFEST = ROOT / "Unpack/v2.0.2/exefs/exefs-manifest.json"
OUT = ROOT / "docs/research/v2.0.2/za-pid-accessor-callsite-xrefs.json"
# Independently reported by decryptu.github.io/pokeldn/za.html for v2.0.2.
# Actual instruction targets verified against sha-pinned ELF below.
KNOWN = {
    "pid_get": 0xE4DBE0,
    "pid_set": 0xE57350,
    "species_get": 0xE49940,
    "species_set": 0xE52AA0,
    "tid_sid_get": 0xE49D50,
    "tid_sid_set": 0xE52EE0,
    "experience_set": 0xE53100,
    "nature_set": 0xE56690,
    "form_set": 0xE56470,
    "ability_set": 0xE535B0,
}
WRITERS = {"pid_set", "species_set", "tid_sid_set", "experience_set",
           "nature_set", "form_set", "ability_set"}
KEYS = {"pid_set", "species_set", "tid_sid_set", "experience_set"}

def sign(v,bits):
    return v-(1<<bits) if v&(1<<(bits-1)) else v

def branch_target(word, pc):
    op=word & 0xFC000000
    if op == 0x94000000: kind="BL"
    elif op == 0x14000000: kind="B"
    else: return None
    return kind, pc+(sign(word & 0x03FFFFFF,26)<<2)

def load_segments(raw):
    if len(raw)<64 or raw[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H",raw,18)[0]!=183:
        raise ValueError("AArch64 little-endian ELF required")
    phoff=struct.unpack_from("<Q",raw,32)[0]
    ent,num=struct.unpack_from("<HH",raw,54)
    if ent<56 or num>200 or phoff+ent*num>len(raw):raise ValueError("invalid ELF PHDR")
    out=[]
    for i in range(num):
        kind,flags,offset,va,_,filesz,_,_=struct.unpack_from("<IIQQQQQQ",raw,phoff+i*ent)
        if kind == 1 and filesz:
            if offset+filesz>len(raw):raise ValueError("ELF segment bounds invalid")
            out.append({"offset":offset,"va":va,"size":filesz,"flags":flags})
    return out

def scan_direct(raw,segs, targets):
    inverted={a:n for n,a in targets.items()}
    entries=[]
    for seg in segs:
        if not (seg["flags"] & 1): continue
        for o in range(0,seg["size"]-3,4):
            w=struct.unpack_from("<I",raw,seg["offset"]+o)[0]
            # Check opcode before decoding target.
            if w & 0xFC000000 not in (0x94000000,0x14000000): continue
            pc=seg["va"]+o
            kind,dest=branch_target(w,pc)
            if dest not in inverted:continue
            entries.append({"caller_pc":pc, "file_offset":seg["offset"]+o,
                            "opcode":kind,"word":w,"target_pc":dest,
                            "target_kind":inverted[dest]})
    entries.sort(key=lambda x:x["caller_pc"])
    return entries

def windows(entries,span=0x800,limit=60):
    # Sliding window over direct callsites; overlaps are reduced by unique target sets.
    groups=[]
    for i,first in enumerate(entries):
        if first["target_kind"] not in WRITERS:continue
        group=[]
        for row in entries[i:]:
            if row["caller_pc"]-first["caller_pc"]>span:break
            group.append(row)
        names={x["target_kind"] for x in group}
        if "pid_set" not in names and len(names & KEYS)<3:continue
        weighted=(25 if "pid_set" in names else 0)+(15 if "species_set" in names else 0)+\
            (12 if "tid_sid_set" in names else 0)+(10 if "experience_set" in names else 0)+\
            3*len(names & WRITERS)+min(len(group),12)
        groups.append({"range_start":first["caller_pc"],"range_end":group[-1]["caller_pc"],
                       "score":weighted,"target_kinds":sorted(names),
                       "calls":[{"caller_pc":f"0x{x['caller_pc']:X}",
                                 "target_kind":x["target_kind"],
                                 "target_pc":f"0x{x['target_pc']:X}",
                                 "op":x["opcode"],"instruction":f"0x{x['word']:08X}"}
                                for x in group]})
    groups.sort(key=lambda z:(-z["score"],z["range_start"]))
    unique=[]
    for group in groups:
        # Do not count repeated sliding windows in the same callsite cluster as independent funcs.
        if any(abs(group["range_start"]-x["range_start"])<=span//2
               and set(group["target_kinds"])==set(x["target_kinds"]) for x in unique):
            continue
        unique.append(group)
        if len(unique)>=limit:break
    for g in unique:
        g["range_start"]=f"0x{g['range_start']:X}"
        g["range_end"]=f"0x{g['range_end']:X}"
    return unique

def run(raw,expected,span,limit):
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=expected:raise ValueError(f"SHA256 mismatch: expected {expected}, got {digest}")
    segments=load_segments(raw)
    sites=scan_direct(raw,segments,KNOWN)
    counts=Counter(x["target_kind"] for x in sites)
    return {
        "source_sha256":digest,
        "source":"v2.0.2 main.elf",
        "evidence":"STATIC_DIRECT_BRANCH_PROVENANCE_ONLY",
        "external_address_reference":"https://decryptu.github.io/pokeldn/za.html",
        "known_accessors":[{"label":k,"target_elf_va":f"0x{v:X}"} for k,v in KNOWN.items()],
        "direct_refs": [{**{k:v for k,v in x.items() if k!="word"},
                          "caller_pc":f"0x{x['caller_pc']:X}",
                          "file_offset":f"0x{x['file_offset']:X}",
                          "instruction":f"0x{x['word']:08X}",
                          "target_pc":f"0x{x['target_pc']:X}"} for x in sites],
        "direct_ref_counts":dict(counts),
        "ranked_callsite_windows":windows(sites,span,limit),
        "limitations":[
            "Static BL/B targets only; indirect BLR, vtables and wrappers not followed",
            "Windows group proximity only and do NOT identify function boundaries",
            "An accessor call does NOT prove shiny logic or actual runtime execution",
            "ELF VA is not yet verified runtime main+offset; no GDB trace was performed",
        ],
        "verified_runtime_shiny_branch":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--elf",type=Path,default=ELF)
    p.add_argument("--manifest",type=Path,default=MANIFEST)
    p.add_argument("--output",type=Path,default=OUT)
    p.add_argument("--span",type=lambda x:int(x,0),default=0x800)
    p.add_argument("--limit",type=int,default=60)
    args=p.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    expected=manifest["modules"]["main"]["elfSha256"]
    report=run(args.elf.read_bytes(),expected,args.span,args.limit)
    report["build_id_manifest"]=manifest["modules"]["main"]["buildIdHex"]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"sha256":report["source_sha256"],
                     "direct_ref_counts":report["direct_ref_counts"],
                     "ranked_windows":len(report["ranked_callsite_windows"]),
                     "top":report["ranked_callsite_windows"][:5],
                     "runtime_verified":False},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
