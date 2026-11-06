#!/usr/bin/env python3
"""Disassemble only bounded v2.0.2 native candidate windows.

The sites were independently observed in SHA-verified main.elf.
Disassembly and nearby calls are not runtime Link Trade predicate proof.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"scripts/Probe-ZA-Lua-Host-ELF.py"
spec=importlib.util.spec_from_file_location("elfhelper",PATH)
host=importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)

SITES={
    "TradeCommandCancel_type_name_ref":0x2DC4154,
    "TradeUI_10_06_resource_ref":0x2D304E0,
    "TradeUI_10_07_resource_ref":0x2D315B4,
    "ItemID_orb_table_page_ref":0x218B14C,
    "ItemID_mega_table_page_ref_A":0x21963DC,
    "ItemID_mega_table_page_ref_B":0x2196320,
    "ItemID_orb_table_page_ref_B":0x2197354,
}

def main():
    manifest=json.loads((ROOT/"Unpack/v2.0.2/exefs/exefs-manifest.json").read_text())
    file=ROOT/"Unpack/v2.0.2/exefs/main/main.elf"
    raw=file.read_bytes()
    if len(raw)!=manifest["modules"]["main"]["elfSize"] or (
        hashlib.sha256(raw).hexdigest()!=manifest["modules"]["main"]["elfSha256"]
    ):
        raise ValueError("native ELF does not match pinned SHA")
    elf=host.ELF64(raw)
    cs=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
    cs.detail=False
    rows=[];calls=[]
    for label,pc in SITES.items():
        for sec in elf.text_regions():
            if sec["addr"]<=pc<sec["addr"]+sec["size"]:
                begin=max(sec["addr"],pc-0x100)
                end=min(sec["addr"]+sec["size"],pc+0x104)
                off=sec["off"]+(begin-sec["addr"])
                data=raw[off:off+end-begin]
                for ins in cs.disasm(data,begin):
                    rel=ins.address-pc
                    rows.append([label,f"0x{pc:X}",f"0x{ins.address:X}",
                                 f"{rel:+d}",ins.mnemonic,ins.op_str])
                    if ins.mnemonic in ("bl","blr","br","ret","b","cbz","cbnz") or (
                        ins.mnemonic.startswith("b.") or ins.mnemonic.startswith("tb")
                    ):
                        calls.append([label,f"0x{ins.address:X}",ins.mnemonic,ins.op_str])
                break
        else:
            raise ValueError(f"PC not found in native executable: 0x{pc:X}")
    out=ROOT/".za-work/trade-disassembly"
    out.mkdir(parents=True,exist_ok=True)
    for file,head,data in (
        ("trade-candidate-disassembly.tsv",
         ("site_label","anchor_pc","instruction_pc","relative_bytes","mnemonic","operands"),rows),
        ("trade-candidate-branches.tsv",
         ("site_label","instruction_pc","mnemonic","operands"),calls)
    ):
        with (out/file).open("w",encoding="utf-8",newline="") as f:
            w=csv.writer(f,delimiter="\t");w.writerow(head);w.writerows(data)
    summ={"mainSha256":manifest["modules"]["main"]["elfSha256"],
          "sites":len(SITES),"instructions":len(rows),
          "branchAndCallInstructions":len(calls),
          "status":"BOUNDED_STATIC_DISASSEMBLY_ONLY"}
    (out/"trade-disassembly-summary.json").write_text(json.dumps(summ,indent=2)+"\n")
    print("TRADE_DISASSEMBLY_SUMMARY_BEGIN")
    print(json.dumps(summ,indent=2))
    print("TRADE_DISASSEMBLY_SUMMARY_END")
    print("TRADE_DISASSEMBLY_SELECTED_BEGIN")
    for row in rows:
        if abs(int(row[3]))<=64:
            print("\t".join(row))
    print("TRADE_DISASSEMBLY_SELECTED_END")
    print("TRADE_BRANCH_CALLS_BEGIN")
    for row in calls:
        print("\t".join(row))
    print("TRADE_BRANCH_CALLS_END")

if __name__=="__main__":
    main()
