#!/usr/bin/env python3
"""Pinned ELF path construction and resource-registration evidence, not a runtime selector."""
import argparse, hashlib, importlib.util, json, struct, collections, re
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
def main():
    p=argparse.ArgumentParser(); p.add_argument("--out",type=Path,default=Path(".za-work/icon-registration")); a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    raw=Path("Unpack/v2.0.2/exefs/main/main.elf").read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if sha!="470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d": raise ValueError("wrong ELF")
    spec=importlib.util.spec_from_file_location("elfhelper",Path(__file__).with_name("Probe-ZA-Lua-Host-ELF.py")); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); e=m.ELF64(raw)
    dis=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
    def region(va):
        for s in e.sections:
            if s["flags"]&2 and s["stype"]!=8 and s["addr"]<=va<s["addr"]+s["size"]: return s
        for s in e.segments:
            if s["addr"]<=va<s["addr"]+s["size"]: return s
    def read(va,n):
        s=region(va)
        if not s or va+n>s["addr"]+s["size"]: return b""
        p=s["off"]+va-s["addr"]; return raw[p:p+n]
    def string(va):
        s=region(va)
        if not s or s["flags"]&4 and s["kind"]=="section": return None
        b=read(va,min(192,s["addr"]+s["size"]-va)).split(b"\0",1)[0]
        return b.decode("ascii") if len(b)>=3 and all(32<=x<=126 for x in b) else None
    def qword(va):
        b=read(va,8); return struct.unpack("<Q",b)[0] if len(b)==8 else None
    constants={0x32F5F06:12,0x323BCAD:10,0x3296760:None,0x32E07A3:None,0x326855E:None,0x3288619:None,0x32D57AB:None}
    strings=[]
    for va,n in constants.items():
        s=region(va); b=read(va,n) if n else b""
        strings.append(dict(va=hex(va),region=s["name"] if s else None,declared_length=n,exact_hex=b.hex(),exact_ascii=b.decode("ascii","backslashreplace") if n else None,c_string=string(va)))
    for r in strings: print("STRING",json.dumps(r))
    roots={0x3E0ACA8:"offset_path_slot",0x3E27BD0:"default_path_slot"}
    neighborhoods=[]
    for root,name in roots.items():
        for va in range(root-0x60,root+0x68,8):
            v=qword(va); s=region(v) if v is not None else None
            neighborhoods.append(dict(root=hex(root),slot=hex(va),delta=va-root,value=hex(v) if v is not None else None,target_section=s["name"] if s else None,target_string=string(v) if s else None))
    for r in neighborhoods: print("NEIGHBOR",json.dumps(r))
    targets={**{k:"string:"+hex(k) for k in constants},**roots}
    # Look for references to enclosing aligned records as well as exact slots. These are candidates.
    for root in roots:
        for va in range(root-0x60,root+0x68,8): targets.setdefault(va,"neighbor:"+hex(root))
    ptrs=[]
    for s in e.data_regions():
        chunk=raw[s["off"]:s["off"]+s["size"]]
        for va in list(constants)+list(roots):
            p=chunk.find(struct.pack("<Q",va))
            while p>=0:
                slot=s["addr"]+p
                if slot%8==0: ptrs.append(dict(slot=hex(slot),target=hex(va),section=s["name"])); targets.setdefault(slot,"indirect:"+hex(va))
                p=chunk.find(struct.pack("<Q",va),p+1)
    pages={x&~4095 for x in targets}
    refs=[]; calls=collections.Counter(); funcs=[0x2A02B0,0x7DEFC0,0x3160690,0x2CD73BC,0x2CD7418,0x2CD6CC8]
    for s in e.text_regions():
        chunk=raw[s["off"]:s["off"]+s["size"]]; words=memoryview(chunk[:len(chunk)//4*4]).cast("I")
        for i,w in enumerate(words):
            pc=s["addr"]+4*i
            if w&0x7c000000==0x14000000:
                dst=pc+4*m.signed(w&0x3ffffff,26)
                if dst in funcs: calls[hex(dst)]+=1
            adr=m.decode_adr(w,pc)
            if adr and adr[1] in targets: refs.append(dict(pc=hex(pc),target=hex(adr[1]),label=targets[adr[1]],kind="ADR"))
            adrp=m.decode_adrp(w,pc)
            if not adrp or adrp[1] not in pages: continue
            reg,page=adrp
            for gap in range(1,13):
                if i+gap>=len(words): break
                w2=words[i+gap]; add=m.decode_add_x_imm(w2)
                va=None; kind=None
                if add and add[1]==reg: va=page+add[2];kind="ADRP_ADD"
                elif w2&0xffc00000==0xf9400000 and (w2>>5)&31==reg: va=page+8*((w2>>10)&4095);kind="ADRP_LDR"
                if va in targets: refs.append(dict(pc=hex(pc),use_pc=hex(pc+4*gap),target=hex(va),label=targets[va],kind=kind))
    windows=[]
    for va in funcs:
        b=read(va,0x300); ins=[]
        for i in dis.disasm(b,va):
            ins.append(dict(va=hex(i.address),op=i.mnemonic,args=i.op_str,bytes=i.bytes.hex()))
        windows.append(dict(anchor=hex(va),instructions=ins))
        print("FUNCTION",hex(va))
        for i in ins[:100]: print(i["va"],i["op"],i["args"])
    for r in ptrs: print("POINTER",json.dumps(r))
    for r in refs[:120]: print("XREF",json.dumps(r))
    summary=dict(elf_sha256=sha,constants=len(strings),neighbor_qwords=len(neighborhoods),pointer_candidates=len(ptrs),xref_candidates=len(refs),direct_branch_counts=dict(calls),windows=len(windows),selector_confirmed=False,registration_confirmed=False)
    for name,rows in [("strings",strings),("registration-neighborhood",neighborhoods),("pointer-candidates",ptrs),("xref-candidates",refs),("functions",windows)]:
        (a.out/(name+".jsonl")).write_text("".join(json.dumps(r)+"\n" for r in rows))
    (a.out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print("SUMMARY",json.dumps(summary))
if __name__=="__main__": main()
