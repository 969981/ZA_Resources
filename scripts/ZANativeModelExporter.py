#!/usr/bin/env python3
"""ZA LOD0 GLB V1: verified native inverse bind matrices, strict geometry, candidate materials."""
import argparse, hashlib, importlib.util, json, math, struct, subprocess
from pathlib import Path
import numpy as np

def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
geo=load("Audit-ZAGeometrySkin")
audit=geo.audit
FB=geo.FB
SAMPLE="ik_pokemon/data/pm0001/pm0001_00_00/pm0001_00_00.trmdl"
EPS=1e-4

def local_matrix(node):
    tr=node["transform"]
    if not tr or any(tr[k] is None for k in ("scale","rotation","translation")):raise ValueError("missing TRS")
    if any(abs(x)>1e-6 for key in ("scale_pivot","rotate_pivot") for x in (node[key] or [])):raise ValueError("nonzero pivot unsupported")
    x,y,z=tr["rotation"];cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y);cz,sz=math.cos(z),math.sin(z)
    rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    m=np.eye(4);m[:3,:3]=rz@ry@rx@np.diag(tr["scale"]);m[:3,3]=tr["translation"]
    if not np.isfinite(m).all():raise ValueError("nonfinite TRS")
    return m

def bind_pose(sk):
    nodes=sk["nodes"];local=[local_matrix(n) for n in nodes];world={};active=set()
    def visit(i):
        if i in world:return world[i]
        if i in active:raise ValueError("skeleton cycle")
        active.add(i);p=nodes[i]["parent"]
        if p < -1 or p>=len(nodes):raise ValueError("invalid parent")
        w=local[i] if p==-1 else visit(p)@local[i];world[i]=w;active.remove(i);return w
    for i in range(len(nodes)):visit(i)
    rig=sk["rig_map"];n=len(sk["bones"])
    if set(rig)!=set(range(n)) or any(len(v)!=1 for v in rig.values()):raise ValueError("non-bijective rig map")
    joints=[rig[i][0] for i in range(n)]
    ib=[];errors=[]
    for i,node in enumerate(joints):
        axes=sk["bones"][i]
        if axes is None or any(x is None for x in axes):raise ValueError("missing native inverse bind")
        m=np.array([list(a)+[float(j==3)] for j,a in enumerate(axes)],dtype=float).T
        if not np.isfinite(m).all():raise ValueError("nonfinite inverse bind")
        err=float(np.max(np.abs(world[node]@m-np.eye(4))))
        ib.append(m);errors.append(err)
    return local,joints,ib,dict(joints=n,transform_nodes=len(nodes),max_identity_error=max(errors,default=0),passed_joints=sum(e<=EPS for e in errors),tolerance=EPS,convention="column vector; T@Rz@Ry@Rx@S; world=parent@local; native Vec3 axes as columns")

def resolve(source,raw,paths):
    p,status=audit.resolve(source,raw,paths)
    if p is None:raise ValueError(status+" "+str(raw))
    return p

def read_mesh(m,b,sk):
    rows=geo.mesh_pair(m,b,sk)
    f=FB(m);g=FB(b);root=f.u("I",0);br=g.u("I",0)
    result=[]
    for i,(t,u,row) in enumerate(zip(f.tables(root,1),g.tables(br,1),rows)):
        if row["issues"]:raise ValueError("mesh audit issues "+str(row["issues"]))
        if len(row["declarations"])!=1:raise ValueError("multiple declarations unsupported V1")
        d=row["declarations"][0]
        if d.get("binding_candidate") not in ("DIRECT_RIG_ONLY","BOTH_POSSIBLE"):raise ValueError("unsupported joint binding")
        if any(d["weights"].get(k,0) for k in ("invalid_weight","invalid_joint_value","zero_weight_vertices","nonunit_weight_vertices","direct_rig_invalid","direct_not_in_palette")):raise ValueError("unsafe skin weights")
        if len(d["strides"])!=1 or d["strides"][0]!=48:raise ValueError("unsupported stride")
        expected=[(1,0,51,0),(2,0,43,12),(3,0,43,20),(6,0,48,28),(7,0,22,36),(8,0,39,40)]
        if [(a["usage"],a["layer"],a["type"],a["offset"]) for a in d["attrs"]]!=expected:raise ValueError("unsupported declaration")
        vd=g.bytes_vector(g.tables(u,1)[0],0);idx=g.bytes_vector(g.tables(u,0)[0],0)
        n=d["vertex_count"];pos=[];normal=[];uv=[];joints=[];weights=[]
        for v in range(n):
            o=v*48;p=struct.unpack_from("<3f",vd,o);q=np.array(struct.unpack_from("<4e",vd,o+12)[:3]);length=np.linalg.norm(q)
            if not np.isfinite(q).all() or length<1e-6:raise ValueError("invalid normal")
            tex=struct.unpack_from("<2f",vd,o+28)
            j=struct.unpack_from("<4B",vd,o+36);w=struct.unpack_from("<4H",vd,o+40);s=sum(w)
            if not s or any(k>=len(sk["bones"]) for k,x in zip(j,w) if x):raise ValueError("invalid skin")
            pos.append(p);normal.append((q/length).tolist());uv.append(tex)
            joints.append([k if x else 0 for k,x in zip(j,w)]);weights.append([x/s for x in w])
        if not np.isfinite(np.array(pos)).all() or not np.isfinite(np.array(uv)).all():raise ValueError("nonfinite vertex")
        if f.scalar(t,2,"I")!=1:raise ValueError("V1 expects uint16 indices")
        ix=np.frombuffer(idx,dtype="<u2")
        parts=[]
        for p in row["parts"]:
            if not p["index_valid"] or p["count"]%3:raise ValueError("invalid triangle range")
            parts.append((p["material"],ix[p["offset"]:p["offset"]+p["count"]].copy()))
        result.append(dict(name=row["name"],positions=pos,normals=normal,uv=uv,joints=joints,weights=weights,parts=parts))
    return result

class GLB:
    def __init__(self):
        self.data=bytearray();self.doc=dict(asset={"version":"2.0","generator":"ZANativeModelExporter V1 candidate"},buffers=[],bufferViews=[],accessors=[],nodes=[],meshes=[],skins=[],materials=[],scenes=[{"nodes":[]}],scene=0)
    def add(self,data,dtype,kind,component,target=None,bounds=False):
        a=np.asarray(data,dtype=dtype)
        while len(self.data)%4:self.data.append(0)
        raw=a.tobytes();view=dict(buffer=0,byteOffset=len(self.data),byteLength=len(raw))
        if target:view["target"]=target
        vi=len(self.doc["bufferViews"]);self.doc["bufferViews"].append(view);self.data.extend(raw)
        ac=dict(bufferView=vi,componentType=component,count=len(a),type=kind)
        if bounds:ac.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
        i=len(self.doc["accessors"]);self.doc["accessors"].append(ac);return i
    def save(self,path):
        self.doc["buffers"]=[dict(byteLength=len(self.data))]
        j=json.dumps(self.doc,separators=(",",":"),allow_nan=False).encode();j+=b" "*((-len(j))%4)
        b=bytes(self.data)+b"\0"*((-len(self.data))%4)
        raw=struct.pack("<4sII",b"glTF",2,12+8+len(j)+8+len(b))+struct.pack("<I4s",len(j),b"JSON")+j+struct.pack("<I4s",len(b),b"BIN\0")+b
        path.write_bytes(raw);return hashlib.sha256(raw).hexdigest()

def export(path,shapes,sk,local,joints,ib,materials,variant):
    g=GLB();d=g.doc
    # Candidate visualization: representative layer color, not texture bake or original Shader.
    mid={}
    for m in materials:
        rgba=m["rgba"].get("BaseColorLayer1") or m["rgba"].get("BaseColor") or [1,1,1,1]
        color=[min(1,max(0,float(x))) for x in rgba]
        mid[m["name"]]=len(d["materials"])
        d["materials"].append(dict(name=m["name"],pbrMetallicRoughness=dict(baseColorFactor=color,metallicFactor=0,roughnessFactor=1),
            extras=dict(native_variant=variant,appearance_status="CANDIDATE_FLAT_LAYER_COLOR",original_material=m)))
    for i,n in enumerate(sk["nodes"]):
        d["nodes"].append(dict(name=n["name"],matrix=local[i].T.reshape(-1).tolist()))
    for i,n in enumerate(sk["nodes"]):
        if n["parent"]==-1:d["scenes"][0]["nodes"].append(i)
        else:d["nodes"][n["parent"]].setdefault("children",[]).append(i)
    ibac=g.add([x.T.reshape(-1) for x in ib],"<f4","MAT4",5126)
    d["skins"].append(dict(joints=joints,inverseBindMatrices=ibac))
    vtotal=itotal=ptotal=0
    for sh in shapes:
        n=len(sh["positions"]);vtotal+=n
        attrs=dict(POSITION=g.add(sh["positions"],"<f4","VEC3",5126,34962,True),
            NORMAL=g.add(sh["normals"],"<f4","VEC3",5126,34962),
            TEXCOORD_0=g.add(sh["uv"],"<f4","VEC2",5126,34962),
            JOINTS_0=g.add(sh["joints"],"<u2","VEC4",5123,34962),
            WEIGHTS_0=g.add(sh["weights"],"<f4","VEC4",5126,34962))
        primitives=[]
        for name,ix in sh["parts"]:
            if name not in mid:raise ValueError("material missing "+str(name))
            itotal+=len(ix);ptotal+=1
            primitives.append(dict(attributes=attrs,indices=g.add(ix,"<u2","SCALAR",5123,34963,True),material=mid[name],mode=4))
        mi=len(d["meshes"]);d["meshes"].append(dict(name=sh["name"],primitives=primitives))
        ni=len(d["nodes"]);d["nodes"].append(dict(name=sh["name"],mesh=mi,skin=0));d["scenes"][0]["nodes"].append(ni)
    d["extras"]=dict(variant=variant,geometry="native LOD0",material_status="candidate flat colors only",native_shader_parity=False,coordinate_parity=False,animations=False)
    digest=g.save(path)
    return dict(file=path.name,sha256=digest,bytes=path.stat().st_size,vertices=vtotal,indices=itotal,primitives=ptotal,joints=len(joints),materials=len(mid),variant=variant,material_status="CANDIDATE_FLAT_LAYER_COLOR")

def validate(path):
    b=path.read_bytes();magic,version,size=struct.unpack_from("<4sII",b)
    if (magic,version,size)!=(b"glTF",2,len(b)):raise ValueError("bad GLB header")
    n,typ=struct.unpack_from("<I4s",b,12)
    if typ!=b"JSON":raise ValueError("bad JSON chunk")
    doc=json.loads(b[20:20+n]);off=20+n;bn,bt=struct.unpack_from("<I4s",b,off)
    if bt!=b"BIN\0" or off+8+bn!=len(b):raise ValueError("bad BIN chunk")
    raw=b[off+8:];sizes={5123:("<u2",2),5126:("<f4",4)};dims={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}
    def accessor(i):
        a=doc["accessors"][i];v=doc["bufferViews"][a["bufferView"]];dtype,k=sizes[a["componentType"]];dim=dims[a["type"]]
        start=v["byteOffset"];need=a["count"]*dim*k
        if start%4 or need>v["byteLength"] or start+need>len(raw):raise ValueError("accessor bounds")
        return np.frombuffer(raw[start:start+need],dtype=dtype).reshape(a["count"],dim)
    skin=doc["skins"][0];j=len(skin["joints"])
    assert accessor(skin["inverseBindMatrices"]).shape==(j,16)
    for mesh in doc["meshes"]:
        for p in mesh["primitives"]:
            a=p["attributes"];n=len(accessor(a["POSITION"]));ix=accessor(p["indices"])
            assert len(ix)%3==0 and int(ix.max())<n
            assert all(len(accessor(i))==n for i in a.values())
            assert int(accessor(a["JOINTS_0"]).max())<j
            assert np.max(np.abs(accessor(a["WEIGHTS_0"]).sum(axis=1)-1))<1e-6
    # Re-read serialized node matrices and original inverse binds independently.
    parent={}
    for i,node in enumerate(doc["nodes"]):
        for c in node.get("children",[]):parent[c]=i
    def world(i):
        m=np.array(doc["nodes"][i].get("matrix",np.eye(4).reshape(-1))).reshape(4,4).T
        return world(parent[i])@m if i in parent else m
    err=max(float(np.max(np.abs(world(i)@m.reshape(4,4).T-np.eye(4)))) for i,m in zip(skin["joints"],accessor(skin["inverseBindMatrices"])))
    if err>EPS:raise ValueError("serialized inverse bind failed")
    return dict(structural_validation="PASS",serialized_bind_max_error=err,external_gltf_validator="NOT_RUN")

def self_test():
    n=dict(name="root",parent=-1,rig=0,transform=dict(scale=[1,1,1],rotation=[0,0,0],translation=[1,2,3]),scale_pivot=[0,0,0],rotate_pivot=[0,0,0])
    sk=dict(nodes=[n],rig_map={0:[0]},bones=[[[1,0,0],[0,1,0],[0,0,1],[-1,-2,-3]]])
    _,_,_,s=bind_pose(sk);assert s["max_identity_error"]==0
    print("inverse bind synthetic regression passed")

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--audit-all-bind",action="store_true");p.add_argument("--model",default=SAMPLE);p.add_argument("--out",type=Path,default=Path(".za-work/ZANativeModelExporterV1"));a=p.parse_args()
    if a.self_test:self_test();return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()) or a.out.resolve()==Path(".za-work").resolve():p.error("local output required")
    if a.out.exists() and any(a.out.iterdir()):p.error("empty output required")
    a.out.mkdir(parents=True,exist_ok=True);paths=audit.tree()
    def get(p):return audit.checked(p,paths)
    if a.audit_all_bind:
        reports=[];errors=[]
        for path in sorted(paths):
            if not path.startswith("ik_pokemon/data/") or not path.endswith(".trmdl"):continue
            try:
                mdl=audit.parse(get(path),".trmdl");sp=resolve(path,mdl["skeleton"],paths)
                _,_,_,r=bind_pose(geo.skeleton(get(sp)));reports.append(dict(model=path,skeleton=sp,**r))
            except Exception as e:errors.append(dict(model=path,error=str(e)))
        audit.write(a.out,"bind-audit",reports);audit.write(a.out,"bind-errors",errors)
        summary=dict(models=len(reports)+len(errors),matrix_evaluated=len(reports),all_joints_pass=sum(x["max_identity_error"]<=EPS for x in reports),matrix_fail=sum(x["max_identity_error"]>EPS for x in reports),unsupported=len(errors))
        (a.out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps(summary,indent=2));return
    if a.model!=SAMPLE:raise ValueError("V1 restricted to verified Bulbasaur sample")
    mdl=audit.parse(get(a.model),".trmdl");sp=resolve(a.model,mdl["skeleton"],paths);sk=geo.skeleton(get(sp))
    local,joints,ib,bind=bind_pose(sk)
    if bind["max_identity_error"]>EPS:raise ValueError("native inverse bind fails")
    mp=resolve(a.model,mdl["meshes"][0],paths);mb=get(mp);f=FB(mb);bp=resolve(mp,f.txt(f.u("I",0),2),paths)
    shapes=read_mesh(mb,get(bp),sk)
    mmp=a.model.removesuffix(".trmdl")+".trmmt"
    variants=audit.parse(get(mmp),".trmmt")["variants"];exports=[]
    for variant in ("normal","rare"):
        rows=[x for x in variants if x["name"]==variant]
        if len(rows)!=1 or len(rows[0]["material_files"])!=1:raise ValueError("unsupported variant")
        path=resolve(mmp,rows[0]["material_files"][0],paths)
        mats=geo.material(get(path))
        file=a.out/(Path(a.model).stem+"_"+variant+".glb")
        exports.append(dict(**export(file,shapes,sk,local,joints,ib,mats,variant),**validate(file)))
    summary=dict(source_commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),model=a.model,mesh=mp,buffer=bp,skeleton=sp,bind_pose=bind,exports=exports,native_shader_parity=False,glb_visual_parity=False)
    (a.out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
