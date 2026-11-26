#!/usr/bin/env python3
"""Checksum-pinned native embedded BNSH and font virtual method evidence."""
import argparse,collections,hashlib,importlib.util,json,re,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
s=importlib.util.spec_from_file_location("elf",Path(__file__).with_name("Probe-ZA-Lua-Host-ELF.py"));elf=importlib.util.module_from_spec(s);s.loader.exec_module(elf)
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=Path(".za-work/native-font-shader"));a=p.parse_args()
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("local output only")
    a.out.mkdir(parents=True,exist_ok=True)
    b=Path("Unpack/v2.0.2/exefs/main/main.elf").read_bytes();digest=hashlib.sha256(b).hexdigest()
    if digest!="470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d":raise ValueError("ELF SHA")
    e=elf.ELF64(b);cs=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN);cs.detail=False
    def locate(va,n=1):
        for g in e.segments:
            if g["addr"]<=va and va+n<=g["addr"]+g["size"]:return g,g["off"]+va-g["addr"]
        raise ValueError(f"unmapped {va:x}")
    def data(va,n):
        g,o=locate(va,n);return b[o:o+n]
    def execp(va):
        try:return bool(locate(va,4)[0]["flags"]&1) and va%4==0
        except ValueError:return False
    reloc={}
    for sec in e.sections:
        if sec["stype"]==4 and sec["entsize"]>=24:
            for o in range(sec["off"],sec["off"]+sec["size"]-23,sec["entsize"]):
                slot,info,add=struct.unpack_from("<QQq",b,o)
                if info&0xffffffff==1027:reloc[slot]=add
    def ptr(va):return reloc.get(va,struct.unpack("<Q",data(va,8))[0])
    def dis(va,n):
        return [dict(pc=f"0x{i.address:X}",bytes=i.bytes.hex(),op=i.mnemonic,args=i.op_str) for i in cs.disasm(data(va,n),va)]
    def body(va,limit=512):
        if not execp(va):return []
        rows=dis(va,limit)
        # First return is a bounded prefix, not a proven full function.
        for i,x in enumerate(rows):
            if x["op"]=="ret":return rows[:i+1]
        return rows
    def calls(rows):
        return sorted({int(x["args"][1:],16) for x in rows if x["op"]=="bl" and x["args"].startswith("#0x")})
    sh=[]
    for va in (0x3ef8000,0x3f00000):
        h=data(va,32);size=struct.unpack_from("<I",h,28)[0]
        if h[:8]!=b"BNSH\0\0\0\0" or h[12:14]!=b"\xff\xfe" or not 32<size<2**20:raise ValueError("BNSH header")
        raw=data(va,size)
        strings=[dict(offset=m.start(),text=m.group().decode("ascii")) for m in re.finditer(rb"[A-Za-z_][A-Za-z0-9_./: -]{4,100}\x00",raw) if re.search(rb"(?i)shader|font|layout|ui2d|vertex|pixel|fragment|sampler|texture|program|variation|color|material|uniform|rect|glyph|screen|draw",m.group())]
        tags=[dict(offset=m.start(),tag=m.group().decode("ascii")) for m in re.finditer(rb"BNSH|_RLT|_STR|_DIC|grsc|grsp|grsv|grsh|grst",raw)]
        sh.append(dict(va=hex(va),size=size,sha256=hashlib.sha256(raw).hexdigest(),header=h.hex(),tags=tags,strings=strings[:120],ui_binding_verified=False))
    windows=[];callee={}
    for pc in (40001936,40004348,40266452):
        rows=dis(pc-64,192);targets=calls(rows)
        windows.append(dict(pc=hex(pc),instructions=rows,calls=[hex(x) for x in targets]))
        for t in targets:
            if execp(t):callee[hex(t)]=body(t,256)
    tables=[];functions={}
    for name,start,ti in [("ResFont",0x3c92110,0x3c92240),("ResFontBase",0x3c92268,0x3c92398)]:
        if ptr(start-8)!=ti:raise ValueError("typeinfo header mismatch")
        off=struct.unpack("<q",data(start-16,8))[0];slots=[]
        for i in range(64):
            slot=start+8*i;fn=ptr(slot)
            if not execp(fn):break
            rows=body(fn);ops=collections.Counter(x["op"] for x in rows)
            score=sum(ops[x] for x in ("udiv","sdiv","msub","madd","ucvtf","scvtf","fdiv","fmul","ldrh","ldrb"))
            slots.append(dict(slot=i,slot_va=hex(slot),function=hex(fn),arithmetic_score=score,ops=dict(ops)))
            functions[hex(fn)]=rows
        tables.append(dict(name=name,start=hex(start),typeinfo=hex(ti),offset_to_top=off,slots=slots))
    # Follow direct calls from the most relevant virtual method prefixes (one level).
    ranked=sorted((x for t in tables for x in t["slots"]),key=lambda x:-x["arithmetic_score"])
    for slot in ranked[:12]:
        for t in calls(functions[slot["function"]]):
            if execp(t) and hex(t) not in functions:functions[hex(t)]=body(t)
    result=dict(elf_sha256=digest,containers=sh,reference_windows=windows,shader_callees=callee,font_vtables=tables,font_methods=functions,native_formula_verified=False)
    (a.out/"evidence.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(containers=sh,shader_refs=[dict(pc=x["pc"],calls=x["calls"],window=[v for v in x["instructions"] if v["op"] in ("adrp","add","bl","blr","mov")]) for x in windows],font_tables=[dict(name=t["name"],start=t["start"],offset_to_top=t["offset_to_top"],slots=len(t["slots"])) for t in tables],ranked=ranked[:15],top_method_prefixes={x["function"]:functions[x["function"]][:36] for x in ranked[:5]},native_formula_verified=False),indent=2))
if __name__=="__main__":main()
