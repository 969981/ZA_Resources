#!/usr/bin/env python3
"""Read-only audit of adjacent Pokémon Z-A item IDs within SHA-pinned main.elf.

Records all surrounding u32 entries and page-relative ADRP references.
These bytes are *not* proof of Link Trade blacklist or runtime validation.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import struct
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
helper=ROOT/"scripts/Probe-ZA-Lua-Host-ELF.py"
spec=importlib.util.spec_from_file_location("elfhelper",helper)
elfhelper=importlib.util.module_from_spec(spec)
spec.loader.exec_module(elfhelper)

SITES={"ORB_IDS_534_535":(0x3358434,534,535),
       "MEGA_IDS_656_657_FIRST":(0x33598E4,656,657),
       "MEGA_IDS_656_657_SECOND":(0x335A708,656,657)}

def off_for_va(elf,addr):
    for sec in elf.sections:
        if sec["stype"]!=8 and sec["addr"]<=addr<sec["addr"]+sec["size"] and sec["flags"]&2:
            return sec["off"]+(addr-sec["addr"]),sec["name"]
    raise ValueError(f"No section for VA: 0x{addr:X}")

def main():
    manifest=json.loads((ROOT/"Unpack/v2.0.2/exefs/exefs-manifest.json").read_text())
    src=ROOT/"Unpack/v2.0.2/exefs/main/main.elf"
    raw=src.read_bytes()
    expected=manifest["modules"]["main"]
    assert len(raw)==expected["elfSize"] and hashlib.sha256(raw).hexdigest()==expected["elfSha256"]
    elf=elfhelper.ELF64(raw)
    names={}
    with (ROOT/"docs/research/v2.0.2/data/za-v2.0.2-items-all-fields.csv").open(
            encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            names[int(row["Id"])]=(row["NameZH"],row["ResearchGroup"])
    out=ROOT/".za-work/trade-native-deep"
    out.mkdir(parents=True,exist_ok=True)
    context=[]
    pages=set()
    for name,(va,first,second) in SITES.items():
        pos,sect=off_for_va(elf,va)
        x,y=struct.unpack_from("<II",raw,pos)
        if (x,y)!=(first,second):
            raise ValueError(f"unexpected item-id site {name}: {x},{y}")
        pages.add(va&~4095)
        for delta in range(-40,41):
            addr=va+4*delta
            try:
                off,reg=off_for_va(elf,addr)
                value=struct.unpack_from("<I",raw,off)[0]
            except (ValueError,struct.error):
                continue
            desc,group=names.get(value,("",""))
            context.append([name,delta,f"0x{addr:X}",value,desc,group])
    ref=[]
    for reg in elf.text_regions():
        bb=raw[reg["off"]:reg["off"]+reg["size"]]
        n=len(bb)//4
        for i in range(n):
            w=struct.unpack_from("<I",bb,4*i)[0]
            pc=reg["addr"]+4*i
            adr=elfhelper.decode_adrp(w,pc)
            if adr is None or adr[1] not in pages:
                continue
            targetreg,base=adr
            near=[]
            for g in range(1,9):
                if i+g>=n:
                    break
                after=struct.unpack_from("<I",bb,4*(i+g))[0]
                add=elfhelper.decode_add_x_imm(after)
                if add and add[0]==targetreg and add[1]==targetreg:
                    near.append((g,"ADD",base+add[2]))
                if after&0xFC000000 in (0x94000000,0x14000000):
                    break
            for name,(site,first,second) in SITES.items():
                if base!=(site&~4095):
                    continue
                span=[(g,k,addr) for g,k,addr in near if abs(addr-site)<=2048]
                ref.append([name,f"0x{pc:X}",f"0x{reg['off']+4*i:X}",
                            f"0x{base:X}",";".join(f"gap{g}:{k}:0x{addr:X}" for g,k,addr in span)])
    def save(path,cols,rows):
        with (out/path).open("w",encoding="utf-8",newline="") as f:
            writer=csv.writer(f,delimiter="\t")
            writer.writerow(cols);writer.writerows(rows)
    save("item-id-table-neighborhoods.tsv",
         ("site","relative_u32_index","virtual_address","u32","known_item_name_zh","research_group"),context)
    save("item-id-table-page-references.tsv",
         ("item_id_pattern","adrp_pc","adrp_file_offset","page_base","near_add_targets"),ref)
    summary={"version":"v2.0.2","mainSha256":expected["elfSha256"],
             "inputIdSites":len(SITES),"contextRows":len(context),
             "codePageReferences":len(ref),
             "codeNearAddPairs":sum(bool(x[-1]) for x in ref),
             "status":"STATIC_ONLY_NOT_LINK_TRADE_CONFIRMATION"}
    (out/"item-id-table-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("ITEM_ID_TABLE_SUMMARY_BEGIN")
    print(json.dumps(summary,indent=2))
    print("ITEM_ID_TABLE_SUMMARY_END")
    print("ITEM_ID_CONTEXT_BEGIN")
    for r in context:
        print("\t".join(map(str,r)))
    print("ITEM_ID_CONTEXT_END")
    print("ITEM_ID_PAGE_REFS_BEGIN")
    for r in ref:
        print("\t".join(map(str,r)))
    print("ITEM_ID_PAGE_REFS_END")

if __name__=="__main__":
    main()
