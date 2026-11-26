#!/usr/bin/env python3
"""Bounded native texture caller and producer audit."""
import argparse, collections, hashlib, importlib.util,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
def main():
    a=argparse.ArgumentParser();a.add_argument("--out",type=Path,default=Path(".za-work/texture-producers"));a=a.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    raw=Path("Unpack/v2.0.2/exefs/main/main.elf").read_bytes();sha=hashlib.sha256(raw).hexdigest()
    assert sha=="470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d"
    spec=importlib.util.spec_from_file_location("elfhelper",Path(__file__).with_name("Probe-ZA-Lua-Host-ELF.py"));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);e=m.ELF64(raw)
    dis=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
    def read(va,n):
        for s in e.segments:
            if s["addr"]<=va and va+n<=s["addr"]+s["size"]:
                o=s["off"]+va-s["addr"];return raw[o:o+n]
        return b""
    def text(va):
        if not any(s["name"]==".rodata" and s["addr"]<=va<s["addr"]+s["size"] for s in e.sections):return None
        b=read(va,160).split(b"\0",1)[0]
        if b and all(32<=x<127 for x in b):return b.decode()
    def window(lo,hi,anchor):
        ins=[dict(va=hex(i.address),op=i.mnemonic,args=i.op_str,bytes=i.bytes.hex()) for i in dis.disasm(read(lo,hi-lo),lo)]
        literals=[]
        for i in range(len(ins)-1):
            pc=int(ins[i]["va"],16);ap=m.decode_adrp(int(ins[i]["bytes"],16) if False else int.from_bytes(bytes.fromhex(ins[i]["bytes"]),"little"),pc)
            if not ap:continue
            ad=m.decode_add_x_imm(int.from_bytes(bytes.fromhex(ins[i+1]["bytes"]),"little"))
            if ad and ad[1]==ap[0]:
                va=ap[1]+ad[2];st=text(va)
                if st:literals.append(dict(pc=hex(pc),va=hex(va),text=st))
        return dict(anchor=hex(anchor),instructions=ins,literals=literals)
    # Identify enclosing prologues as candidates, not inferred function extent.
    roots=[0x2d33c84,0x2d6aef8]
    windows=[];starts=[]
    for va in roots:
        w=window(va-0x500,va+0x340,va);windows.append(w)
        pre=[i for i in w["instructions"] if int(i["va"],16)<=va and i["op"]=="stp" and i["args"].startswith("x29, x30, [sp")]
        if pre:
            p=int(pre[-1]["va"],16);prev=next((i for i in w["instructions"] if int(i["va"],16)==p-4),None)
            if prev and prev["op"]=="sub" and prev["args"].startswith("sp, sp,"):p-=4
            starts.append(p)
    targets=set(starts)|{0x2d33be4,0x2d33c00,0x629d8c}
    calls=[]
    for s in e.text_regions():
        b=raw[s["off"]:s["off"]+s["size"]];ws=memoryview(b[:len(b)//4*4]).cast("I")
        for i,w in enumerate(ws):
            if w&0x7c000000!=0x14000000:continue
            pc=s["addr"]+4*i;dst=pc+4*m.signed(w&0x3ffffff,26)
            if dst in targets:calls.append(dict(pc=hex(pc),target=hex(dst),kind="BL" if w&0x80000000 else "B"))
    for c in calls[:100]:
        va=int(c["pc"],16);windows.append(window(va-0x90,va+0x60,va))
    for w in windows:
        print("WINDOW",w["anchor"])
        for i in w["instructions"]:print(i["va"],i["op"],i["args"])
        for r in w["literals"]:print("LITERAL",json.dumps(r))
    for c in calls:print("CALL",json.dumps(c))
    (a.out/"windows.jsonl").write_text("".join(json.dumps(w)+"\n" for w in windows));(a.out/"calls.jsonl").write_text("".join(json.dumps(c)+"\n" for c in calls))
    s=dict(elf_sha256=sha,start_candidates=[hex(x) for x in starts],calls=len(calls),windows=len(windows),runtime_verified=False);(a.out/"summary.json").write_text(json.dumps(s,indent=2));print("SUMMARY",json.dumps(s))
if __name__=="__main__":main()
