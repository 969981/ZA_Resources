#!/usr/bin/env python3
"""V2.1 representative batch, strict geometry gates, source-backed catalog and isolated failures."""
import argparse, collections, hashlib, importlib.util, json, math, shutil, struct, subprocess
from pathlib import Path
import numpy as np
def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v2=load("ZANativeModelExporterV2");v1=v2.v1;geo=v2.geo;audit=v2.audit;FB=geo.FB
TARGET={1,3,6,25,450,479,718}
def checked(path,paths):
    f=audit.V/path
    b=f.read_bytes() if f.is_file() else subprocess.check_output(["git","cat-file","blob",paths[path]])
    if hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()!=paths[path]:raise ValueError("blob mismatch")
    return b
def selection(paths,all_models=False):
    catpath=audit.native.CAT.relative_to(audit.V).as_posix()
    perpath=audit.native.PERSONAL.relative_to(audit.V).as_posix()
    per=audit.native.personal(checked(perpath,paths));cat=audit.native.catalog(checked(catpath,paths),per)
    groups=collections.defaultdict(list)
    for c in cat:
        p=c["personal"]
        if not p or (not all_models and p["national_raw"] not in TARGET):continue
        raw=c["slots"]["1"]
        if raw:groups["ik_pokemon/data/"+raw].append(dict(catalog_index=c["index"],key_raw=c["key_raw"],national_raw=p["national_raw"],gender_raw=p["gender_group"],gender_ratio_raw=p["gender_ratio"],mmt_raw=c["slots"]["2"]))
    if all_models:
        for p in sorted(paths):
            if p.startswith("ik_pokemon/data/") and p.endswith(".trmdl"):groups.setdefault(p,[])
    return dict(sorted(groups.items()))
def read_mesh(m,b,sk):
    rows=geo.mesh_pair(m,b,sk);f=FB(m);g=FB(b);root=f.u("I",0);br=g.u("I",0);result=[];ambiguous=0
    for t,u,row in zip(f.tables(root,1),g.tables(br,1),rows):
        if row["issues"]:raise ValueError("mesh issues "+str(row["issues"]))
        if len(row["declarations"])!=1:raise ValueError("multiple declarations")
        d=row["declarations"][0];candidate=d.get("binding_candidate")
        if candidate not in ("DIRECT_RIG_ONLY","BOTH_POSSIBLE"):raise ValueError("binding "+str(candidate))
        if any(d["weights"].get(k,0) for k in ("invalid_weight","invalid_joint_value","zero_weight_vertices","nonunit_weight_vertices","direct_rig_invalid","direct_not_in_palette")):raise ValueError("unsafe skin weights")
        if candidate=="BOTH_POSSIBLE":
            pal=row["palette_raw"]
            if any(pal[k]!=k for k in d["used_raw_joint_ids"]):ambiguous+=1
        vs=g.tables(u,1)
        if len(vs)!=1 or len(d["strides"])!=1:raise ValueError("multiple vertex streams")
        data=g.bytes_vector(vs[0],0);stride=d["strides"][0];n=d["vertex_count"]
        def attr(usage,types):
            found=[a for a in d["attrs"] if a["usage"]==usage]
            if len(found)!=1 or found[0]["layer"]!=0 or found[0]["type"] not in types:raise ValueError("unsupported attribute "+str(usage))
            return found[0]
        po=attr(1,{51});no=attr(2,{43,51,54});uv=attr(6,{48,43});jo=attr(7,{22,39});we=attr(8,{20,39,54})
        def read(a,i):
            o=i*stride+a["offset"]
            if a["usage"]==7 and a["type"]==39:return struct.unpack_from("<4H",data,o)
            return geo.unpack(data,o,a["type"])
        positions=[];normals=[];uvs=[];joints=[];weights=[]
        for i in range(n):
            p=read(po,i);q=np.array(read(no,i)[:3]);norm=np.linalg.norm(q);tex=read(uv,i)[:2];j=read(jo,i);w=read(we,i);s=sum(w)
            if not all(math.isfinite(x) for x in (*p,*q,*tex,*w)) or norm<1e-6 or s<=0 or any(x<0 for x in w):raise ValueError("invalid vertex")
            if len(j)!=4 or len(w)!=4 or any(k>=len(sk["bones"]) or k<0 for k,x in zip(j,w) if x>0):raise ValueError("invalid joint")
            positions.append(p);normals.append((q/norm).tolist());uvs.append(tex);joints.append([int(k) if x else 0 for k,x in zip(j,w)]);weights.append([x/s for x in w])
        typ=f.scalar(t,2,"I");idx=g.bytes_vector(g.tables(u,0)[0],0)
        if typ not in (0,1,2):raise ValueError("index format")
        ix=np.frombuffer(idx,dtype={0:"u1",1:"<u2",2:"<u4"}[typ]);parts=[]
        for p in row["parts"]:
            if not p["index_valid"] or p["count"]%3 or p["max_index"] is None or p["max_index"]>65535:raise ValueError("unsupported triangle range")
            parts.append((p["material"],ix[p["offset"]:p["offset"]+p["count"]].astype("<u2")))
        result.append(dict(name=row["name"],positions=positions,normals=normals,uv=uvs,joints=joints,weights=weights,parts=parts))
    if ambiguous:raise ValueError("ambiguous direct/local mapping differs on used joints: "+str(ambiguous))
    return result
def batch_one(model,keys,paths,out):
    def get(p):return checked(p,paths)
    def resolve(source,raw):return v1.resolve(source,raw,paths)
    mdl=audit.parse(get(model),".trmdl");sp=resolve(model,mdl["skeleton"]);sk=geo.skeleton(get(sp))
    local,joints,ib,bind=v1.bind_pose(sk)
    if bind["max_identity_error"]>v1.EPS:raise ValueError("native bind failure")
    if not mdl["meshes"]:raise ValueError("no mesh")
    mp=resolve(model,mdl["meshes"][0]);mb=get(mp);f=FB(mb);bp=resolve(mp,f.txt(f.u("I",0),2))
    shapes=read_mesh(mb,get(bp),sk);used={name for sh in shapes for name,_ in sh["parts"]}
    refs={c["mmt_raw"] for c in keys if c["mmt_raw"]}
    if len(refs)>1:raise ValueError("multiple catalog TRMMT references")
    mmp="ik_pokemon/data/"+next(iter(refs)) if refs else model.removesuffix(".trmdl")+".trmmt"
    variants=audit.parse(get(mmp),".trmmt")["variants"];cache={};report=[];exports=[];missing=[]
    for variant in ("normal","rare"):
        match=[x for x in variants if x["name"]==variant]
        if not match:missing.append(variant);continue
        if len(match)!=1 or len(match[0]["material_files"])!=1:raise ValueError("multiple variant material files")
        matpath=resolve(mmp,match[0]["material_files"][0]);materials=[m for m in geo.material(get(matpath)) if m["name"] in used]
        if {m["name"] for m in materials}!=used or len(materials)!=len(used):raise ValueError("missing or duplicate LayerMask materials")
        flat=out/(variant+".flat.glb");dest=out/(Path(model).stem+"_"+variant+".glb")
        v1.export(flat,shapes,sk,local,joints,ib,materials,variant)
        exports.append(v2.textured(flat,dest,matpath,variant,paths,cache,report));flat.unlink()
    if "normal" in missing:raise ValueError("normal variant absent")
    if len(exports)==2:
        gs=[v2.parse_glb(out/e["file"]) for e in exports];ends=[min(g.doc["bufferViews"][i["bufferView"]]["byteOffset"] for i in g.doc["images"]) for g in gs]
        if gs[0].data[:ends[0]]!=gs[1].data[:ends[1]]:raise ValueError("variant geometry mismatch")
        tex=[{x["name"]:x["rgba_sha256"] for x in e["textures"] if x["name"].endswith("_baseColor")} for e in exports]
        different=tex[0]!=tex[1]
    else:different=None
    audit.write(out,"source-mips",report)
    return dict(model=model,keys=keys,bind_pose=bind,mesh=mp,buffer=bp,skeleton=sp,missing_variants=missing,exports=exports,unique_source_textures=len(report),decoded_mips=sum(len(r["mips"]) for r in report),basecolor_differs=different,geometry_identical=True if len(exports)==2 else None,visual_parity=False,status="EXPORTED_CANDIDATE")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--out",type=Path,default=Path(".za-work/ZANativeModelExporterV21"));p.add_argument("--all",action="store_true",help="explicit opt-in to all native TRMDL, with strict gates");p.add_argument("--self-test",action="store_true");a=p.parse_args()
    if a.self_test:v2.self_test();return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()) or a.out.resolve()==Path(".za-work").resolve():p.error("local output only")
    if a.out.exists() and any(a.out.iterdir()):p.error("empty output required")
    a.out.mkdir(parents=True,exist_ok=True);paths=audit.tree();selected=selection(paths,a.all)
    if not a.all and (len(selected)!=21 or sum(map(len,selected.values()))!=23):raise ValueError("representative catalog baseline changed")
    # Keep same Git blob verification when v2 resolves shared texture paths via sparse checkout.
    audit.checked=checked
    results=[]
    for model,keys in selected.items():
        out=a.out/"models"/Path(model).parent.name/Path(model).stem;out.mkdir(parents=True,exist_ok=True)
        try:
            row=batch_one(model,keys,paths,out)
            (out/"summary.json").write_text(json.dumps(row,indent=2,allow_nan=False)+"\n")
        except Exception as e:
            shutil.rmtree(out);row=dict(model=model,keys=keys,status="REJECTED",error=type(e).__name__+": "+str(e),visual_parity=False)
        results.append(row);print("MODEL",json.dumps({k:v for k,v in row.items() if k not in ("exports","keys")}),flush=True)
    audit.write(a.out,"batch-results",results)
    ok=[r for r in results if r["status"]=="EXPORTED_CANDIDATE"]
    s=dict(source_commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),selected_models=len(selected),catalog_keys=sum(map(len,selected.values())),exported_models=len(ok),rejected_models=len(results)-len(ok),glbs=sum(len(r["exports"]) for r in ok),normal_rare_pairs=sum(len(r["exports"])==2 for r in ok),decoded_mips=sum(r["decoded_mips"] for r in ok),rejections=dict(collections.Counter(r["error"] for r in results if r["status"]=="REJECTED")),visual_parity=False)
    (a.out/"summary.json").write_text(json.dumps(s,indent=2)+"\n");print("BATCH_SUMMARY",json.dumps(s))
    if not any(r["model"]==v1.SAMPLE for r in ok):raise SystemExit("Bulbasaur regression")
if __name__=="__main__":main()
