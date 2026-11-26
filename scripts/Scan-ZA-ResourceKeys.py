#!/usr/bin/env python3
"""Scan aligned static resource keys in SHA-pinned ZA main ELF. Exact byte hash, length, VA checks."""
import argparse, bisect, collections, hashlib, importlib.util, json, re, struct
from pathlib import Path
SEED=0xcbf29ce484222645
PRIME=0x100000001b3
MASK=(1<<64)-1
def native_hash(b):
    h=SEED
    for x in b: h=((h^x)*PRIME)&MASK
    return h
def classify(s):
    s=s.lower()
    if "/icon/" in s and "ik_pokemon/" in s: return "pokemon_icon"
    if "icon_item" in s: return "item_icon"
    if "icon_donut" in s: return "donut_icon"
    if "pokemon_icon_offset" in s: return "pokemon_icon_offset"
    if "poke_resource_table" in s or "trpmcatalog" in s: return "pokemon_catalog"
    if "pokeicon" in s or "poke_icon" in s or "pokemonicon" in s or "switch_icon" in s or "p_icon_00" in s: return "ui_pokemon_node"
    if "icon_type" in s or "type_icon" in s: return "type_icon"
    if "icon" in s: return "other_icon"
    if any(x in s for x in ("ribbon","medal","badge","mark","achievement")): return "mark_or_badge_candidate"
    if s.endswith((".bntx",".bflim",".png",".dds",".bflan",".bflyt",".arc",".truiv")): return "other_image_or_ui"
    if "/" in s: return "other_path"
    return "other_string"
def write(out,name,rows):
    (out/name).write_text("".join(json.dumps(r,ensure_ascii=True)+"\n" for r in rows),encoding="utf8")
def main():
    p=argparse.ArgumentParser(); p.add_argument("--out",type=Path,default=Path(".za-work/resource-keys")); a=p.parse_args(); out=a.out; out.mkdir(parents=True,exist_ok=True)
    raw=Path("Unpack/v2.0.2/exefs/main/main.elf").read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if sha!="470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d": raise ValueError("unexpected ELF")
    spec=importlib.util.spec_from_file_location("elfhelper",Path(__file__).with_name("Probe-ZA-Lua-Host-ELF.py")); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m); e=m.ELF64(raw)
    sections=sorted([s for s in e.sections if s["flags"]&2 and s["stype"]!=8 and s["size"]],key=lambda s:s["addr"])
    starts=[s["addr"] for s in sections]
    def region(va):
        i=bisect.bisect_right(starts,va)-1
        if i>=0:
            s=sections[i]
            if va<s["addr"]+s["size"]: return s
    def read(va,n):
        s=region(va)
        if not s or va+n>s["addr"]+s["size"]: return None
        off=s["off"]+va-s["addr"];return raw[off:off+n]
    # Every file-backed load segment, aligned VA; includes executable segments.
    # Records must be contained in one segment; strings must be in allocated file-backed sections.
    relocs={}
    for s in sections:
        if s["stype"]==4 and s["entsize"]>=24:
            for off in range(s["off"],s["off"]+s["size"]-23,s["entsize"]):
                va,info,add=struct.unpack_from("<QQq",raw,off)
                if info&0xffffffff==1027 and info>>32==0: relocs[va]=add
    rows=[]; seen=set(); counters=collections.Counter(); byseg=[]
    for s in e.segments:
        n=0; pos=(-s["addr"])%8
        for i in range(pos,s["size"]-23,8):
            va=s["addr"]+i; off=s["off"]+i
            if va in seen:continue
            h,ptr,l=struct.unpack_from("<QQQ",raw,off)
            if not 0<l<=4096:continue
            counters["bounded_length"]+=1
            p2=relocs.get(va+8,ptr)
            if p2<=0:continue
            b=read(p2,l+1)
            if not b or b[-1]!=0 or 0 in b[:-1]:continue
            counters["terminated_string"]+=1
            if native_hash(b[:-1])!=h:continue
            counters["hash_match"]+=1
            try: txt=b[:-1].decode("utf-8")
            except UnicodeDecodeError:txt=None
            section=region(va)
            rows.append(dict(record_va=hex(va),record_file_offset=hex(off),record_section=section["name"] if section else s["name"],hash=f"{h:016x}",string_va=hex(p2),pointer_raw=hex(ptr),pointer_kind="RELA_RELATIVE" if va+8 in relocs else "RAW",length=l,text=txt,bytes_hex=b[:-1].hex() if txt is None else None,category=classify(txt) if txt else "non_utf8"))
            seen.add(va); n+=1
        byseg.append(dict(segment=s["name"],bytes=s["size"],aligned_slots=max(0,(s["size"]-24-pos)//8+1),matches=n))
    rows.sort(key=lambda r:int(r["record_va"],16))
    assert {0x3e0aca0,0x3e27bc8,0x3e27be0}.issubset({int(r["record_va"],16) for r in rows})
    write(out,"resource-keys.jsonl",rows)
    relevant=[r for r in rows if r["category"] not in ("other_string","other_path","non_utf8")]
    write(out,"image-key-candidates.jsonl",relevant)
    hashes=collections.defaultdict(set)
    for r in rows:hashes[r["hash"]].add(r["text"] if r["text"] is not None else r["bytes_hex"])
    collisions=[dict(hash=k,values=sorted(v)) for k,v in hashes.items() if len(v)>1]
    write(out,"hash-collisions.jsonl",collisions)
    print("SAMPLES",json.dumps([r for r in relevant if r["category"] in ("pokemon_icon","pokemon_icon_offset","pokemon_catalog","type_icon","item_icon","ui_pokemon_node")][:50]))
    # Trace selected record base addresses, not all generic string consumers.
    selected={int(r["record_va"],16):r for r in relevant if r["category"] in ("pokemon_icon","pokemon_icon_offset","pokemon_catalog","type_icon","item_icon","ui_pokemon_node")}
    selected.update({0x3e27be0:next(r for r in rows if r["record_va"]=="0x3e27be0")})
    pages={k&~4095 for k in selected}; refs=[]
    for s in e.text_regions():
        chunk=raw[s["off"]:s["off"]+s["size"]]; words=memoryview(chunk[:len(chunk)//4*4]).cast("I")
        for i,w in enumerate(words):
            pc=s["addr"]+i*4; adr=m.decode_adr(w,pc)
            if adr and adr[1] in selected:refs.append(dict(pc=hex(pc),target=hex(adr[1]),kind="ADR",text=selected[adr[1]]["text"]))
            ap=m.decode_adrp(w,pc)
            if not ap or ap[1] not in pages:continue
            reg,page=ap
            # Nearby pair candidate, register liveness not established.
            for gap in range(1,9):
                if i+gap>=len(words):break
                add=m.decode_add_x_imm(words[i+gap])
                if add and add[1]==reg and page+add[2] in selected:
                    t=page+add[2];refs.append(dict(pc=hex(pc),use_pc=hex(pc+4*gap),target=hex(t),kind="ADRP_ADD_CANDIDATE",text=selected[t]["text"]))
    write(out,"image-key-xrefs.jsonl",refs)
    from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
    dis=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
    windows=[]
    for va in (0x1B4E240,0x421C,0x2D69DB4,0x2D69D00):
        b=read(va,0x300); ins=[]
        for i in dis.disasm(b,va):ins.append(dict(va=hex(i.address),op=i.mnemonic,args=i.op_str,bytes=i.bytes.hex()))
        windows.append(dict(anchor=hex(va),instructions=ins))
        print("FUNCTION",hex(va))
        for i in ins[:100]: print(i["va"],i["op"],i["args"])
    write(out,"functions.jsonl",windows)
    # Decode actual ADRP+ADD constants referenced in type path helper.
    const=[]
    for va in range(0x2D69DB4,0x2D69DB4+0x100,4):
        w=struct.unpack("<I",read(va,4))[0]; ap=m.decode_adrp(w,va)
        if not ap:continue
        for gap in range(1,9):
            q=va+gap*4; add=m.decode_add_x_imm(struct.unpack("<I",read(q,4))[0])
            if add and add[1]==ap[0]:
                t=ap[1]+add[2]; s=region(t)
                if not s:continue
                b=read(t,min(192,s["addr"]+s["size"]-t)).split(b"\0",1)[0]
                if b and all(32<=x<127 for x in b):const.append(dict(pc=hex(va),use_pc=hex(q),target=hex(t),text=b.decode("ascii")))
    write(out,"type-path-constants.jsonl",const)
    types=[]; lookup={int(r["record_va"],16):r for r in rows}
    for i in range(40):
        r=lookup.get(0x3e27be0+i*24)
        if not r:break
        types.append(dict(index=i,**r))
    write(out,"type-table-contiguous.jsonl",types)
    print("TYPE_CONSTANTS",json.dumps(const));print("TYPE_TABLE",json.dumps(types))
    print("XREFS",json.dumps(refs[:80]))
    summary=dict(elf_sha256=sha,scope="aligned 24-byte candidates across all file-backed PT_LOAD segments; nonempty NUL strings <=4096 bytes; allocated section targets; RELATIVE relocations supported",segments=byseg,filters=dict(counters),records=len(rows),unique_hashes=len(hashes),unique_strings=len({(r["text"],r["bytes_hex"]) for r in rows}),hash_collisions=len(collisions),categories=dict(collections.Counter(r["category"] for r in rows)),sections=dict(collections.Counter(r["record_section"] for r in rows)),image_candidates=len(relevant),xref_candidates=len(refs),type_table_contiguous_records=len(types),runtime_verified=False)
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print("SUMMARY",json.dumps(summary))
if __name__=="__main__":main()
