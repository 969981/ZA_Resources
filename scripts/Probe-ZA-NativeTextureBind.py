#!/usr/bin/env python3
"""Native texture bind call graph, bounded windows and data evidence."""
import argparse,collections,hashlib,importlib.util,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=Path(".za-work/native-bind"));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    raw=Path("Unpack/v2.0.2/exefs/main/main.elf").read_bytes();sha=hashlib.sha256(raw).hexdigest()
    assert sha=="470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d"
    spec=importlib.util.spec_from_file_location("elfhelper",Path(__file__).with_name("Probe-ZA-Lua-Host-ELF.py"));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);e=m.ELF64(raw)
    d=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
    def read(va,n):
        for s in e.segments:
            if s["addr"]<=va<s["addr"]+s["size"]:
                off=s["off"]+va-s["addr"];return raw[off:off+min(n,s["addr"]+s["size"]-va)]
        return b""
    def literal(va):
        if not any(s["name"]==".rodata" and s["addr"]<=va<s["addr"]+s["size"] for s in e.sections):return None
        b=read(va,160).split(b"\0",1)[0]
        return b.decode("ascii") if b and all(32<=x<127 for x in b) else None
    def window(va,lo,hi):
        ins=[dict(va=hex(i.address),op=i.mnemonic,args=i.op_str,bytes=i.bytes.hex()) for i in d.disasm(read(lo,hi-lo),lo)]
        lits=[]
        for i in range(len(ins)-1):
            pc=int(ins[i]["va"],16);ap=m.decode_adrp(int.from_bytes(bytes.fromhex(ins[i]["bytes"]),"little"),pc)
            if not ap:continue
            ad=m.decode_add_x_imm(int.from_bytes(bytes.fromhex(ins[i+1]["bytes"]),"little"))
            if ad and ad[1]==ap[0]:
                v=ap[1]+ad[2];s=literal(v)
                if s:lits.append(dict(pc=hex(pc),va=hex(v),text=s))
        return dict(anchor=hex(va),instructions=ins,literals=lits)
    roots=[0x3d45cc,0xf65720,0x10000c8,0x2b50fc,0x886240,0x2d32d18]
    wins=[window(v,v-(0x300 if v==0x2d32d18 else 0),v+0x280) for v in roots]
    calls=[]
    for s in e.text_regions():
        b=raw[s["off"]:s["off"]+s["size"]];ws=memoryview(b[:len(b)//4*4]).cast("I")
        for i,w in enumerate(ws):
            if w&0x7c000000!=0x14000000:continue
            pc=s["addr"]+4*i;dst=pc+4*m.signed(w&0x3ffffff,26)
            if dst in roots:calls.append(dict(pc=hex(pc),target=hex(dst),kind="BL" if w&0x80000000 else "B"))
    for w in wins:
        print("WINDOW",w["anchor"])
        for i in w["instructions"]:print(i["va"],i["op"],i["args"])
        for r in w["literals"]:print("LITERAL",json.dumps(r))
    for c in calls:
        if c["target"]=="0x3d45cc":print("BIND_CALL",json.dumps(c))
    for name,rows in [("windows",wins),("calls",calls)]:
        (a.out/(name+".jsonl")).write_text("".join(json.dumps(x)+"\n" for x in rows))
    s=dict(elf_sha256=sha,windows=len(wins),direct_branch_counts=dict(collections.Counter(c["target"] for c in calls)),runtime_verified=False)
    (a.out/"summary.json").write_text(json.dumps(s,indent=2));print("SUMMARY",json.dumps(s))
if __name__=="__main__":main()
