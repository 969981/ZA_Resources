#!/usr/bin/env python3
"""Native catalog key, personal table, config and icon crosswalk. No semantic gender/shiny guesses."""
import argparse, collections, hashlib, importlib.util, json, math, re, struct
from pathlib import Path

V=Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual")
CAT=V/"ik_pokemon/catalog/catalog/poke_resource_table.trpmcatalog"
PERSONAL=V/"avalon/data/personal_array.bin"
DATA=V/"ik_pokemon/data"
def sha(b): return hashlib.sha256(b).hexdigest()
class FB:
    def __init__(self,b): self.b=b
    def u(self,fmt,o):
        if o<0 or o+struct.calcsize("<"+fmt)>len(self.b): raise ValueError("out of bounds")
        return struct.unpack_from("<"+fmt,self.b,o)[0]
    def table(self,o):
        v=o-self.u("i",o); n=self.u("H",v); size=self.u("H",v+2)
        if n<4 or n%2 or size<4 or v+n>len(self.b) or o+size>len(self.b): raise ValueError("bad vtable")
        offsets=[self.u("H",v+4+i) for i in range(0,n-4,2)]
        if any(x and not 4<=x<size for x in offsets): raise ValueError("bad slot")
        return v,size,offsets
    def field(self,o,i):
        _,_,a=self.table(o)
        return o+a[i] if i<len(a) and a[i] else None
    def scalar(self,o,i,fmt,default=0):
        p=self.field(o,i)
        return default if p is None else self.u(fmt,p)
    def ptr(self,p):
        if p is None: return None
        q=p+self.u("I",p)
        if not p<q<len(self.b): raise ValueError("invalid offset")
        return q
    def string(self,p):
        q=self.ptr(p)
        if q is None: return None
        n=self.u("I",q)
        if n>4096 or q+4+n>=len(self.b) or self.b[q+4+n]!=0: raise ValueError("bad string")
        return self.b[q+4:q+4+n].decode("utf-8")
    def rows(self,slot):
        root=self.u("I",0); p=self.ptr(self.field(root,slot)); n=self.u("I",p)
        if n>100000 or p+4+4*n>len(self.b): raise ValueError("bad vector")
        return [self.ptr(p+4+4*i) for i in range(n)]
def config(b):
    f=FB(b); o=f.u("I",0); v,size,offsets=f.table(o); slots={}
    starts=sorted(set(x for x in offsets if x))
    for i,off in enumerate(offsets):
        if not off: continue
        end=next((x for x in starts if x>off),size); raw=b[o+off:o+end]
        value=dict(offset=off,raw_hex=raw.hex(),span=len(raw))
        if len(raw)==1: value["u8_candidate"]=raw[0]
        if len(raw)==4:
            fv=struct.unpack("<f",raw)[0]
            value["f32_candidate"]=fv if math.isfinite(fv) else None
        slots[str(i)]=value
    return dict(root_offset=o,vtable_offset=v,object_size=size,vtable_slots=len(offsets),slots=slots)
def personal(b):
    f=FB(b); rows={}
    for i,o in enumerate(f.rows(0)):
        p=f.field(o,0); g=f.field(o,10)
        if p is None: raise ValueError("missing personal detail")
        species,form,national=(f.u("H",p+2*k) for k in range(3))
        key=(species,form)
        if key in rows: raise ValueError("duplicate personal key")
        rows[key]=dict(row=i,species_internal=species,form=form,national_raw=national,present=bool(f.scalar(o,1,"B")),gender_group=f.u("B",g) if g is not None else None,gender_ratio=f.u("B",g+1) if g is not None else None)
    return rows
def catalog(b,per):
    f=FB(b); rows=[]
    for i,o in enumerate(f.rows(1)):
        k=f.ptr(f.field(o,0)); slots={str(j):f.string(f.field(o,j)) for j in (1,2,3,6,8)}
        key=[f.scalar(k,0,"H"),f.scalar(k,1,"B"),f.scalar(k,2,"B")]
        model=slots["1"]; match=re.fullmatch(r"(pm\d{4})/(pm\d{4}_\d+_\d+)/[^/]+\.trmdl",model or "")
        rows.append(dict(index=i,table_offset=o,key_table_offset=k,key_raw=key,key_slot_offsets=f.table(k)[2],personal=per.get(tuple(key[:2])),resource_dir="/".join(match.groups()) if match else None,resource_number=int(match.group(1)[2:]) if match else None,slots=slots,gender_semantic=None,shiny_semantic=None))
    return rows
def write(out,name,rows):
    (out/name).write_text("".join(json.dumps(x,ensure_ascii=True)+"\n" for x in rows),encoding="utf-8")
def load_decoder():
    spec=importlib.util.spec_from_file_location("za_bntx",Path(__file__).with_name("Decode-ZA-BNTX.py"))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def main():
    a=argparse.ArgumentParser(description=__doc__); a.add_argument("--out",type=Path,default=Path(".za-work/pokemon-selector")); a=a.parse_args(); out=a.out; out.mkdir(parents=True,exist_ok=True)
    cb,pb=CAT.read_bytes(),PERSONAL.read_bytes(); per=personal(pb); rows=catalog(cb,per)
    assert len(rows)==637 and len(per)==1445 and sum(p["present"] for p in per.values())==594
    assert len({tuple(r["key_raw"]) for r in rows})==637
    dirs=collections.defaultdict(list)
    for r in rows: dirs[r["resource_dir"]].append(r)
    cfgs=[]; icons=[]; errors=[]; decoder=load_decoder()
    for file in sorted(DATA.glob("*/*/*.trpokecfg")):
        rel=file.relative_to(DATA).as_posix()
        try:
            b=file.read_bytes(); cfgs.append(dict(path=rel,sha256=sha(b),bytes=len(b),**config(b)))
        except Exception as e: errors.append(dict(path=rel,stage="config",error=str(e)))
    for file in sorted(DATA.glob("*/*/icon/*.bntx")):
        rel=file.relative_to(DATA).as_posix(); key="/".join(rel.split("/")[:2]); matches=dirs.get(key,[])
        try:
            b=file.read_bytes()
            for t in decoder.parse(b):
                name=t["name"]; m=re.fullmatch(r"pm(\d{4})_(\d+)_(\d+)_(\d+)_(\d+)",name)
                icons.append(dict(path=rel,texture=name,format=t["format_code"],width=t["width"],height=t["height"],source_sha256=sha(b),catalog_indices=[r["index"] for r in matches],catalog_keys=[r["key_raw"] for r in matches],personal_candidates=[r["personal"] for r in matches],name_tokens=list(map(int,m.groups())) if m else None,filename_matches_brti=file.stem==name,gender=None,shiny=None,status="DIRECTORY_JOIN_CANDIDATE" if matches else "UNMATCHED"))
        except Exception as e: errors.append(dict(path=rel,stage="brti",error=str(e)))
    write(out,"catalog-keys.jsonl",rows); write(out,"personal-keys.jsonl",per.values()); write(out,"config-fields.jsonl",cfgs); write(out,"icon-crosswalk.jsonl",icons); write(out,"errors.jsonl",errors)
    matched=[r for r in rows if r["personal"]]; present={k for k,p in per.items() if p["present"]}; covered={tuple(r["key_raw"][:2]) for r in matched if r["personal"]["present"]}
    summary=dict(catalog_sha256=sha(cb),personal_sha256=sha(pb),catalog_records=len(rows),personal_records=len(per),personal_present_forms=len(present),catalog_personal_matches=len(matched),catalog_personal_present_records=sum(r["personal"]["present"] for r in matched),catalog_distinct_present_forms=len(covered),present_forms_without_catalog=sorted(present-covered),resource_number_mismatch=sum(r["resource_number"]!=r["personal"]["national_raw"] for r in matched),catalog_key_slot2_hist=dict(collections.Counter(r["key_raw"][2] for r in rows)),config_paths=len(cfgs),config_unique_sha256=len({r["sha256"] for r in cfgs}),config_slot_presence=dict(collections.Counter(k for r in cfgs for k in r["slots"])),icon_brti_count=len(icons),icon_join_counts=dict(collections.Counter(r["status"] for r in icons)),errors=len(errors),selector_proven=False,shiny_proven=False)
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n"); print(json.dumps(summary,indent=2))
    if not cfgs or not icons: raise SystemExit("no configs/icons checked")
if __name__=="__main__": main()
