#!/usr/bin/env python3
"""Read-only ZA v9 capture texture and FLTS keyframe audit, with explicit evidence."""
import argparse, collections, hashlib, importlib.util, json, math, re, struct, subprocess
from pathlib import Path
spec=importlib.util.spec_from_file_location("layout",Path(__file__).with_name("Audit-ZA-UILayout.py"))
layout=importlib.util.module_from_spec(spec);spec.loader.exec_module(layout)
pack=layout.pack
def ctl(s,e):
    u=layout.reader(s,e);n=u("H",8);end=12+48*n;layout.need(s,12,48*n);out=[]
    for i in range(n):
        a=12+48*i; x,y=u("I",a),u("I",a+4)
        if min(x,y)<end:raise ValueError("capture name points inside records")
        scale=u("f",a+44)
        if not math.isfinite(scale):raise ValueError("capture scale")
        out.append(dict(index=i,offset=a,name=layout.string(s,x),source_pane=layout.string(s,y),raw_hex=s[a:a+48].hex(),scale_candidate=scale))
    return out
def bounded_name(s,a,n):
    layout.need(s,a,n)
    # Fixed-width character arrays need not contain NUL; record this separately.
    raw=s[a:a+n];return raw.split(b"\0",1)[0].decode("utf-8"),b"\0" not in raw
def capture(b):
    captures=[];textures=[];fonts=[];panes=collections.defaultdict(list);secs=[];errors=[]
    for tag,off,s,e in layout.sections(b):
        u=layout.reader(s,e)
        try:
            if tag=="ctl1":
                for r in ctl(s,e):captures.append(dict(section_offset=off,**r))
            elif tag in ("txl1","fnl1"):
                names=layout.name_table(s,e,u("H",8),12)
                if tag=="txl1":textures.extend(names)
                else:fonts.extend(names)
            elif tag in ("pan1","pic1","txt1","wnd1","bnd1","prt1","cpt1"):
                name,full=bounded_name(s,12,24);p=dict(name=name,tag=tag,offset=off,full_width_name=full)
                if tag=="txt1":
                    layout.need(s,0,96); p.update(size=list(u("2f",76)),font_index_candidate=u("H",90),material_index_candidate=u("H",88),message_key_candidates=[m.decode("ascii") for m in re.findall(rb"msg_[A-Za-z0-9_]+",s)])
                panes[name].append(p)
            secs.append(dict(tag=tag,offset=off,size=len(s)))
        except Exception as ex:errors.append(dict(tag=tag,offset=off,error=str(ex)))
    for c in captures:
        c["listed_in_txl1"]=c["name"] in textures
        c["pane_candidates"]=panes.get(c["source_pane"],[])
        c["status"]="CAPTURE_SOURCE_UNIQUE" if len(c["pane_candidates"])==1 else "CAPTURE_SOURCE_AMBIGUOUS" if c["pane_candidates"] else "CAPTURE_SOURCE_MISSING"
    for ps in panes.values():
        for p in ps:
            idx=p.get("font_index_candidate")
            if idx is not None:p["font_name_candidate"]=fonts[idx] if idx<len(fonts) else None
    return dict(captures=captures,textures=textures,fonts=fonts,sections=secs,errors=errors)
def animation(b):
    out=[];errors=[];tags=collections.Counter()
    for tag,off,s,e in layout.sections(b):
        if tag!="pai1":continue
        u=layout.reader(s,e);frames=u("H",8);ne=u("H",14);table=u("I",16);layout.need(s,table,4*ne)
        for i in range(ne):
            a=u("I",table+i*4)
            try:
                layout.need(s,a,32);name,_=bounded_name(s,a,28);tc=s[a+28];ty=s[a+29];layout.need(s,a+32,tc*4)
                if ty not in (0,1):raise ValueError("unsupported target type")
                for j in range(tc):
                    g=a+u("I",a+32+j*4);layout.need(s,g,8);kind=s[g:g+4].decode("ascii")
                    if kind!="FLTS":continue
                    tags[kind]+=1;nn=u("I",g+4);layout.need(s,g+8,4*nn)
                    for k in range(nn):
                        q=g+u("I",g+8+k*4);layout.need(s,q,12);dt=u("H",q+2);nk=u("H",q+4);ko=q+u("I",q+8)
                        r=dict(target=name,target_type=ty,tag_offset=off+g,offset=off+q,index=s[q],property=s[q+1],data_type=dt,key_count=nk,animation_frames=frames,keys=[])
                        if dt in (1,2):
                            step=8 if dt==1 else 12;layout.need(s,ko,nk*step)
                            for x in range(nk):
                                p=ko+x*step
                                if dt==2:
                                    f,v,t=u("3f",p)
                                    if not all(math.isfinite(z) for z in (f,v,t)):raise ValueError("nonfinite Hermite key")
                                    r["keys"].append(dict(frame=f,value=v,tangent=t))
                                else:
                                    f=u("f",p)
                                    if not math.isfinite(f):raise ValueError("nonfinite step key")
                                    r["keys"].append(dict(frame=f,value_raw=u("H",p+4),padding=u("H",p+6)))
                            r["status"]="PARSED_KEYS"
                        else:r["status"]="UNSUPPORTED_KEY_TYPE"
                        r["strict_frames"]=all(x["frame"]<y["frame"] for x,y in zip(r["keys"],r["keys"][1:]))
                        out.append(r)
            except Exception as ex:errors.append(dict(offset=off+a,error=str(ex)))
    return out,errors,tags
def hermite(keys,frame):
    if not keys:raise ValueError("empty keys")
    if any(a["frame"]>=b["frame"] for a,b in zip(keys,keys[1:])):raise ValueError("non-strict key order")
    if frame<=keys[0]["frame"]:return keys[0]["value"]
    if frame>=keys[-1]["frame"]:return keys[-1]["value"]
    for a,b in zip(keys,keys[1:]):
        if a["frame"]<=frame<=b["frame"]:
            d=b["frame"]-a["frame"];t=(frame-a["frame"])/d
            return (2*t**3-3*t*t+1)*a["value"]+(t**3-2*t*t+t)*d*a["tangent"]+(-2*t**3+3*t*t)*b["value"]+(t**3-t*t)*d*b["tangent"]
def audit(out,ref,missing_path=None):
    out.mkdir(parents=True,exist_ok=True);counts=collections.Counter();props=collections.Counter();sources=set();missing=set();missing_names=set();matched=set();missing_records=[]
    if missing_path:
        for line in missing_path.open(encoding="utf-8"):
            x=json.loads(line)
            if x["status"]=="MISSING":missing.add((x["blob"],x["layout"],x["name"]));missing_names.add(x["name"]);missing_records.append((x["blob"],x["layout"],x["name"]))
    groups=collections.defaultdict(list)
    for logical,path,oid in pack.tracked(ref):
        if logical.endswith(".arc"):groups[logical].append((path,oid))
    with (out/"captures.jsonl").open("w",encoding="utf-8") as cf,(out/"flts.jsonl").open("w",encoding="utf-8") as af,(out/"errors.jsonl").open("w",encoding="utf-8") as ef:
        def emit(f,r):f.write(json.dumps(r,ensure_ascii=True,allow_nan=False)+"\n")
        for logical,entries in sorted(groups.items()):
            counts["arc_paths"]+=1
            if len(entries)!=1 or entries[0][0]!=logical:counts["unrestored"]+=1;continue
            path,oid=entries[0]
            if oid in sources:counts["aliases"]+=1;continue
            sources.add(oid)
            try:
                raw=(pack.ROOT/path).read_bytes()
                if hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()!=oid:raise ValueError("blob mismatch")
                for m,b in pack.sarc(raw):
                    if b[:4] not in (b"FLYT",b"FLAN"):continue
                    base=dict(path=path,blob=oid,member=m["name"])
                    try:
                        if b[:4]==b"FLYT":
                            counts["flyt"]+=1;d=capture(b)
                            for x in d["captures"]:
                                counts["capture_records"]+=1;counts[x["status"]]+=1
                                if x["listed_in_txl1"]:counts["capture_in_txl1"]+=1
                                k=(oid,m["name"],x["name"])
                                if k in missing:matched.add(k)
                                emit(cf,dict(**base,**x,fonts=d["fonts"]))
                            for ex in d["errors"]:counts["section_errors"]+=1;emit(ef,dict(**base,**ex))
                        else:
                            counts["flan"]+=1;tracks,errors,tags=animation(b);counts["flts_tags"]+=tags["FLTS"]
                            for x in tracks:
                                counts["flts_tracks"]+=1;counts["flts_keys"]+=len(x["keys"]);counts["flts:"+x["status"]]+=1;props[(x["index"],x["property"],x["data_type"])]+=1
                                if not x["strict_frames"]:counts["non_strict_frames"]+=1
                                if x["data_type"]==2 and x["keys"] and x["strict_frames"]:
                                    t=(x["keys"][0]["frame"]+x["keys"][-1]["frame"])/2;x["midpoint_candidate"]=dict(frame=t,value=hermite(x["keys"],t))
                                emit(af,dict(**base,**x))
                            for ex in errors:counts["animation_errors"]+=1;emit(ef,dict(**base,**ex))
                    except Exception as ex:counts["member_errors"]+=1;emit(ef,dict(**base,error=str(ex)))
            except Exception as ex:counts["arc_errors"]+=1;emit(ef,dict(path=path,error=str(ex)))
    result=dict(source_commit=ref,counts=dict(counts),missing_input_rows=len(missing_records),missing_input_distinct_names=len(missing_names),matched_missing_rows=sum(k in matched for k in missing_records),matched_missing_names=len({k[2] for k in matched}),unmatched_missing_names=sorted({k[2] for k in missing if k not in matched}),property_histogram=[dict(index=i,property=p,data_type=d,count=n) for (i,p,d),n in props.most_common()],runtime_render_verified=False)
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,indent=2))
    if not counts["capture_records"] or not counts["flts_tracks"]:raise SystemExit("no capture/FLTS evidence")
def self_test():
    s=bytearray(72);s[:4]=b"ctl1";struct.pack_into("<IHHII",s,4,len(s),1,0,60,66);s[60:66]=b"x_D\0\0\0";s[66:72]=b"pane\0\0";struct.pack_into("<f",s,56,1)
    assert ctl(bytes(s),"<")[0]["source_pane"]=="pane"
    k=[dict(frame=0,value=-.8,tangent=.0533333333333333),dict(frame=30,value=.8,tangent=.0533333333333333)]
    assert abs(hermite(k,15))<1e-9 and abs(hermite(k,7.5)+.4)<1e-9
    assert bounded_name(b"abcd",0,4)==("abcd",True)
    a=bytearray(100);struct.pack_into("<HHHHI",a,0,30,0,0,1,20);struct.pack_into("<I",a,12,24);a[16:20]=b"mat\0";a[44]=1;a[45]=1;struct.pack_into("<I",a,48,36);a[52:56]=b"FLTS";struct.pack_into("<II",a,56,1,12);struct.pack_into("<BBHHHI",a,64,1,1,2,2,0,12);struct.pack_into("<6f",a,76,0,-.8,.053333333,30,.8,.053333333)
    sec=b"pai1"+struct.pack("<I",8+len(a))+a;blob=b"FLAN"+struct.pack("<HHIIHH",0xfeff,20,0x09000000,20+len(sec),1,0)+sec
    tracks,errors,tags=animation(blob);assert not errors and tags["FLTS"]==1 and len(tracks[0]["keys"])==2 and abs(hermite(tracks[0]["keys"],15))<1e-7
    print("capture offsets, fixed-width names and Hermite fixtures passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--ref",default="HEAD");p.add_argument("--out",type=Path,default=Path(".za-work/ui-dynamic"));p.add_argument("--missing",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("local output only")
    ref=subprocess.check_output(["git","rev-parse",a.ref+"^{commit}"],text=True).strip();audit(a.out,ref,a.missing)
if __name__=="__main__":main()
