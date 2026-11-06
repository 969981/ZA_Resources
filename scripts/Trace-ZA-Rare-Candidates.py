#!/usr/bin/env python3
"""Bounded AArch64 disassembly around exact ZA Rare/Never mask sites.
This is a static inspection aide only, not proof of execution or shiny logic.
Requires capstone>=5; source/ELF integrity checked against existing report.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

ROOT=Path(__file__).resolve().parents[1]
ELF=ROOT/"Unpack/v2.0.2/exefs/main/main.elf"
REPORT=ROOT/"docs/research/v2.0.2/za-rare-arm64-static-candidates.json"
OUTPUT=ROOT/"docs/research/v2.0.2/za-rare-arm64-exact-sites.md"

def segments(raw):
    if raw[:6]!=b"\x7fELF\x02\x01" or struct.unpack_from("<H",raw,18)[0]!=183:
        raise ValueError("not AArch64 little endian ELF")
    phoff=struct.unpack_from("<Q",raw,32)[0]
    entsize,n=struct.unpack_from("<HH",raw,54)
    for i in range(n):
        kind,flags,off,addr,_,sz,_,_=struct.unpack_from("<IIQQQQQQ",raw,phoff+i*entsize)
        if kind==1 and flags&1 and sz and off+sz<=len(raw):
            yield (off,addr,sz)

def context(raw,segs,pc,before,after,md):
    for off,va,sz in segs:
        if va<=pc<va+sz:
            start=max(va,pc-before)&~3
            end=min(va+sz,pc+after+4)&~3
            data=raw[off+start-va:off+end-va]
            return [
                {"pc":"0x%X"%i.address, "op":i.mnemonic, "args":i.op_str,
                 "word":raw[off+i.address-va:off+i.address-va+4].hex(),
                 "needle":i.address==pc}
                for i in md.disasm(data,start)
            ]
    raise ValueError("candidate outside executable segment")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--elf",type=Path,default=ELF)
    parser.add_argument("--report",type=Path,default=REPORT)
    parser.add_argument("--output",type=Path,default=OUTPUT)
    parser.add_argument("--site-kind",choices=["exact-never","anti-shiny-xor"],default="exact-never")
    parser.add_argument("--before",type=lambda x:int(x,0),default=0x100)
    parser.add_argument("--after",type=lambda x:int(x,0),default=0x100)
    p=parser.parse_args()
    raw=p.elf.read_bytes()
    report=json.loads(p.report.read_text(encoding="utf-8"))
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=report["elf_sha256"]:
        raise SystemExit("ELF and report SHA mismatch")
    field="exact_never_instruction_sites" if p.site_kind=="exact-never" else "anti_shiny_xor_candidates"
    sites=report["arm64_scan"][field]
    if not sites: raise SystemExit("No exact sites")
    md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    md.detail=False
    segs=list(segments(raw))
    lines=[
        "# Z-A v2.0.2 "+("Rare mask 0x1FFFFFFF" if p.site_kind=="exact-never" else "AntiShiny XOR 0x10000000")+" exact opcode contexts",
        "",
        "> [!WARNING] STATIC CANDIDATES ONLY. A mask instruction does not prove EncountData.Rare reads or a runtime hook.",
        "",
        "- main.elf SHA-256: "+actual,
        "- Exact scanner site count: "+str(len(sites)),
        "- Instruction window: 0x%X bytes before and 0x%X bytes after."%(p.before,p.after),
        "- To confirm: trace operand register origin and TID/PID xor logic in the same function; verify runtime via GDB, not just opcode shape.",
        "",
    ]
    for site in sites:
        pc=int(site["pc"],16)
        lines.append("## Static PC "+site["pc"]+" (word "+site["instruction"]+")")
        lines.append("")
        lines.append("- ELF file offset: "+site["file_offset"]+"; opcode: "+site["operation"]+"; mask: "+site["immediate"])
        lines.append("- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.")
        lines.extend(["","~~~asm"])
        for ins in context(raw,segs,pc,p.before,p.after,md):
            lines.append("%s%s: %-8s %s ; %s"%
                         (">> " if ins["needle"] else "   ",ins["pc"],ins["op"],ins["args"],ins["word"]))
        lines.extend(["~~~",""])
    p.output.parent.mkdir(parents=True,exist_ok=True)
    p.output.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"sha256":actual,"sites":[x["pc"] for x in sites],"output":str(p.output)},indent=2))
if __name__=="__main__":
    main()
