#!/usr/bin/env python3
"""ZA v9 FLYT/FLAN static reference audit; no rendering or inferred IDs."""
import argparse, collections, importlib.util, json, math, struct, subprocess
from pathlib import Path
spec=importlib.util.spec_from_file_location("pack",Path(__file__).with_name("Build-ZAImageResources.py"))
pack=importlib.util.module_from_spec(spec); spec.loader.exec_module(pack)
def need(b,o,n):
    if o<0 or n<0 or o+n>len(b): raise ValueError("out of bounds")
def reader(b,e):
    def read(f,o):
        n=struct.calcsize(e+f); need(b,o,n); a=struct.unpack_from(e+f,b,o)
        return a[0] if len(a)==1 else a
    return read
def string(b,o,end=None):
    end=len(b) if end is None else end
    if not 0<=o<end<=len(b): raise ValueError("string bounds")
    z=b.find(b"\0",o,end)
    if z<0: raise ValueError("unterminated string")
    return b[o:z].decode("utf-8")
def sections(b):
    if len(b)<20 or b[:4] not in (b"FLYT",b"FLAN"): raise ValueError("magic")
    e={b"\xff\xfe":"<",b"\xfe\xff":">"}.get(bytes(b[4:6]))
    if not e: raise ValueError("BOM")
    u=reader(b,e); h=u("H",6); n=u("H",16)
    if h<20 or u("I",12)!=len(b) or u("I",8)!=0x09000000: raise ValueError("unsupported header/version")
    for i in range(n):
        need(b,h,8); size=u("I",h+4)
        if size<8: raise ValueError("section size")
        need(b,h,size); yield b[h:h+4].decode("ascii"),h,b[h:h+size],e; h+=size
    if h!=len(b): raise ValueError("trailing bytes")
def name_table(b,e,count,base,limit=None):
    u=reader(b,e); limit=len(b) if limit is None else limit
    need(b,base,count*4)
    return [string(b,base+u("I",base+i*4),limit) for i in range(count)]
def flyt(b):
    tex=[]; mats=[]; pics=[]; panes=[]; sec=[]; stack=[]; last=None
    for tag,off,s,e in sections(b):
        u=reader(s,e); sec.append(dict(tag=tag,offset=off,size=len(s)))
        if tag=="txl1": tex=name_table(s,e,u("H",8),12)
        elif tag=="mat1":
            n=u("H",8); need(s,12,n*4)
            offsets=[u("I",12+4*i) for i in range(n)]+[len(s)]
            for i,(a,z) in enumerate(zip(offsets,offsets[1:])):
                if a<12+4*n or z-a<44 or z>len(s): raise ValueError("material bounds")
                flags=u("I",a+28); count=flags&3
                if a+44+4*count>z: raise ValueError("texture map bounds")
                maps=[dict(texture_index=u("H",a+44+4*j),sampler_raw=s[a+46+4*j:a+48+4*j].hex()) for j in range(count)]
                mats.append(dict(index=i,name=string(s,a,a+28),flags=flags,offset=off+a,size=z-a,color_words=[u("I",a+36),u("I",a+40)],texture_maps=maps,raw_sha256=pack.sha(s[a:z])))
        elif tag in ("pan1","pic1","txt1","wnd1","bnd1","prt1"):
            need(s,0,84); name=string(s,12,36); last=len(panes)
            pane=dict(index=last,name=name,tag=tag,offset=off,parent=stack[-1] if stack else None,flags=s[8],alpha=s[10],transform=list(u("10f",44)))
            panes.append(pane)
            if tag=="pic1":
                need(s,0,104); count=s[102]; need(s,104,count*32)
                uv=[list(u("8f",104+32*j)) for j in range(count)]
                if any(not math.isfinite(x) for v in uv for x in v): raise ValueError("nonfinite UV")
                pics.append(dict(pane_index=last,name=name,offset=off,material_index=u("H",100),vertex_colors=s[84:100].hex(),uv=uv))
        elif tag=="pas1":
            if last is None: raise ValueError("orphan pas1")
            stack.append(last)
        elif tag=="pae1":
            if not stack: raise ValueError("orphan pae1")
            stack.pop()
    if stack: raise ValueError("unclosed pane stack")
    for m in mats:
        for t in m["texture_maps"]:
            i=t["texture_index"]; t["name"]=tex[i] if i<len(tex) else None
    for p in pics:
        i=p["material_index"]; p["material"]=mats[i]["name"] if i<len(mats) else None
        p["texture_names"]=[t["name"] for t in mats[i]["texture_maps"]] if i<len(mats) else []
        p["uv_kind"]="FULL" if p["uv"]==[[0,0,1,0,0,1,1,1]] else "OTHER"
    return dict(sections=sec,textures=tex,materials=mats,panes=panes,pictures=pics)
def flan(b):
    sec=[]; targets=[]; patterns=[]; errors=[]; info=[]
    for tag,off,s,e in sections(b):
        u=reader(s,e); sec.append(dict(tag=tag,offset=off,size=len(s)))
        if tag=="pat1":
            info.append(dict(order=u("H",8),group_count=u("H",10),name=string(s,u("I",12)),group_offset=u("I",16)))
        if tag!="pai1": continue
        frames=u("H",8); nt=u("H",12); ne=u("H",14); table=u("I",16)
        tex=name_table(s,e,nt,20,table) if nt else []
        need(s,table,ne*4); info.append(dict(frames=frames,flags=s[10],texture_names=tex,target_count=ne))
        for i in range(ne):
            a=u("I",table+4*i)
            try:
                need(s,a,32); name=string(s,a,a+28); count=s[a+28]; ty=s[a+29]
                need(s,a+32,4*count); target=dict(name=name,type=ty,offset=off+a,tags=[]); targets.append(target)
                if ty not in (0,1):
                    errors.append(dict(offset=off+a,error="unsupported target type",type=ty)); continue
                for j in range(count):
                    g=a+u("I",a+32+4*j); need(s,g,8); kind=s[g:g+4].decode("ascii"); n=u("I",g+4); need(s,g+8,n*4)
                    target["tags"].append(dict(tag=kind,offset=off+g,entry_count=n))
                    if kind!="FLTP": continue
                    for k in range(n):
                        q=g+u("I",g+8+4*k); need(s,q,12); dt=u("H",q+2); nk=u("H",q+4); ko=q+u("I",q+8)
                        row=dict(target=name,target_type=ty,tag=kind,offset=off+q,index=s[q],property=s[q+1],data_type=dt,key_count=nk,keys=[])
                        if dt==1:
                            need(s,ko,nk*8)
                            for x in range(nk):
                                f=ko+x*8; frame=u("f",f); val=u("H",f+4)
                                if not math.isfinite(frame): raise ValueError("nonfinite frame")
                                row["keys"].append(dict(frame=frame,value_raw=val,padding_raw=u("H",f+6),texture_candidate=tex[val] if val<len(tex) else None))
                        else: row["unsupported_key_type"]=True
                        patterns.append(row)
            except Exception as ex: errors.append(dict(offset=off+a,error=str(ex)))
    return dict(sections=sec,info=info,targets=targets,patterns=patterns,errors=errors)
def audit(out,ref):
    out.mkdir(parents=True,exist_ok=True)
    counts=collections.Counter(); groups=collections.defaultdict(list); cache={}
    for logical,path,oid in pack.tracked(ref):
        if logical.endswith(".arc"): groups[logical].append((path,oid))
    with (out/"sources.jsonl").open("w",encoding="utf-8") as src,(out/"layouts.jsonl").open("w",encoding="utf-8") as lay,(out/"animations.jsonl").open("w",encoding="utf-8") as ani,(out/"combined-textures.jsonl").open("w",encoding="utf-8") as tx,(out/"errors.jsonl").open("w",encoding="utf-8") as err:
        def emit(f,v): f.write(json.dumps(v,ensure_ascii=True,allow_nan=False)+"\n")
        for logical,entries in sorted(groups.items()):
            counts["arc_paths"]+=1
            if len(entries)!=1 or entries[0][0]!=logical:
                emit(src,dict(path=logical,status="UNRESTORED",entries=entries)); counts["unrestored"]+=1; continue
            path,oid=entries[0]
            if oid in cache:
                emit(src,dict(path=path,blob=oid,status=cache[oid],alias=True)); counts["alias_paths"]+=1; continue
            counts["unique_raw_arc"]+=1; status="PARSED"
            try:
                raw=(pack.ROOT/path).read_bytes()
                import hashlib
                if hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()!=oid: raise ValueError("blob mismatch")
                members=list(pack.sarc(raw)); names=collections.defaultdict(list)
                for m,b in members:
                    if b[:4]!=b"BNTX": continue
                    if (m["name"] or "").rsplit("/",1)[-1]!="__Combined.bntx": continue
                    counts["combined_containers"]+=1
                    try:
                        for t in pack.bntx.parse(b):
                            counts["combined_brti"]+=1; key=dict(member=m["name"],index=t["index"],name=t["name"])
                            names[t["name"]].append(key); emit(tx,dict(path=path,blob=oid,member=m,texture=t))
                    except Exception as ex: counts["combined_errors"]+=1; emit(err,dict(path=path,member=m,error=str(ex)))
                for m,b in members:
                    if b[:4] not in (b"FLYT",b"FLAN"): continue
                    kind="flyt" if b[:4]==b"FLYT" else "flan"; counts[kind+"_members"]+=1
                    try:
                        d=flyt(b) if kind=="flyt" else flan(b)
                        if kind=="flyt":
                            counts["txl_refs"]+=len(d["textures"]); counts["mat_records"]+=len(d["materials"])
                            d["texture_joins"]=[dict(name=n,candidates=names.get(n,[])) for n in d["textures"]]
                            for j in d["texture_joins"]: counts["txl_join_"+("exact" if len(j["candidates"])==1 else "ambiguous" if j["candidates"] else "missing")]+=1
                            for p in d["pictures"]: counts["pic_"+p["uv_kind"]]+=1
                        else:
                            counts["animation_targets"]+=len(d["targets"]); counts["pattern_tracks"]+=len(d["patterns"]); counts["animation_partial_errors"]+=len(d["errors"])
                            for t in d["targets"]:
                                for g in t["tags"]: counts["tag:"+g["tag"]]+=1
                        emit(lay if kind=="flyt" else ani,dict(path=path,blob=oid,member=m,**d)); counts[kind+"_parsed"]+=1
                    except Exception as ex: counts[kind+"_errors"]+=1; emit(err,dict(path=path,member=m,error=str(ex)))
            except Exception as ex: status="FAILED"; counts["arc_errors"]+=1; emit(err,dict(path=path,error=str(ex)))
            cache[oid]=status; emit(src,dict(path=path,blob=oid,status=status,alias=False))
    summary=dict(source_commit=ref,counts=dict(counts),runtime_selector_verified=False,atlas_crop_verified=False,material_shader_verified=False)
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8"); print(json.dumps(summary,indent=2))
    if not counts["flyt_parsed"] or not counts["combined_brti"]: raise SystemExit("no layout evidence")
def self_test():
    def section(tag,p): return tag+struct.pack("<I",8+len(p))+p
    def file(m,*ss):
        body=b"".join(ss); return m+struct.pack("<HHIIHH",0xfeff,20,0x09000000,20+len(body),len(ss),0)+body
    tx=section(b"txl1",struct.pack("<HHI",1,0,4)+b"tex\0")
    mat=bytearray(48); mat[:4]=b"mat\0"; struct.pack_into("<I",mat,28,1)
    mt=section(b"mat1",struct.pack("<HHI",1,0,16)+mat)
    pic=bytearray(128); pic[4:8]=b"pic\0"; pic[94]=1; struct.pack_into("<8f",pic,96,0,0,1,0,0,1,1,1)
    d=flyt(file(b"FLYT",tx,mt,section(b"pic1",pic)))
    assert d["pictures"][0]["texture_names"]==["tex"] and d["pictures"][0]["uv_kind"]=="FULL"
    a=bytearray(84); struct.pack_into("<HHHHI",a,0,1,0,0,1,20); struct.pack_into("<I",a,12,24); a[16:20]=b"mat\0"; a[44]=1; a[45]=1; struct.pack_into("<I",a,48,36); a[52:56]=b"FLTP"; struct.pack_into("<II",a,56,1,12); struct.pack_into("<BBHHHI",a,64,0,0,1,1,0,12); struct.pack_into("<fHH",a,76,0,0,0)
    d=flan(file(b"FLAN",section(b"pai1",a))); assert len(d["patterns"])==1 and not d["errors"],d
    print("synthetic FLYT reference and FLAN pattern fixtures passed")
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--self-test",action="store_true"); p.add_argument("--ref",default="HEAD"); p.add_argument("--out",type=Path,default=Path(".za-work/ui-layout")); a=p.parse_args()
    if a.self_test: self_test(); return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()): p.error("output must be local .za-work")
    ref=subprocess.check_output(["git","rev-parse",a.ref+"^{commit}"],text=True).strip(); audit(a.out,ref)
if __name__=="__main__": main()
