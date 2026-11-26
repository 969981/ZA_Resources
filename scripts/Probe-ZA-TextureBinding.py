#!/usr/bin/env python3
"""Trace ZA texture extension keys and dynamic string-key consumers. Static evidence only."""
import argparse, bisect, collections, hashlib, importlib.util, json, re, struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=Path(".za-work/texture-binding"));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    raw=Path("Unpack/v2.0.2/exefs/main/main.elf").read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    if sha!="470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d":raise ValueError("ELF SHA mismatch")
    spec=importlib.util.spec_from_file_location("elfhelper",Path(__file__).with_name("Probe-ZA-Lua-Host-ELF.py"));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);e=m.ELF64(raw)
    ss=sorted([s for s in e.sections if s["flags"]&2 and s["stype"]!=8 and s["size"]],key=lambda s:s["addr"]); starts=[s["addr"] for s in ss]
    def region(va):
        i=bisect.bisect_right(starts,va)-1
        if i>=0 and va<ss[i]["addr"]+ss[i]["size"]:return ss[i]
        return next((s for s in e.segments if s["addr"]<=va<s["addr"]+s["size"]),None)
    def read(va,n):
        s=region(va)
        if not s or va+n>s["addr"]+s["size"]:return b""
        off=s["off"]+va-s["addr"];return raw[off:off+n]
    def q(va):
        b=read(va,8);return struct.unpack("<Q",b)[0] if len(b)==8 else None
    def h(b):
        v=0xcbf29ce484222645
        for x in b:v=((v^x)*0x100000001b3)&0xffffffffffffffff
        return v
    def cstr(va):
        s=region(va)
        if not s:return None
        b=read(va,min(512,s["addr"]+s["size"]-va)).split(b"\0",1)[0]
        if b and all(32<=x<127 for x in b):return b.decode("ascii")
    def key(va):
        b=read(va,24)
        if len(b)!=24:return None
        v,p,n=struct.unpack("<QQQ",b)
        if not 0<n<=4096:return None
        x=read(p,n+1)
        if len(x)!=n+1 or x[-1]!=0 or 0 in x[:-1] or h(x[:-1])!=v:return None
        return dict(va=hex(va),hash=f"{v:016x}",string_va=hex(p),length=n,text=x[:-1].decode("utf8","replace"))
    def dump(name,rows):
        (a.out/(name+".jsonl")).write_text("".join(json.dumps(r,ensure_ascii=True)+"\n" for r in rows))
    roots=[0x3e28138,0x3e27bc8,0x3e27bb0,0x3e0aca0]; neighbors=[]
    for root in roots:
        for va in range(root-0x180,root+0x188,8):
            r=key(va)
            if r:neighbors.append(dict(root=hex(root),delta=va-root,**r))
    dump("neighbor-keys",neighbors)
    for r in neighbors:print("NEIGHBOR",json.dumps(r))
    # ASCII tokens, including mangled class strings and candidate filename templates.
    pat=re.compile(rb"[ -~]{4,512}")
    tokens=[]
    for s in e.data_regions():
        if s["name"]!=".rodata":continue
        for z in pat.finditer(raw[s["off"]:s["off"]+s["size"]]):
            b=z.group(); low=b.lower()
            if any(x in low for x in (b"uikitpokeicon",b"poke_resource_table",b"ik_pokemon/data/",b"pokemon_icon_offset",b"pm%04",b"pm%0",b"icon_item/",b"/icon/",b".bntx")):
                tokens.append(dict(va=hex(s["addr"]+z.start()),text=b.decode("ascii"),hash=f"{h(b):016x}"))
    dump("texture-strings",tokens)
    for r in tokens[:160]:print("TOKEN",json.dumps(r))
    target={int(r["va"],16):"key:"+r["text"] for r in neighbors}
    for r in neighbors:
        va=int(r["va"],16);target[va+8]="keyptr:"+r["text"];target[va+16]="keylen:"+r["text"]
    for r in tokens:target[int(r["va"],16)]="literal:"+r["text"]
    target[0x3296760]="UikitPokeIcon"; target[0x31ad4ec]=".bntx literal"
    # Exact string/pointer values and relative relocation addends.
    ptrs=[]; indirect={}
    for s in e.data_regions():
        b=raw[s["off"]:s["off"]+s["size"]]
        for i in range((-s["addr"])%8,len(b)-7,8):
            v=struct.unpack_from("<Q",b,i)[0]
            if v in target:
                va=s["addr"]+i;ptrs.append(dict(slot=hex(va),value=hex(v),label=target[v],section=s["name"],kind="RAW_POINTER"));indirect[va]="indirect:"+target[v]
    for s in e.sections:
        if s["stype"]==4 and s["entsize"]>=24:
            for off in range(s["off"],s["off"]+s["size"]-23,s["entsize"]):
                va,info,add=struct.unpack_from("<QQq",raw,off)
                if info&0xffffffff==1027 and info>>32==0 and add in target:
                    ptrs.append(dict(slot=hex(va),value=hex(add),label=target[add],section=s["name"],kind="RELA_RELATIVE"));indirect[va]="indirect:"+target[add]
    dump("pointer-candidates",ptrs)
    target.update({k:v for k,v in indirect.items() if k not in target})
    pages={v&~4095 for v in target}; refs=[];calls=[]; funcs={0x283f0,0x2cd6cc8,0x2cd73bc,0x2cd7418,0x7defc0,0x972470,0x629d8c,0x2a02b0}
    for s in e.text_regions():
        b=raw[s["off"]:s["off"]+s["size"]]; words=memoryview(b[:len(b)//4*4]).cast("I")
        for i,w in enumerate(words):
            pc=s["addr"]+4*i
            if w&0x7c000000==0x14000000:
                dst=pc+4*m.signed(w&0x3ffffff,26)
                if dst in funcs:calls.append(dict(pc=hex(pc),target=hex(dst),kind="BL" if w&0x80000000 else "B"))
            ad=m.decode_adr(w,pc)
            if ad and ad[1] in target:refs.append(dict(pc=hex(pc),target=hex(ad[1]),label=target[ad[1]],kind="ADR"))
            ap=m.decode_adrp(w,pc)
            if not ap or ap[1] not in pages:continue
            reg,page=ap
            for gap in range(1,9):
                if i+gap>=len(words):break
                w2=words[i+gap];add=m.decode_add_x_imm(w2);va=None;kind=None
                if add and add[1]==reg:va=page+add[2];kind="ADRP_ADD_CANDIDATE"
                elif w2&0xffc00000==0xf9400000 and (w2>>5)&31==reg:va=page+8*((w2>>10)&4095);kind="ADRP_LDR_CANDIDATE"
                if va in target:refs.append(dict(pc=hex(pc),use_pc=hex(pc+gap*4),target=hex(va),label=target[va],kind=kind))
    dump("xrefs",refs);dump("calls",calls)
    # Exact 64-bit values in mapped data, and adjacent MOVZ/MOVK constructions
    # in executable sections. Bounded register tracking; candidates, not dataflow proof.
    needles={h(b"UikitPokeIcon"):"UikitPokeIcon",h(b".bntx"):".bntx",h(b"/"):"/",h(b"_"):"_"}
    hash_hits=[]
    for s in e.segments:
        b=raw[s["off"]:s["off"]+s["size"]]
        for val,name in needles.items():
            needle=struct.pack("<Q",val); pos=0
            while True:
                pos=b.find(needle,pos)
                if pos<0:break
                hash_hits.append(dict(kind="raw_u64",va=hex(s["addr"]+pos),hash=f"{val:016x}",name=name,aligned=(s["addr"]+pos)%8==0));pos+=1
    # Match MOVZ + MOVK 64-bit opcodes; skip unrelated words, but invalidate
    # at another MOVZ or any other instruction with same low 5-bit Rd.
    for s in e.text_regions():
        b=raw[s["off"]:s["off"]+s["size"]];words=memoryview(b[:len(b)//4*4]).cast("I")
        for i,w in enumerate(words):
            if w&0xff800000!=0xd2800000:continue
            rd=w&31;value=((w>>5)&0xffff)<<(16*((w>>21)&3))
            if not any(((v>>(16*((w>>21)&3)))&0xffff)==((w>>5)&0xffff) for v in needles):continue
            for j in range(i+1,min(i+13,len(words))):
                ww=words[j]
                if ww&31!=rd:continue
                if ww&0xff800000!=0xf2800000:break
                shift=16*((ww>>21)&3);value=(value&~(0xffff<<shift))|(((ww>>5)&0xffff)<<shift)
                if value in needles:
                    hash_hits.append(dict(kind="MOVZ_MOVK_CANDIDATE",va=hex(s["addr"]+4*i),end_va=hex(s["addr"]+4*j),register=rd,hash=f"{value:016x}",name=needles[value]));break
    dump("hash-hits",hash_hits)
    for r in hash_hits:print("HASH_HIT",json.dumps(r))
    interesting=[r for r in refs if any(t in r["label"].lower() for t in (".bntx","uikitpokeicon","ik_pokemon/data/","poke_resource_table","/icon/","pm%"))]
    for r in interesting[:120]:print("XREF",json.dumps(r))
    for r in ptrs:
        if "uikitpokeicon" in r["label"].lower():print("CLASS_PTR",json.dumps(r))
    dis=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
    windows=[]
    anchors={0x283f0,0x972470,0x629d8c,0x2cd6ad4,0x2cd6cc8,0x2cd6d20,0x2cd73bc,0x2d6af90,0x2bca1d0,0x2cdfff0,0x2d33c84,0x2c0477c,0x2c1655c,0x2c1689c}
    anchors.update(int(r["pc"],16) for r in interesting[:120])
    for va in sorted(anchors):
        s=region(va)
        if not s:continue
        lo=max(s["addr"],va-(0 if va in (0x283f0,0x972470,0x629d8c) else 0x100));hi=min(s["addr"]+s["size"],va+(0x500 if va in (0x972470,0x629d8c) else 0x160));b=read(lo,hi-lo)
        if not b:continue
        ins=[dict(va=hex(i.address),op=i.mnemonic,args=i.op_str,bytes=i.bytes.hex()) for i in dis.disasm(b,lo)]
        windows.append(dict(anchor=hex(va),instructions=ins))
        if va in (0x283f0,0x972470,0x629d8c) or any(int(r["pc"],16)==va and (".bntx" in r["label"] or "UikitPokeIcon" in r["label"]) for r in interesting):
            print("WINDOW",hex(va))
            for i in ins[:180]:print(i["va"],i["op"],i["args"])
    dump("windows",windows)
    constants=[]
    for win in windows:
        ins=win["instructions"]
        for i in range(len(ins)-1):
            pc=int(ins[i]["va"],16);w=int.from_bytes(bytes.fromhex(ins[i]["bytes"]),"little");ap=m.decode_adrp(w,pc)
            if not ap:continue
            w2=int.from_bytes(bytes.fromhex(ins[i+1]["bytes"]),"little");ad=m.decode_add_x_imm(w2)
            if ad and ad[1]==ap[0]:
                va=ap[1]+ad[2];s=region(va);st=cstr(va) if s and s["name"]==".rodata" else None
                if st:constants.append(dict(anchor=win["anchor"],pc=hex(pc),va=hex(va),text=st))
    dump("window-literals",constants)
    for r in constants:print("WINDOW_LITERAL",json.dumps(r))
    summary=dict(elf_sha256=sha,neighbor_keys=len(neighbors),texture_strings=len(tokens),pointer_candidates=len(ptrs),xref_candidates=len(refs),texture_xrefs=len(interesting),direct_calls=dict(collections.Counter(r["target"] for r in calls)),windows=len(windows),hash_hits=len(hash_hits),uikit_hash_hits=sum(r["name"]=="UikitPokeIcon" for r in hash_hits),uikit_type_binding_proven=False,texture_selector_proven=False)
    (a.out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print("SUMMARY",json.dumps(summary))
if __name__=="__main__":main()
