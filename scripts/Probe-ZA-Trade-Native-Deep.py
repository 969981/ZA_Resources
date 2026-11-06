#!/usr/bin/env python3
"""ZA v2.0.2: deeper *static-only* AArch64 trade-name reference triage.

Extends Probe-ZA-Trade-ELF.py. Reads only SHA-pinned main.elf; never changes
game files. Reports exact references, ELF RELA addends, pointer cells and
nearby ARM64 instructions. No address is a proven held-item trade restriction.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts/Probe-ZA-Lua-Host-ELF.py"
spec = importlib.util.spec_from_file_location("za_native_host", PROBE)
assert spec and spec.loader
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)

TERMS = re.compile(
    rb"(?i)(?:LinkTrade|NetTrade|PokemonTrade|PokeTrade|Trading|"
    rb"Trade|Exchang(?:e|ing)|HeldItem|HoldItem|ItemHold|"
    rb"TradeCheck|TradeError|LinkPlay|LinkCommunication)"
)
KW = ("TradeMatchingPage", "TradeMatchingControlView", "TradeMatchingTextView",
      "WaitReadyToTradeCoroutine", "BoxExchange", "CommandConfirmTrade",
      "CommandCancelTrade", "holdItem", "net_trade", "/trade_offer", "/trade_reset",
      "PartnerExchange", "SyncSaveClient", "net_topmenu_trade")

def rows_to_file(path, headers, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(headers)
        w.writerows(rows)

def chunks(raw, key):
    at = 0
    while True:
        at = raw.find(key, at)
        if at < 0:
            return
        yield at
        at += 1

def scan_addrs(elf, mapping, cap=20000):
    """Locate exact pointers and RELA addends for selected string virtual addresses."""
    lookups = defaultdict(list)
    sections = [s for s in elf.sections if s["stype"] in (1, 3) and
                s["flags"] & 2 and not s["flags"] & 4 and s["size"]]
    for target, label in mapping.items():
        pattern = struct.pack("<Q", target)
        for s in sections:
            data = elf.raw[s["off"]:s["off"] + s["size"]]
            for relative in chunks(data, pattern):
                off = s["off"] + relative
                va, region = elf.location(off)
                lookups[target].append(("EXACT_DATA_U64_POINTER", label, target,
                                       va, off, region, ""))
                if sum(len(v) for v in lookups.values()) > cap:
                    raise ValueError("too many pointer hits")
    for s in elf.sections:
        if s["stype"] != 4 or s["entsize"] < 24:
            continue
        n = s["size"] // s["entsize"]
        if n > 8_000_000:
            raise ValueError("suspicious rela count")
        for i in range(n):
            p = s["off"] + i * s["entsize"]
            offset, info, addend = struct.unpack_from("<QQq", elf.raw, p)
            if addend not in mapping:
                continue
            lookups[addend].append(("ELF_RELA_ADDEND", mapping[addend], addend,
                                   offset, p, s["name"], f"reloc_type={info & 0xffffffff}"))
    return lookups

def ldr_x_imm(word):
    # LDR Xt,[Xn,#imm12*8] unsigned immediate.
    if (word & 0xFFC00000) != 0xF9400000:
        return None
    return (word & 31, (word >> 5) & 31, ((word >> 10) & 4095) * 8)

def scan_xrefs(elf, targets, pointer_slots, limit=16000):
    """Scan matching direct ADR/ADRP+ADD or indirect ADRP+LDR pointer slot references.

    Short basic blocks only: we require exact target VA and same base register.
    An ADRP pair is discarded if a prior intervening instruction writes base
    through obvious ADR/ADRP/ADD (conservative, not full dataflow).
    """
    found = []
    pointer_map = {va:(target,label) for target,label,va in pointer_slots if va is not None}
    watch = set(targets) | set(pointer_map)
    for section in elf.text_regions():
        raw = elf.raw[section["off"]:section["off"]+section["size"]]
        n = len(raw) // 4
        for i in range(n):
            w = struct.unpack_from("<I", raw, 4*i)[0]
            pc = section["addr"]+4*i
            adr = host.decode_adr(w,pc)
            if adr is not None and adr[1] in watch:
                tgt = adr[1]; kind = "ADR_DIRECT" if tgt in targets else "ADR_POINTER_SLOT"
                label = targets.get(tgt, pointer_map.get(tgt,("",""))[1])
                found.append((f"0x{pc:X}",f"0x{section['off']+4*i:X}",kind,
                              f"0x{tgt:X}",label,0,""))
            adrp = host.decode_adrp(w,pc)
            if adrp is None:
                continue
            reg, base = adrp
            for gap in range(1,9):
                j=i+gap
                if j>=n:
                    break
                nw=struct.unpack_from("<I",raw,4*j)[0]
                add=host.decode_add_x_imm(nw)
                if add is not None and add[1]==reg and add[0]==reg:
                    target=base+add[2]
                    if target in watch:
                        kind="ADRP_ADD_DIRECT" if target in targets else "ADRP_ADD_POINTER_SLOT"
                        label=targets.get(target, pointer_map.get(target,("",""))[1])
                        found.append((f"0x{pc:X}",f"0x{section['off']+4*i:X}",kind,
                                      f"0x{target:X}",label,gap,f"next_pc=0x{pc+gap*4:X}"))
                ld=ldr_x_imm(nw)
                if ld is not None and ld[1]==reg:
                    target=base+ld[2]
                    if target in pointer_map:
                        found.append((f"0x{pc:X}",f"0x{section['off']+4*i:X}",
                                      "ADRP_LDR_POINTER_SLOT",f"0x{target:X}",
                                      pointer_map[target][1],gap,f"next_pc=0x{pc+gap*4:X}"))
                # Stop after a BL/RET/branch; no cross-control flow pairing.
                if nw & 0xFC000000 in (0x14000000,0x94000000) or nw == 0xD65F03C0:
                    break
                # Stop after base register is overwritten by an ADR / ADRP / ADD
                other=host.decode_adrp(nw,pc+gap*4) or host.decode_adr(nw,pc+gap*4)
                if other is not None and other[0]==reg:
                    break
                if add is not None and add[0]==reg and add[1]!=reg:
                    break
            if len(found)>limit:
                raise ValueError("too many code xrefs")
    # Exact duplicates only.
    return list(dict.fromkeys(found))

def code_windows(elf, xrefs, radius=14, max_anchors=75):
    windows=[]
    seen=set()
    for row in xrefs[:max_anchors]:
        pc=int(row[0],16)
        for section in elf.text_regions():
            if not section["addr"]<=pc<section["addr"]+section["size"]:
                continue
            off=section["off"]+(pc-section["addr"])
            for delta in range(-radius,radius+1):
                o=off+4*delta
                if o < section["off"] or o+4>section["off"]+section["size"]:
                    continue
                key=(o,pc)
                if key in seen:
                    continue
                seen.add(key)
                word=struct.unpack_from("<I",elf.raw,o)[0]
                site=section["addr"]+(o-section["off"])
                opclass="AARCH64_WORD"
                target=""
                if word&0xFC000000==0x94000000:
                    imm=word&0x3FFFFFF
                    rel=host.signed(imm,26)<<2
                    opclass="BL_CALL";target=f"0x{site+rel:X}"
                elif word&0xFC000000==0x14000000:
                    imm=word&0x3FFFFFF;rel=host.signed(imm,26)<<2
                    opclass="B_BRANCH";target=f"0x{site+rel:X}"
                elif word&0xFF000010==0x54000000:
                    opclass="B_COND"
                elif word&0x7F000000 in (0x34000000,0x35000000):
                    opclass="CBZ_OR_CBNZ"
                elif word == 0xD65F03C0:
                    opclass="RET"
                windows.append((f"0x{pc:X}",row[4],f"0x{site:X}",f"{word:08X}",opclass,target,delta))
            break
    return windows

def analyze(repo:Path,out:Path):
    exefs=repo/"Unpack/v2.0.2/exefs"
    manifest=json.loads((exefs/"exefs-manifest.json").read_text("utf-8"))
    data=(exefs/"main/main.elf").read_bytes()
    target=manifest["modules"]["main"]
    sha=hashlib.sha256(data).hexdigest()
    if sha!=target["elfSha256"] or len(data)!=target["elfSize"]:
        raise ValueError("native main.elf SHA or size not pinned")
    elf=host.ELF64(data)
    host.TERMS=TERMS
    hits,total,trunc=host.scan_strings(elf,"main",limit=3000)
    targets={int(x[4],16):x[6] for x in hits if any(term.lower() in x[6].lower() for term in KW)}
    lookups=scan_addrs(elf,targets)
    ptr=[row for rows in lookups.values() for row in rows]
    slots=[(row[2],row[1],row[3]) for row in ptr if row[0]=="EXACT_DATA_U64_POINTER"]
    xrefs=scan_xrefs(elf,targets,slots)
    windows=code_windows(elf,xrefs)
    out.mkdir(parents=True,exist_ok=True)
    rows_to_file(out/"trade-target-strings.tsv",
                 ("label","virtual_address","file_offset","source_region"),
                 [(label,f"0x{addr:X}",f"0x{next(int(x[3],16) for x in hits if int(x[4],16)==addr):X}",
                   next(x[5] for x in hits if int(x[4],16)==addr)) for addr,label in targets.items()])
    rows_to_file(out/"trade-rela-pointer-sites.tsv",
                 ("evidence","target_label","string_va","pointer_va","source_offset","source_region","notes"),
                 [(kind,label,f"0x{sv:X}", "" if pv is None else f"0x{pv:X}",
                   f"0x{offset:X}",reg,note) for kind,label,sv,pv,offset,reg,note in ptr])
    rows_to_file(out/"trade-code-xrefs.tsv",
                 ("instruction_pc","instruction_file_offset","evidence","target_va","target_string",
                  "instruction_gap","notes"),xrefs)
    rows_to_file(out/"trade-context-windows.tsv",
                 ("anchor_pc","target_string","instruction_pc","raw_instruction_hex","decode_class",
                  "branch_target","relative_word_index"),windows)
    # Probe known numeric item values only in contiguous sequences; these are
    # ambiguous without function/data linkage and are reported for audit only.
    needles=(struct.pack("<HH",534,535),struct.pack("<II",534,535),
             struct.pack("<HH",656,657),struct.pack("<II",656,657))
    patterns=[]
    for label,needle in zip(("ORBS_U16_ADJACENT","ORBS_U32_ADJACENT",
                             "MEGA_656_657_U16_ADJACENT","MEGA_656_657_U32_ADJACENT"),needles):
        for section in elf.data_regions():
            bb=data[section["off"]:section["off"]+section["size"]]
            for off in chunks(bb,needle):
                patterns.append((label,f"0x{section['addr']+off:X}",
                                 f"0x{section['off']+off:X}",section["name"]))
    rows_to_file(out/"item-id-adjacency.tsv",
                 ("pattern","virtual_address","file_offset","region"),patterns[:4000])
    summary={
        "version":"v2.0.2","mainElfSha256":sha,"mainElfBytes":len(data),
        "keywordStringCount":total,"targetStringCount":len(targets),
        "pointersAndRelocations":len(ptr),
        "exactStaticCodeRefs":len(xrefs),
        "nearbyInstructionRecords":len(windows),
        "rawItemIdAdjacentMatches":len(patterns),
        "evidenceStatus":"STATIC_CANDIDATE_ONLY",
        "runtimeHeldItemTradePredicate":"UNVERIFIED",
        "byEvidence":dict(Counter(row[2] for row in xrefs)),
        "targetHits":dict(Counter(row[4] for row in xrefs)),
        "caveats":[
            "String virtual addresses do not identify function starts.",
            "ADR/ADRP+ADD/LDR pairings are syntactic candidate references, not dataflow proof.",
            "RELATIVE relocation addends and data pointers do not by themselves prove callable consumers.",
            "No real Link Trade runtime call stack or item-specific reject branch has been verified.",
        ],
    }
    (out/"trade-deep-summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("DEEP_SUMMARY_JSON_BEGIN")
    print(json.dumps(summary,indent=2,ensure_ascii=False))
    print("DEEP_SUMMARY_JSON_END")
    for filename in ("trade-target-strings.tsv","trade-rela-pointer-sites.tsv",
                     "trade-code-xrefs.tsv","item-id-adjacency.tsv",
                     "trade-context-windows.tsv"):
        path=out/filename
        lines=path.read_text().splitlines()
        print(f"EVIDENCE {filename} lines={len(lines)}")
        print("EVIDENCE_TSV_BEGIN "+filename)
        for line in lines:
            print(line)
        print("EVIDENCE_TSV_END "+filename)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,default=Path(".za-work/trade-native-deep"))
    a=p.parse_args()
    analyze(a.repo.resolve(),a.output.resolve())

if __name__=="__main__":
    main()
