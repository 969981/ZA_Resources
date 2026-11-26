#!/usr/bin/env python3
"""Audit native material record boundaries, known v9 layouts and unresolved tails."""
import argparse, collections, hashlib, importlib.util, json, math, struct, subprocess
from pathlib import Path
spec=importlib.util.spec_from_file_location("layout",Path(__file__).with_name("Audit-ZA-UILayout.py"))
layout=importlib.util.module_from_spec(spec);spec.loader.exec_module(layout)
pack=layout.pack
# Candidate bit layout cross-checked against observed v9 records; unknown bits stay raw.
FIELDS=[("maps",0,2),("srt",2,2),("coord",4,2),("combiner",6,3),("alpha",9,1),("blend",10,1),("blend_rgba",12,1),("rotate",14,1),("projection",15,2),("font_color",17,1),("detailed",19,1),("user",20,1),("extension",21,1),("vector",22,2),("brick",24,2)]
MASK=sum(((1<<w)-1)<<s for _,s,w in FIELDS)
def material(b,e="<"):
    u=layout.reader(b,e);layout.need(b,0,32)
    flags=u("I",28);counts={n:(flags>>s)&((1<<w)-1) for n,s,w in FIELDS}
    row=dict(name=layout.string(b,0,28),size=len(b),flags=flags,field_counts_candidate=counts,unknown_bits=flags&~MASK,record_sha256=pack.sha(b),status="PARTIAL",blocks=[])
    if b[32:36]!=bytes([0,2,4,8]):
        row.update(reason="unsupported color header",unparsed_tail_hex=b[32:].hex());return row
    layout.need(b,0,44);row["colors"]=[list(b[36:40]),list(b[40:44])];row["color_header"]=b[32:36].hex();off=44
    def take(name,n):
        nonlocal off
        layout.need(b,off,n);d=b[off:off+n];row["blocks"].append(dict(kind=name,offset=off,size=n,raw_hex=d.hex()));off+=n;return d
    def many(name,n,count):return [take(name,n) for _ in range(count)]
    try:
        row["maps"]=[]
        for _ in range(counts["maps"]):
            x=take("map",4);row["maps"].append(dict(texture_index=struct.unpack_from(e+"H",x)[0],u_options=x[2],v_options=x[3],u_wrap_candidate=x[2]&3,u_filter_candidate=(x[2]>>2)&3,v_wrap_candidate=x[3]&3,v_filter_candidate=(x[3]>>2)&3))
        if counts["extension"]:
            row.update(reason="texture extension offsets not verified",unparsed_tail_hex=b[off:].hex());return row
        row["srt"]=[]
        for x in many("srt",20,counts["srt"]):
            a=struct.unpack(e+"5f",x)
            if not all(math.isfinite(v) for v in a):raise ValueError("nonfinite SRT")
            row["srt"].append(dict(translation=list(a[:2]),rotation=a[2],scale=list(a[3:])))
        # 16 bytes for coord records, 4 for simple combiner: observed size fits, not shader semantics.
        row["coord_raw"]=[x.hex() for x in many("coord_candidate",16,counts["coord"])]
        row["combiner_raw"]=[x.hex() for x in many("combiner_candidate",4,counts["combiner"])]
        row["alpha_compare_raw"]=[x.hex() for x in many("alpha_candidate",8,counts["alpha"])]
        row["blend"]=[dict(equation=x[0],src=x[1],dst=x[2],logic=x[3]) for x in many("blend_candidate",4,counts["blend"])]
        if counts["blend_rgba"] or row["unknown_bits"]:
            row.update(reason="unknown or combined blend bits",unparsed_tail_hex=b[off:].hex());return row
        row["rotate_raw"]=[x.hex() for x in many("rotate_candidate",12,counts["rotate"])]
        row["projection_raw"]=[x.hex() for x in many("projection_candidate",20,counts["projection"])]
        row["font_color_raw"]=[x.hex() for x in many("font_color_candidate",8,counts["font_color"])]
        row["unparsed_tail_hex"]=b[off:].hex()
        if off==len(b) and not any(counts[k] for k in ("detailed","user","vector","brick")):row["status"]="BOUNDARY_FIT_CANDIDATE"
        else:row["reason"]="unparsed material extension or tail"
    except Exception as ex:row.update(reason=str(ex),unparsed_tail_hex=b[off:].hex())
    return row
def audit(out,ref):
    out.mkdir(parents=True,exist_ok=True);counts=collections.Counter();flags=collections.Counter();seen=set();groups=collections.defaultdict(list)
    for logical,path,oid in pack.tracked(ref):
        if logical.endswith(".arc"):groups[logical].append((path,oid))
    with (out/"materials.jsonl").open("w",encoding="utf-8") as f,(out/"errors.jsonl").open("w",encoding="utf-8") as err:
        for logical,entries in sorted(groups.items()):
            counts["arc_paths"]+=1
            if len(entries)!=1 or entries[0][0]!=logical:counts["unrestored"]+=1;continue
            path,oid=entries[0]
            if oid in seen:counts["alias_paths"]+=1;continue
            seen.add(oid)
            try:
                raw=(pack.ROOT/path).read_bytes()
                if hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()!=oid:raise ValueError("blob mismatch")
                for mem,b in pack.sarc(raw):
                    if b[:4]!=b"FLYT":continue
                    try:
                        for tag,off,s,e in layout.sections(b):
                            if tag!="mat1":continue
                            u=layout.reader(s,e);n=u("H",8);layout.need(s,12,4*n);offsets=[u("I",12+4*i) for i in range(n)]+[len(s)]
                            for i,(a,z) in enumerate(zip(offsets,offsets[1:])):
                                if a<12+4*n or z<a or z>len(s):raise ValueError("material bounds")
                                try:
                                    d=material(s[a:z],e);counts["material_records"]+=1;counts[d["status"]]+=1
                                    flags[(d["flags"],d["size"],d["status"])]+=1
                                    f.write(json.dumps(dict(path=path,blob=oid,member=mem["name"],index=i,offset=off+a,**d),allow_nan=False)+"\n")
                                except Exception as ex:counts["material_errors"]+=1;err.write(json.dumps(dict(path=path,member=mem["name"],index=i,error=str(ex)))+"\n")
                    except Exception as ex:counts["layout_errors"]+=1;err.write(json.dumps(dict(path=path,member=mem["name"],error=str(ex)))+"\n")
            except Exception as ex:counts["arc_errors"]+=1;err.write(json.dumps(dict(path=path,error=str(ex)))+"\n")
    result=dict(source_commit=ref,counts=dict(counts),flag_size_histogram=[dict(flags=f"0x{a:08X}",size=b,status=c,count=n) for (a,b,c),n in flags.most_common()],shader_verified=False,flags_semantics_verified=False)
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(dict(counts=dict(counts),top_flag_sizes=result["flag_size_histogram"][:20]),indent=2))
    if not counts["material_records"]:raise SystemExit("no materials")
def self_test():
    b=bytearray(88);b[:2]=b"x\0";struct.pack_into("<I",b,28,0x415);b[32:36]=bytes([0,2,4,8]);b[40:44]=bytes([255]*4);struct.pack_into("<HBB5f",b,44,3,6,6,.5,.5,0,2,2);b[84:88]=bytes([1,4,1,0])
    r=material(bytes(b));assert r["status"]=="BOUNDARY_FIT_CANDIDATE" and r["srt"][0]["scale"]==[2,2] and r["blend"][0]["src"]==4 and r["maps"][0]["texture_index"]==3
    assert material(bytes(b[:-1]))["status"]=="PARTIAL"
    print("material record boundary, SRT and blend fixtures passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--ref",default="HEAD");p.add_argument("--out",type=Path,default=Path(".za-work/ui-material"));a=p.parse_args()
    if a.self_test:self_test();return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("output must be local")
    ref=subprocess.check_output(["git","rev-parse",a.ref+"^{commit}"],text=True).strip();audit(a.out,ref)
if __name__=="__main__":main()
