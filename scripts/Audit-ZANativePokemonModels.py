#!/usr/bin/env python3
"""ZA native model structural audit and icon appearance evidence, no guessed runtime IDs."""
import argparse, collections, hashlib, importlib.util, json, math, posixpath, re, sqlite3, subprocess, tempfile
from pathlib import Path
def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
native=load("Probe-ZA-PokemonConfig")
V=native.V
EXT={".trmdl",".trmsh",".trmbf",".trskl",".trmtr",".trmmt"}
def sha(b): return hashlib.sha256(b).hexdigest()
class FB(native.FB):
    def vec(self,o,i,width=4):
        p=self.ptr(self.field(o,i))
        if p is None: return []
        n=self.u("I",p)
        if n>10000000 or p+4+n*width>len(self.b): raise ValueError("bad vector bounds")
        return range(p+4,p+4+n*width,width)
    def tables(self,o,i): return [self.ptr(p) for p in self.vec(o,i)]
    def strings(self,o,i): return [self.string(p) for p in self.vec(o,i)]
    def txt(self,o,i): return self.string(self.field(o,i))
    def bytes_vector(self,o,i):
        p=self.ptr(self.field(o,i))
        if p is None: return b""
        n=self.u("I",p)
        if p+4+n>len(self.b): raise ValueError("bad byte vector")
        return self.b[p+4:p+4+n]
    def floats(self,o,i,n):
        p=self.field(o,i)
        if p is None:return None
        a=[self.u("f",p+4*k) for k in range(n)]
        return [v if math.isfinite(v) else None for v in a]
def parse(b,ext):
    f=FB(b); o=f.u("I",0); v,size,slots=f.table(o)
    result=dict(root=o,vtable=v,object_size=size,slot_offsets=slots,refs=[])
    def ref(role,path):
        if path: result["refs"].append(dict(role=role,raw=path))
    if ext==".trmdl":
        meshes=[f.txt(t,0) for t in f.tables(o,1)]
        sk=f.ptr(f.field(o,2)); skeleton=f.txt(sk,0) if sk is not None else None
        materials=f.strings(o,3)
        for p in meshes:ref("mesh",p)
        ref("skeleton",skeleton)
        for p in materials:ref("material",p)
        ref("trltt",f.txt(o,7))
        lod=[dict(type=f.txt(t,1),indices=[f.scalar(x,0,"I") for x in f.tables(t,0)]) for t in f.tables(o,4)]
        result.update(meshes=meshes,skeleton=skeleton,materials=materials,lods=lod,
            invalid_lod_indices=[i for l in lod for i in l["indices"] if i>=len(meshes)])
    elif ext==".trmsh":
        shapes=[]
        for t in f.tables(o,1):
            access=[]
            for a in f.tables(t,3):
                access.append(dict(strides=[f.scalar(x,0,"I") for x in f.tables(a,1)],
                    attrs=[dict(attribute=f.scalar(x,1,"I"),layer=f.scalar(x,2,"I"),type=f.scalar(x,3,"I"),position=f.scalar(x,4,"I")) for x in f.tables(a,0)]))
            shapes.append(dict(name=f.txt(t,0),polygon_type=f.scalar(t,2,"I"),accessors=access,
                materials=[dict(name=f.txt(x,3),count=f.scalar(x,0,"I"),offset=f.scalar(x,1,"I")) for x in f.tables(t,4)]))
        ref("buffer",f.txt(o,2));result.update(shapes=shapes)
    elif ext==".trmbf":
        buffers=[]
        for t in f.tables(o,1):
            row={}
            for i,name in [(0,"indices"),(1,"vertices")]:
                row[name]=[dict(bytes=len(data),sha256=sha(data)) for x in f.tables(t,i) for data in [f.bytes_vector(x,0)]]
            buffers.append(row)
        result.update(buffers=buffers)
    elif ext==".trskl":
        nodes=[dict(name=f.txt(t,0),parent=f.scalar(t,4,"i",-1),rig=f.scalar(t,5,"i",-1),type=f.scalar(t,7,"I")) for t in f.tables(o,1)]
        bones=f.tables(o,2)
        invalid=[i for i,n in enumerate(nodes) if n["parent"] < -1 or n["parent"]>=len(nodes) or n["parent"]==i]
        cycles=[]
        for i in range(len(nodes)):
            seen=set(); j=i
            while 0<=j<len(nodes):
                if j in seen:cycles.append(i);break
                seen.add(j);j=nodes[j]["parent"]
        result.update(nodes=nodes,bone_count=len(bones),ik_count=len(f.tables(o,3)),invalid_parents=invalid,cycle_nodes=cycles)
    elif ext==".trmtr":
        mats=[]
        for t in f.tables(o,1):
            textures=[dict(name=f.txt(x,0),file=f.txt(x,1),slot=f.scalar(x,2,"I")) for x in f.tables(t,2)]
            for x in textures:ref("texture",x["file"])
            params=[dict(name=f.txt(x,0),rgba=f.floats(x,1,4)) for x in f.tables(t,7)]
            mats.append(dict(name=f.txt(t,0),textures=textures,rgba_parameters=params,
                shaders=[f.txt(x,0) for x in f.tables(t,1)]))
        result.update(materials=mats)
    elif ext==".trmmt":
        variants=[]
        for t in f.tables(o,2):
            name=f.txt(t,0); files=f.strings(t,1)
            for p in files:ref("variant_material",p)
            variants.append(dict(name=name,material_files=files))
        result.update(variants=variants)
    else:raise ValueError("unsupported extension")
    return result
def resolve(source,raw,paths):
    if "\\" in raw or raw.startswith("/") or ":" in raw: return None,"UNSUPPORTED_PATH"
    p=posixpath.normpath(posixpath.join(posixpath.dirname(source),raw))
    if p.startswith("../") or p=="..":return None,"OUTSIDE_ROOT"
    return (p,"EXACT_RELATIVE_PATH") if p in paths else (None,"MISSING_EXACT_PATH")
def compare(a,b):
    def index(x):
        d={}
        for m in x["materials"]:
            if m["name"] in d:raise ValueError("duplicate material name")
            d[m["name"]]=m
        return d
    aa,bb=index(a),index(b); out=[]
    for k in sorted(aa.keys()|bb.keys()):
        x,y=aa.get(k),bb.get(k)
        if x is None or y is None:out.append(dict(material=k,status="ONE_SIDE_ONLY"));continue
        def keyed(m):
            d={}
            for p in m["rgba_parameters"]:
                if p["name"] in d:raise ValueError("duplicate parameter name")
                d[p["name"]]=p["rgba"]
            return d
        u,w=keyed(x),keyed(y)
        out.append(dict(material=k,status="PAIR",texture_lists_equal=x["textures"]==y["textures"],
            rgba_changes=[dict(name=n,normal=u.get(n),rare=w.get(n)) for n in sorted(u.keys()|w.keys()) if u.get(n)!=w.get(n)]))
    return out
def tree():
    root=V.as_posix()+"/"; data=subprocess.check_output(["git","ls-tree","-rz","HEAD","--",V.as_posix()])
    paths={}
    for x in data.split(b"\0"):
        if not x:continue
        m,p=x.split(b"\t",1);mode,kind,oid=m.decode().split();p=p.decode()
        if kind=="blob" and p.startswith(root):paths[p[len(root):]]=oid
    return paths
def checked(path,paths):
    b=(V/path).read_bytes()
    if hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()!=paths[path]:raise ValueError("blob mismatch")
    return b
def write(out,name,rows):
    with (out/(name+".jsonl")).open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=True,allow_nan=False)+"\n")
def icon_audit(db,cat,per,paths):
    dirs=collections.defaultdict(list)
    for c in cat:
        if c["resource_dir"]:dirs[c["resource_dir"]].append(c)
    groups=collections.defaultdict(list); irregular=[]
    for row in db.execute("""SELECT s.path,t.name,t.rgba_sha256,t.width,t.height,t.decode_status FROM source s JOIN ui_texture_source u USING(resource_id) JOIN ui_texture t USING(blob,member_index,texture_index) WHERE s.path LIKE 'ik_pokemon/data/%/icon/%.bntx' ORDER BY s.path,t.name"""):
        path,name,pix,w,h,state=row
        m=re.fullmatch(r"(pm\d{4}_\d+_\d+_\d+)_(0|1)",name)
        d="/".join(path.split("/")[2:4]); cs=dirs[d]
        r=dict(path=path,name=name,pixel_sha256=pix,width=w,height=h,decode_status=state,
            catalog_keys=[c["key_raw"] for c in cs],personal_gender_raw=[c["personal"] for c in cs if c["personal"]],
            gender=None,shiny=None)
        if not m:irregular.append(r);continue
        groups[(d,m.group(1))].append((m.group(2),r))
    pairs=[]
    for (d,stem),rows in sorted(groups.items()):
        a=[r for suffix,r in rows if suffix=="0"];b=[r for suffix,r in rows if suffix=="1"]
        equal=None
        if len(a)==len(b)==1 and a[0]["pixel_sha256"] and b[0]["pixel_sha256"]:
            equal=(a[0]["width"],a[0]["height"],a[0]["pixel_sha256"])==(b[0]["width"],b[0]["height"],b[0]["pixel_sha256"])
        pairs.append(dict(directory=d,stem=stem,zero=a,one=b,pixel_equal=equal,
            status="PAIRED_PIXEL_CANDIDATE" if equal is not None else "UNPAIRED_OR_UNDECODED",
            gender=None,shiny=None))
    return pairs,irregular
def self_test():
    assert resolve("ik_pokemon/data/a/b/a.trmtr","../../../share/x.bntx",{"ik_pokemon/share/x.bntx":"x"})==("ik_pokemon/share/x.bntx","EXACT_RELATIVE_PATH")
    assert resolve("a/b","../../x",{})[1]=="OUTSIDE_ROOT"
    a=dict(materials=[dict(name="body",textures=[1],rgba_parameters=[dict(name="color",rgba=[0,0,0,1])])])
    b=dict(materials=[dict(name="body",textures=[1],rgba_parameters=[dict(name="color",rgba=[1,0,0,1])])])
    assert compare(a,b)[0]["texture_lists_equal"] and len(compare(a,b)[0]["rgba_changes"])==1
    try:parse(b"\0"*16,".trmdl");raise AssertionError("bad root accepted")
    except ValueError:pass
    print("native model bounds, path and rare-material fixtures passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true")
    p.add_argument("--cores",type=Path);p.add_argument("--out",type=Path,default=Path(".za-work/ZANativeModelAudit"))
    a=p.parse_args()
    if a.self_test:self_test();return
    if a.cores is None:p.error("--cores required")
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()) or a.out.resolve()==Path(".za-work").resolve():p.error("local output required")
    if a.out.exists() and any(a.out.iterdir()):p.error("empty output required")
    a.out.mkdir(parents=True,exist_ok=True);paths=tree()
    catpath=native.CAT.relative_to(V).as_posix();perpath=native.PERSONAL.relative_to(V).as_posix()
    per=native.personal(checked(perpath,paths));cat=native.catalog(checked(catpath,paths),per)
    parsed={};errors=[];refs=[];formats=collections.Counter()
    wanted=[p for p in sorted(paths) if p.startswith("ik_pokemon/data/") and Path(p).suffix in EXT]
    for path in wanted:
        ext=Path(path).suffix
        try:
            b=checked(path,paths);r=parse(b,ext);r.update(path=path,sha256=sha(b),bytes=len(b),extension=ext)
            parsed[path]=r;formats[ext]+=1
            for x in r["refs"]:
                target,status=resolve(path,x["raw"],paths);refs.append(dict(source=path,**x,target=target,status=status))
        except Exception as e:errors.append(dict(path=path,error=str(e)))
    rare=[];pair_errors=[]
    for path,r in parsed.items():
        if r["extension"]!=".trmmt":continue
        groups=collections.defaultdict(list)
        for v in r["variants"]:groups[v["name"]].extend(v["material_files"])
        if len(groups["normal"])==len(groups["rare"])==1:
            n,_=resolve(path,groups["normal"][0],paths);q,_=resolve(path,groups["rare"][0],paths)
            if n in parsed and q in parsed:
                try:rare.append(dict(source=path,normal=n,rare=q,materials=compare(parsed[n],parsed[q]),runtime_verified=False))
                except ValueError as e:pair_errors.append(dict(path=path,error=str(e)))
            else:pair_errors.append(dict(path=path,error="variant target not parsed"))
    missing=[]
    for c in cat:
        for slot,raw in c["slots"].items():
            if raw is None:continue
            path="ik_pokemon/data/"+raw
            if path not in paths:
                d=c["resource_dir"] or ""; stem=Path(raw).stem
                alternatives=[p for p in paths if p.startswith("ik_pokemon/data/"+d+"/icon/"+stem+"_") and p.endswith(".bntx")] if slot=="6" and d else []
                missing.append(dict(catalog_index=c["index"],slot=slot,raw_path=raw,icon_variants=sorted(alternatives),status="ICON_NAME_FAMILY_CANDIDATE" if alternatives else "UNRESOLVED"))
    with sqlite3.connect("file:"+str(a.cores.resolve())+"?mode=ro",uri=True) as db:
        pairs,irregular=icon_audit(db,cat,per,paths)
        # Validate the older artifact refers to the same native resource blobs, including icons.
        for path,blob in db.execute("SELECT path,blob FROM source WHERE path LIKE 'ik_pokemon/data/%/icon/%.bntx'"):
            if paths.get(path)!=blob:raise ValueError("icon source blob mismatch "+path)
    for name,rows in [("model-structures",parsed.values()),("native-references",refs),("parse-errors",errors),("normal-rare-materials",rare),("variant-errors",pair_errors),("catalog-missing",missing),("icon-pairs",pairs),("icon-irregular",irregular)]:write(a.out,name,rows)
    s=dict(source_commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),requested_files=len(wanted),parsed_files=len(parsed),format_counts=dict(formats),parse_errors=len(errors),references=dict(collections.Counter(r["status"] for r in refs)),
        catalog_missing_by_slot=dict(collections.Counter(r["slot"] for r in missing)),catalog_missing_icon_family_candidates=sum(bool(r["icon_variants"]) for r in missing),normal_rare_pairs=len(rare),variant_errors=len(pair_errors),
        normal_rare_same_texture_materials=sum(m.get("texture_lists_equal") is True for r in rare for m in r["materials"]),normal_rare_changed_rgba=sum(len(m.get("rgba_changes",[])) for r in rare for m in r["materials"]),
        icon_pairs=len(pairs),icon_equal_pixels=sum(r["pixel_equal"] is True for r in pairs),icon_different_pixels=sum(r["pixel_equal"] is False for r in pairs),icon_irregular=len(irregular),runtime_gender_shiny_verified=False,geometry_exported=False)
    (a.out/"summary.json").write_text(json.dumps(s,indent=2)+"\n");print(json.dumps(s,indent=2))
    if not parsed or not pairs or not rare:raise SystemExit("missing audit coverage")
if __name__=="__main__":main()
