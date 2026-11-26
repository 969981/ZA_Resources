#!/usr/bin/env python3
"""Probe native FlatBuffers resource catalog slots without inventing schema names."""
import argparse, hashlib, json, re, struct
from pathlib import Path
from collections import Counter
DEFAULT=Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/ik_pokemon/catalog/catalog/poke_resource_table.trpmcatalog")
def inspect(b):
    def u(fmt,o): return struct.unpack_from("<"+fmt,b,o)[0]
    def field(o,i):
        v=o-u("i",o); size=u("H",v)
        if v<0 or size<4 or size%2 or v+size>len(b): raise ValueError("invalid vtable")
        pos=v+4+2*i
        if pos+2>v+size: return None
        off=u("H",pos)
        return o+off if off else None
    def ptr(o):
        if o is None: return None
        p=o+u("I",o)
        if not o<p<len(b): raise ValueError("invalid pointer")
        return p
    def string(o):
        p=ptr(o)
        if p is None: return None
        n=u("I",p)
        if n>4096 or p+4+n>=len(b) or b[p+4+n]!=0: raise ValueError("invalid string")
        return b[p+4:p+4+n].decode("utf-8")
    root=u("I",0); vec=ptr(field(root,1)); n=u("I",vec)
    if n>100000 or vec+4+4*n>len(b): raise ValueError("invalid vector")
    rows=[]
    for i in range(n):
        o=ptr(vec+4+4*i)
        slots={str(k):string(field(o,k)) for k in (1,2,3,6,8)}
        model=slots["1"]
        m=re.fullmatch(r"(pm\d{4})/(pm\d{4}_\d+_\d+)/[^/]+\.trmdl",model or "")
        rows.append(dict(catalog_index=i,table_offset=o,resource_slots=slots,resource_directory="/".join(m.groups()) if m else None,field_0_raw=None if field(o,0) is None else u("I",field(o,0)),species=None,form=None,gender=None,shiny=None))
    return rows
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--catalog",type=Path,default=DEFAULT); p.add_argument("--candidates",type=Path); p.add_argument("--out",type=Path,default=Path(".za-work/bntx")); a=p.parse_args()
    b=a.catalog.read_bytes(); rows=inspect(b); a.out.mkdir(parents=True,exist_ok=True)
    dirs={}
    for r in rows:
        if r["resource_directory"]: dirs.setdefault(r["resource_directory"],[]).append(r["catalog_index"])
    (a.out/"catalog-records.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
    joined=[]
    if a.candidates:
        for line in a.candidates.read_text().splitlines():
            r=json.loads(line); parts=r["path"].split("/")
            key="/".join(parts[2:4]); ids=dirs.get(key,[])
            r.update(resource_directory=key,catalog_indices=ids,catalog_join_status="DIRECTORY_MATCH" if ids else "NO_DIRECTORY_MATCH")
            joined.append(r)
        (a.out/"pokemon-catalog-join.jsonl").write_text("".join(json.dumps(r)+"\n" for r in joined))
    summary=dict(source_sha256=hashlib.sha256(b).hexdigest(),catalog_records=len(rows),resource_directories=len(dirs),duplicate_directories=sum(len(v)>1 for v in dirs.values()),slot_presence={str(k):sum(r["resource_slots"][str(k)] is not None for r in rows) for k in (1,2,3,6,8)},join_counts=dict(Counter(r["catalog_join_status"] for r in joined)),native_icon_selector_confirmed=False,semantic_mapping_confirmed=False)
    (a.out/"catalog-summary.json").write_text(json.dumps(summary,indent=2)+"\n"); print(json.dumps(summary,indent=2))
if __name__=="__main__": main()
