#!/usr/bin/env python3
"""Locate native UI2D RTTI and shader candidates; bounded disassembly, no inferred function names."""
import argparse,collections,hashlib,importlib.util,json,re,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
s=importlib.util.spec_from_file_location("elf",Path(__file__).with_name("Probe-ZA-Lua-Host-ELF.py"));elf=importlib.util.module_from_spec(s);s.loader.exec_module(elf)
def run(out):
    out.mkdir(parents=True,exist_ok=True);b=Path("Unpack/v2.0.2/exefs/main/main.elf").read_bytes();digest=hashlib.sha256(b).hexdigest()
    if digest!="470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d":raise ValueError("ELF hash")
    e=elf.ELF64(b);cs=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN);counts=collections.Counter();names={};ptr=collections.defaultdict(list);values={};embedded=[]
    def locate(va):
        for g in e.segments:
            if g["addr"]<=va<g["addr"]+g["size"]:return g,g["off"]+va-g["addr"]
        return None,None
    def isexec(va):
        g,_=locate(va);return bool(g and g["flags"]&1)
    for seg in e.segments:
        if seg["flags"]&1:continue
        data=b[seg["off"]:seg["off"]+seg["size"]]
        for m in re.finditer(rb"(?<![A-Za-z0-9_])(?:N2nn4ui2d|N2nn4font|N2nn3gfx)[A-Za-z0-9_]{2,140}\x00",data):
            va=seg["addr"]+m.start();names[va]=m.group()[:-1].decode("ascii")
        for m in re.finditer(rb"BNSH",data):
            o=seg["off"]+m.start()
            # Magic alone is a candidate, not proof of an embedded shader.
            if o+32<=len(b) and b[o+12:o+14] in (b"\xff\xfe",b"\xfe\xff"):
                embedded.append(dict(va=seg["addr"]+m.start(),file_offset=o,header=b[o:o+32].hex()))
    for sec in e.sections:
        if sec["stype"]!=4 or sec["entsize"]<24:continue
        for p in range(sec["off"],sec["off"]+sec["size"]-23,sec["entsize"]):
            slot,info,add=struct.unpack_from("<QQq",b,p)
            if (info&0xffffffff)==1027:
                values[slot]=add;ptr[add].append((slot,"RELA_RELATIVE"))
    # Raw aligned pointers only where mapped; avoid treating arbitrary data as typeinfo.
    for seg in e.segments:
        if seg["flags"]&1:continue
        for o in range(seg["off"],seg["off"]+seg["size"]-7,8):
            va=seg["addr"]+o-seg["off"]
            if va in values:continue
            target=struct.unpack_from("<Q",b,o)[0]
            if target in names:ptr[target].append((va,"RAW_POINTER"))
    typeinfo=[]
    for va,name in sorted(names.items()):
        for slot,kind in ptr.get(va,[]):
            ti=slot-8;g,o=locate(ti)
            if not g or g["flags"]&1 or o+16>len(b):continue
            vptr=values.get(ti,struct.unpack_from("<Q",b,o)[0])
            if not locate(vptr)[0]:continue
            row=dict(name=name,name_va=va,typeinfo_candidate=ti,name_slot=slot,kind=kind,typeinfo_vptr=vptr,vtables=[])
            for ts,tk in ptr.get(ti,[]):
                start=ts+8;slots=[]
                for i in range(24):
                    x=start+8*i;gg,oo=locate(x)
                    if not gg or oo+8>len(b):break
                    fn=values.get(x,struct.unpack_from("<Q",b,oo)[0])
                    if not isexec(fn):break
                    slots.append(dict(slot=i,address=fn))
                if slots:row["vtables"].append(dict(typeinfo_slot=ts,first_function_slot=start,kind=tk,slots=slots))
            typeinfo.append(row)
    # Also retain exact known font-loader xrefs, without declaring entry boundaries.
    regions=[]
    for pc in (19412324,19444444,19444556,8455276):
        g,o=locate(pc)
        if not g:continue
        start=max(g["off"],o-48);end=min(g["off"]+g["size"],o+80);va=g["addr"]+start-g["off"]
        ins=[dict(pc=i.address,bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in cs.disasm(b[start:end],va)]
        regions.append(dict(reference_pc=pc,instructions=ins))
    counts.update(names=len(names),typeinfo_candidates=len(typeinfo),vtable_candidates=sum(len(t["vtables"]) for t in typeinfo),embedded_bnsh_candidates=len(embedded))
    result=dict(sha256=digest,counts=dict(counts),names=[dict(va=k,name=v) for k,v in sorted(names.items())],typeinfo=typeinfo,embedded=embedded,reference_windows=regions,material_formula_verified=False)
    (out/"native-ui-rtti.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(counts=dict(counts),names=result["names"][:75],typeinfo=[dict(name=t["name"],va=hex(t["typeinfo_candidate"]),vtables=[dict(va=hex(x["first_function_slot"]),slots=len(x["slots"])) for x in t["vtables"]]) for t in typeinfo[:40]],embedded=embedded[:12],reference_windows=regions[:3]),indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=Path(".za-work/ui-rtti"));a=p.parse_args()
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("local output only")
    run(a.out)
if __name__=="__main__":main()
