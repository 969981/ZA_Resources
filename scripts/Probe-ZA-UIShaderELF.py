#!/usr/bin/env python3
"""Checksum-pinned read-only ELF shader string and relocation candidate locator."""
import argparse, collections, hashlib, importlib.util, json, re, struct
from pathlib import Path
s=importlib.util.spec_from_file_location("elf",Path(__file__).with_name("Probe-ZA-Lua-Host-ELF.py"));elf=importlib.util.module_from_spec(s);s.loader.exec_module(elf)
TERMS=re.compile(rb"(?i)(?:nn::lyt|nn_lyt|layoutshader|layout_shader|shaderlayout|shader_layout|texturecombiner|texcombiner|texturepattern|texture_srt|capturetexture|capture_texture|drawcontext|materialshader|material_shader|imgui_texture2d|imgui\.bnsh|\.bfsha|\.bflim|\.bfcpx|\.bffnt|c_capture_00|uikitpokeicon)")
def audit(out):
    out.mkdir(parents=True,exist_ok=True);p=Path("Unpack/v2.0.2/exefs/main/main.elf");b=p.read_bytes();digest=hashlib.sha256(b).hexdigest()
    if digest!="470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d":raise ValueError("ELF SHA mismatch")
    e=elf.ELF64(b);hits=[];targets={};rel=[];refs=[];counts=collections.Counter()
    for seg in e.segments:
        if seg["flags"]&1:continue
        for m in re.finditer(rb"[\x20-\x7e]{4,}",b[seg["off"]:seg["off"]+seg["size"]]):
            value=m.group()
            if not TERMS.search(value):continue
            va=seg["addr"]+m.start();row=dict(va=va,file_offset=seg["off"]+m.start(),text=value[:400].decode("ascii"));hits.append(row);targets[va]=row;counts["string_hits"]+=1
    for sec in e.sections:
        if sec["stype"]!=4 or sec["entsize"]<24:continue
        for p in range(sec["off"],sec["off"]+sec["size"]-23,sec["entsize"]):
            slot,info,add=struct.unpack_from("<QQq",b,p)
            if add in targets:rel.append(dict(slot_va=slot,type=info&0xffffffff,target=targets[add]));counts["relocations"]+=1
    # Direct ADR and nearby same-register ADRP + ADD; not full dataflow.
    pages=collections.defaultdict(set)
    for va in targets:pages[va&~4095].add(va)
    def sext(v,n):return (v^(1<<(n-1)))-(1<<(n-1))
    for seg in e.segments:
        if not seg["flags"]&1:continue
        lo=seg["off"];hi=lo+seg["size"]
        for o in range(lo,hi-3,4):
            ins=struct.unpack_from("<I",b,o)[0];pc=seg["addr"]+o-lo;kind=ins&0x9f000000
            if kind not in (0x10000000,0x90000000):continue
            imm=sext(((ins>>5)&0x7ffff)<<2|((ins>>29)&3),21);rd=ins&31
            if kind==0x10000000:
                dest=pc+imm
                if dest in targets:refs.append(dict(pc=pc,target=targets[dest],kind="ADR"));counts["adr"]+=1
            else:
                page=(pc&~4095)+(imm<<12)
                if page not in pages:continue
                for k in (4,8,12,16):
                    if o+k+4>hi:break
                    q=struct.unpack_from("<I",b,o+k)[0]
                    if q&0xff000000==0x91000000 and (q>>5)&31==rd:
                        dest=page+(((q>>10)&4095)<<(12 if q&(1<<22) else 0))
                        if dest in targets:refs.append(dict(pc=pc,add_pc=pc+k,target=targets[dest],kind="ADRP_ADD_CANDIDATE"));counts["adrp_add"]+=1
    result=dict(elf_sha256=digest,counts=dict(counts),strings=hits,relocations=rel,references=refs,ui_shader_binding_verified=False,formula_verified=False)
    (out/"shader-locators.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(dict(counts=dict(counts),strings=hits[:35],references=refs[:15],ui_shader_binding_verified=False),indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=Path(".za-work/ui-shader-elf"));a=p.parse_args()
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("local output only")
    audit(a.out)
if __name__=="__main__":main()
