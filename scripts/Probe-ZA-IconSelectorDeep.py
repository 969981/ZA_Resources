#!/usr/bin/env python3
"""Read-only ZA resource numbering, icon-offset table and ELF candidate audit."""
import argparse, collections, hashlib, importlib.util, json, math, struct, re
from pathlib import Path
def load(name, file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def write(out,name,rows):
    (out/name).write_text("".join(json.dumps(r,ensure_ascii=True)+"\n" for r in rows),encoding="utf-8")
def assets(out):
    m=load("cfg","Probe-ZA-PokemonConfig.py")
    per=m.personal(m.PERSONAL.read_bytes()); cat=m.catalog(m.CAT.read_bytes(),per)
    forward=collections.defaultdict(set); reverse=collections.defaultdict(set)
    for r in cat:
        a=r["key_raw"][0]; b=r["resource_number"]; forward[a].add(b); reverse[b].add(a)
    records=[dict(species_key=k,resource_numbers=sorted(v),catalog_indices=[r["index"] for r in cat if r["key_raw"][0]==k]) for k,v in sorted(forward.items())]
    write(out,"species-resource-crosswalk.jsonl",records)
    fpath=m.V/"world/exl/pokemon_icon_offset/pokemon_icon_offset/pokemon_icon_offset.bin"
    b=fpath.read_bytes(); f=m.FB(b); rows=[]
    for i,o in enumerate(f.rows(0)):
        v,size,offsets=f.table(o)
        fields={}
        for k in range(7):
            p=f.field(o,k)
            if p is None: fields[str(k)]=None; continue
            raw=f.u("I",p)
            val=f.u("f",p) if k>=3 else raw
            fields[str(k)]=dict(offset=p-o,raw_hex=f"{raw:08x}",value=val if not isinstance(val,float) or math.isfinite(val) else None)
        key=[f.scalar(o,k,"I") for k in range(3)]
        matches=[r for r in cat if r["key_raw"][:2]==key[1:3]]
        rows.append(dict(index=i,table_offset=o,vtable_offset=v,object_size=size,fields=fields,key_candidate=key,catalog_candidates=[r["index"] for r in matches],resource_dirs=sorted({r["resource_dir"] for r in matches}),axes_semantic=None))
    write(out,"pokemon-icon-offset.jsonl",rows)
    pm=[]
    for file in sorted((m.DATA/"pm0770").rglob("*")):
        if not file.is_file() or file.suffix not in (".bntx",".trpokecfg",".trmdl",".trmmt"): continue
        rel=file.relative_to(m.DATA).as_posix()
        if file.suffix==".bntx" and "/icon/" not in rel: continue
        key="/".join(rel.split("/")[:2]); matches=[r for r in cat if r["resource_dir"]==key]
        data=file.read_bytes(); pm.append(dict(path=rel,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),catalog_keys=[r["key_raw"] for r in matches]))
    write(out,"pm0770-resources.jsonl",pm)
    summary=dict(catalog_records=len(cat),species_keys=len(forward),resource_numbers=len(reverse),forward_conflicts={str(k):sorted(v) for k,v in forward.items() if len(v)>1},reverse_conflicts={str(k):sorted(v) for k,v in reverse.items() if len(v)>1},offset_table_sha256=hashlib.sha256(b).hexdigest(),offset_rows=len(rows),offset_serial_ids=[r["key_candidate"][0] for r in rows],offset_fields_present=dict(collections.Counter(k for r in rows for k,v in r["fields"].items() if v is not None)),offset_pair_join_count=sum(bool(r["catalog_candidates"]) for r in rows),offset_unmatched_keys=[r["key_candidate"] for r in rows if not r["catalog_candidates"]],pm0770_paths=len(pm),offset_axis_semantic_proven=False,selector_proven=False)
    (out/"asset-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))
    for r in rows: print("OFFSET",json.dumps(r,separators=(",",":")))
def elf_audit(out):
    from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
    m=load("elfhelper","Probe-ZA-Lua-Host-ELF.py")
    raw=Path("Unpack/v2.0.2/exefs/main/main.elf").read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    if sha!="470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d": raise ValueError("unexpected ELF SHA")
    e=m.ELF64(raw); dis=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
    targets={0x3296760:"UikitPokeIcon",0x32E07A3:"pokemon_icon_offset",0x3288619:"catalog_path",0x326855E:"default_icon_path",0x32D57AB:"pokemon_data_path"}
    pointers=[]
    for s in e.sections:
        if s["stype"]==4 and s["entsize"]>=24:
            for p in range(s["off"],s["off"]+s["size"]-23,s["entsize"]):
                dest,info,add=struct.unpack_from("<QQq",raw,p)
                if add in targets:
                    pointers.append(dict(kind="RELA_ADDEND_MATCH",slot_va=dest,relocation_type=info&0xffffffff,target_va=add,target=targets[add],section=s["name"]))
    for s in e.data_regions():
        chunk=raw[s["off"]:s["off"]+s["size"]]
        for va,name in targets.items():
            needle=struct.pack("<Q",va); p=chunk.find(needle)
            while p>=0:
                if (s["addr"]+p)%8==0: pointers.append(dict(kind="ALIGNED_RAW_POINTER",slot_va=s["addr"]+p,target_va=va,target=name,section=s["name"]))
                p=chunk.find(needle,p+1)
    write(out,"elf-pointer-candidates.jsonl",pointers)
    look=dict(targets)
    for p in pointers: look[p["slot_va"]]="pointer:"+p["target"]
    pages={k&~4095 for k in look}
    refs=[]; calls=[]; entries=(0x2CD6CC8,0x2CD6AD4,0x2CD73BC,0x2CD7418,0x7DEFC0)
    for s in e.text_regions():
        chunk=raw[s["off"]:s["off"]+s["size"]]; words=memoryview(chunk[:len(chunk)//4*4]).cast("I")
        for i,w in enumerate(words):
            pc=s["addr"]+i*4
            if w&0x7c000000==0x14000000:
                dst=pc+4*m.signed(w&0x03ffffff,26)
                if dst in entries: calls.append(dict(pc=pc,target=dst,kind="BL" if w&0x80000000 else "B"))
            adr=m.decode_adr(w,pc)
            if adr and adr[1] in look: refs.append(dict(pc=pc,target=adr[1],name=look[adr[1]],kind="ADR"))
            adr=m.decode_adrp(w,pc)
            if not adr or adr[1] not in pages: continue
            reg,page=adr
            for gap in range(1,9):
                if i+gap>=len(words): break
                w2=words[i+gap]; add=m.decode_add_x_imm(w2)
                if add and add[1]==reg and page+add[2] in look:
                    va=page+add[2]; refs.append(dict(pc=pc,use_pc=pc+4*gap,target=va,name=look[va],kind="ADRP_ADD_CANDIDATE"))
                if w2&0xffc00000==0xf9400000 and ((w2>>5)&31)==reg:
                    va=page+8*((w2>>10)&4095)
                    if va in look: refs.append(dict(pc=pc,use_pc=pc+4*gap,target=va,name=look[va],kind="ADRP_LDR_CANDIDATE"))
    write(out,"elf-deep-xrefs.jsonl",refs); write(out,"elf-direct-branches.jsonl",calls)
    windows=[]
    def window(va,before,after):
        for s in e.text_regions():
            if s["addr"]<=va<s["addr"]+s["size"]:
                lo=max(s["addr"],va-before); hi=min(s["addr"]+s["size"],va+after); p=s["off"]+lo-s["addr"]
                return dict(anchor=hex(va),instructions=[dict(va=hex(i.address),op=i.mnemonic,args=i.op_str,bytes=i.bytes.hex()) for i in dis.disasm(raw[p:p+hi-lo],lo)])
    for va in sorted(set(entries)|{r["pc"] for r in refs}|{r["pc"] for r in calls}):
        w=window(va,0x40,0x300 if va in entries else 0x70)
        if w: windows.append(w)
    write(out,"elf-deep-windows.jsonl",windows)
    summary=dict(elf_sha256=sha,pointer_candidates=len(pointers),xref_candidates=len(refs),direct_branches=len(calls),windows=len(windows),selector_confirmed=False)
    (out/"elf-deep-summary.json").write_text(json.dumps(summary,indent=2)+"\n"); print(json.dumps(summary,indent=2))
    for r in pointers: print("POINTER",json.dumps(r))
    for r in refs: print("XREF",json.dumps(r))
    for r in calls: print("BRANCH",json.dumps(r))
    for w in windows:
        if int(w["anchor"],16) in entries:
            print("WINDOW",w["anchor"])
            for i in w["instructions"]: print(i["va"],i["op"],i["args"])
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--mode",choices=["assets","elf"],required=True); p.add_argument("--out",type=Path,default=Path(".za-work/icon-deep")); a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    (assets if a.mode=="assets" else elf_audit)(a.out)
if __name__=="__main__": main()
