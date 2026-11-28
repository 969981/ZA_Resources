#!/usr/bin/env python3
"""Native mesh/skin audit; explicit candidate LayerMask formula, no runtime parity claim."""
import argparse, collections, importlib.util, json, math, struct, subprocess
from pathlib import Path
def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
audit=load("Audit-ZANativePokemonModels")
FB=audit.FB
# Known widths from repository SV schema; unsupported types are reported, not guessed.
FMT={20:("4B",4,255),22:("4B",4,1),36:("I",4,1),37:("i",4,1),39:("4H",8,65535),43:("4e",8,1),48:("2f",8,1),51:("3f",12,1),54:("4f",16,1)}
def unpack(data,off,typ):
    fmt,size,div=FMT[typ]
    if off<0 or off+size>len(data):raise ValueError("attribute outside buffer")
    return tuple(x/div if div!=1 else x for x in struct.unpack_from("<"+fmt,data,off))
def skeleton(b):
    f=FB(b);o=f.u("I",0)
    nodes=[]
    for t in f.tables(o,1):
        tr=f.ptr(f.field(t,1))
        nodes.append(dict(name=f.txt(t,0),parent=f.scalar(t,4,"i",-1),rig=f.scalar(t,5,"i",-1),
            transform=None if tr is None else dict(scale=f.floats(tr,0,3),rotation=f.floats(tr,1,3),translation=f.floats(tr,2,3)),
            scale_pivot=f.floats(t,2,3),rotate_pivot=f.floats(t,3,3)))
    bones=[]
    for t in f.tables(o,2):
        m=f.ptr(f.field(t,2));bones.append(None if m is None else [f.floats(m,i,3) for i in range(4)])
    rig=collections.defaultdict(list)
    for i,n in enumerate(nodes):
        if n["rig"]>=0:rig[n["rig"]].append(i)
    return dict(nodes=nodes,bones=bones,rig_offset=f.scalar(o,4,"I"),rig_map=dict(rig),
                nonunique_rig=sum(len(x)!=1 for x in rig.values()),rig_outside_bones=sum(i>=len(bones) for i in rig))
def mesh_pair(m,b,sk):
    f=FB(m);g=FB(b);root=f.u("I",0);br=g.u("I",0)
    shapes=f.tables(root,1);buffers=g.tables(br,1)
    if len(shapes)!=len(buffers):raise ValueError("shape/buffer count mismatch")
    rig=sk["rig_map"];result=[]
    for i,(t,u) in enumerate(zip(shapes,buffers)):
        row=dict(shape_index=i,name=f.txt(t,0),issues=[],parts=[],declarations=[])
        issues=row["issues"]; vertices=[g.bytes_vector(x,0) for x in g.tables(u,1)]
        indices=[g.bytes_vector(x,0) for x in g.tables(u,0)]
        pal=[f.scalar(x,0,"I") for x in f.tables(t,10)]
        row["palette_raw"]=pal
        row["palette_invalid_rigs"]=sum(len(rig.get(k,[]))!=1 for k in pal)
        declarations=f.tables(t,3)
        counts={}
        for di,d in enumerate(declarations):
            attrs=[dict(usage=f.scalar(x,1,"I"),layer=f.scalar(x,2,"I"),type=f.scalar(x,3,"I"),offset=f.scalar(x,4,"I")) for x in f.tables(d,0)]
            strides=[f.scalar(x,0,"I") for x in f.tables(d,1)]
            dr=dict(index=di,attrs=attrs,strides=strides,stream_lengths=[len(v) for v in vertices])
            row["declarations"].append(dr)
            pos=[a for a in attrs if a["usage"]==1]
            if len(pos)!=1:issues.append("POSITION_MISSING_OR_AMBIGUOUS");continue
            # layer-as-stream is a reference-schema hypothesis; bounds verify actual compatibility.
            def stream(a):
                # Single interleaved stream: layer is the semantic set, not stream index.
                l=0 if len(vertices)==len(strides)==1 else a["layer"]
                if l>=len(vertices) or l>=len(strides) or not strides[l]:raise ValueError("unsupported stream/stride")
                if len(vertices[l])%strides[l]:raise ValueError("nonintegral vertex count")
                if a["type"] not in FMT:raise ValueError("unsupported attribute type "+str(a["type"]))
                if a["offset"]+FMT[a["type"]][1]>strides[l]:raise ValueError("attribute exceeds stride")
                return vertices[l],strides[l],len(vertices[l])//strides[l]
            try:
                vd,st,n=stream(pos[0]);counts[di]=n;dr["vertex_count"]=n
                bounds=[[],[]];finite=0
                for v in range(n):
                    p=unpack(vd,v*st+pos[0]["offset"],pos[0]["type"])
                    if len(p)!=3 or not all(math.isfinite(x) for x in p):continue
                    if finite==0:bounds=[list(p),list(p)]
                    else:
                        bounds[0]=[min(a,b) for a,b in zip(bounds[0],p)];bounds[1]=[max(a,b) for a,b in zip(bounds[1],p)]
                    finite+=1
                dr.update(finite_positions=finite,bounds=bounds if finite else None)
                if finite!=n:issues.append("INVALID_POSITION")
                for a in attrs:
                    try:
                        _,_,an=stream(a)
                        if an!=n:issues.append("STREAM_VERTEX_COUNT_MISMATCH")
                    except ValueError as e:issues.append(str(e))
                js=[a for a in attrs if a["usage"]==7];ws=[a for a in attrs if a["usage"]==8]
                if len(js)!=len(ws):issues.append("JOINT_WEIGHT_STREAM_MISMATCH");continue
                if not js:dr["skin"]="NO_SKIN_ATTRIBUTES";continue
                streams=[(j,w,stream(j),stream(w)) for j,w in zip(js,ws)]
                stat=collections.Counter();minsum=math.inf;maxsum=-math.inf;used=set()
                for vi in range(n):
                    total=0.0
                    for j,w,(jb,jst,jn),(wb,wst,wn) in streams:
                        if vi>=min(jn,wn):raise ValueError("joint/weight stream shorter")
                        ji=unpack(jb,vi*jst+j["offset"],j["type"]);ww=unpack(wb,vi*wst+w["offset"],w["type"])
                        # Type39 normalized joint fields, if present, need raw integers, not normalized values.
                        if j["type"]==39:ji=struct.unpack_from("<4H",jb,vi*jst+j["offset"])
                        if len(ji)!=len(ww):raise ValueError("joint/weight component mismatch")
                        for k,x in zip(ji,ww):
                            if not math.isfinite(x) or x<0:stat["invalid_weight"]+=1;continue
                            total+=x
                            if x==0:continue
                            stat["positive_influences"]+=1
                            if not math.isfinite(k) or k<0 or int(k)!=k:stat["invalid_joint_value"]+=1;continue
                            k=int(k);used.add(k)
                            if len(rig.get(k,[]))!=1 or k>=len(sk["bones"]):stat["direct_rig_invalid"]+=1
                            if k not in pal:stat["direct_not_in_palette"]+=1
                            if k>=len(pal) or len(rig.get(pal[k],[]))!=1 or pal[k]>=len(sk["bones"]):stat["local_palette_invalid"]+=1
                    minsum=min(minsum,total);maxsum=max(maxsum,total)
                    if total==0:stat["zero_weight_vertices"]+=1
                    if abs(total-1)>0.002:stat["nonunit_weight_vertices"]+=1
                dr.update(skin="AUDITED",weights=dict(stat),weight_sum_min=minsum if n else None,weight_sum_max=maxsum if n else None,used_raw_joint_ids=sorted(used))
                direct=stat["direct_rig_invalid"]==stat["direct_not_in_palette"]==stat["invalid_joint_value"]==0
                local=stat["local_palette_invalid"]==stat["invalid_joint_value"]==0
                dr["binding_candidate"]="BOTH_POSSIBLE" if direct and local else "DIRECT_RIG_ONLY" if direct else "LOCAL_PALETTE_ONLY" if local else "NEITHER"
            except (ValueError,KeyError,struct.error,OverflowError) as e:issues.append(str(e))
        typ=f.scalar(t,2,"I");width={0:1,1:2,2:4}.get(typ)
        if width is None or len(indices)!=1:issues.append("UNSUPPORTED_INDEX_LAYOUT")
        else:
            data=indices[0]
            if len(data)%width:issues.append("INDEX_BUFFER_REMAINDER")
            else:
                ix=[x[0] for x in struct.iter_unpack("<"+{1:"B",2:"H",4:"I"}[width],data)]
                row["index_count"]=len(ix)
                for part in f.tables(t,4):
                    count=f.scalar(part,0,"I");off=f.scalar(part,1,"I");di=f.scalar(part,2,"I")
                    end=off+count; valid=end<=len(ix) and di in counts
                    sub=ix[off:end] if valid else []
                    good=valid and all(x<counts[di] for x in sub)
                    row["parts"].append(dict(material=f.txt(part,3),count=count,offset=off,declaration=di,range_valid=valid,index_valid=good,max_index=max(sub,default=None),triangle_count_candidate=count//3 if count%3==0 else None))
                    if not good:issues.append("INDEX_OR_PART_RANGE_INVALID")
        result.append(row)
    return result
def layer_reference(texel,base,layers,weights,multiply):
    # gftool IkCharacter.glsl, not original ZA GPU shader. Caller supplies processed weights.
    if len(weights)!=4 or len(layers)!=4 or not all(0<=w<=1 for w in weights):raise ValueError("four processed weights required")
    rgb=[base[i]*texel[i]*max(1-sum(weights),0) for i in range(3)]
    for tint,w in zip(layers,weights):
        rgb=[v*(1-w)+tint[i]*(texel[i] if multiply else 1)*w for i,v in enumerate(rgb)]
    return rgb
def material(b):
    f=FB(b);o=f.u("I",0);rows=[]
    for t in f.tables(o,1):
        textures={f.txt(x,0):f.txt(x,1) for x in f.tables(t,2)}
        if "LayerMaskMap" not in textures:continue
        def params(slot,typ,default):
            return {f.txt(x,0):f.scalar(x,1,typ,default) for x in f.tables(t,slot)}
        rgba={f.txt(x,0):f.floats(x,1,4) for x in f.tables(t,7)}
        shaders=[]
        for x in f.tables(t,1):
            shaders.append(dict(name=f.txt(x,0),values={f.txt(y,0):f.txt(y,1) for y in f.tables(x,1)}))
        rows.append(dict(name=f.txt(t,0),textures=textures,shaders=shaders,rgba=rgba,
            int_parameters=params(9,"i",-1),float_parameters=params(4,"f",0.0),
            reference_algorithm="GFTool IkCharacter candidate only",native_shader_verified=False))
    return rows
def self_test():
    assert unpack(struct.pack("<4H",65535,0,32768,0),0,39)[0]==1
    assert unpack(bytes([3,0,0,0]),0,22)==(3,0,0,0)
    assert layer_reference([1,1,1],[1,1,1],[[1,0,0]]*4,[1,0,0,0],False)==[1,0,0]
    assert layer_reference([.5,.5,.5],[1,1,1],[[1,0,0]]*4,[0,0,0,0],True)==[.5,.5,.5]
    print("geometry decoder and candidate blend fixtures passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--out",type=Path,default=Path(".za-work/ZAGeometrySkinAudit"));a=p.parse_args()
    if a.self_test:self_test();return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()) or a.out.resolve()==Path(".za-work").resolve():p.error("local output required")
    if a.out.exists() and any(a.out.iterdir()):p.error("empty output required")
    a.out.mkdir(parents=True,exist_ok=True);paths=audit.tree()
    models=[p for p in sorted(paths) if p.startswith("ik_pokemon/data/") and p.endswith(".trmdl")]
    refs={};errors=[];meshes=[];skels={};matrows=[];counts=collections.Counter();cache={}
    def get(p):
        return audit.checked(p,paths)
    def target(source,raw):
        p,status=audit.resolve(source,raw,paths)
        if p is None:raise ValueError(status+" "+raw)
        return p
    for p in models:
        try:
            mdl=audit.parse(get(p),".trmdl");skp=target(p,mdl["skeleton"])
            if skp not in skels:skels[skp]=skeleton(get(skp))
            sk=skels[skp]
            for raw in mdl["meshes"]:
                mp=target(p,raw)
                key=(mp,skp)
                if key in refs:continue
                mb=get(mp);f=FB(mb);bp=target(mp,f.txt(f.u("I",0),2))
                shapes=mesh_pair(mb,get(bp),sk)
                refs[key]=bp;meshes.append(dict(model=p,mesh=mp,buffer=bp,skeleton=skp,shapes=shapes))
                counts["mesh_pairs"]+=1
                for sh in shapes:
                    counts["shapes"]+=1;counts["shape_issues"]+=bool(sh["issues"])
                    for d in sh["declarations"]:
                        counts["declarations"]+=1;counts["vertices_declaration_sum"]+=d.get("vertex_count",0)
                        if d.get("skin")=="AUDITED":
                            counts[d["binding_candidate"]]+=1
                            counts.update(d["weights"])
        except Exception as e:errors.append(dict(model=p,error=str(e)))
    for p in sorted(paths):
        if not p.startswith("ik_pokemon/data/") or not p.endswith(".trmtr"):continue
        try:
            for m in material(get(p)):
                # JSON strict: nonfinite raw floats are preserved as null, not fabricated.
                m["float_parameters"]={k:v if math.isfinite(v) else None for k,v in m["float_parameters"].items()}
                matrows.append(dict(path=p,**m))
        except Exception as e:errors.append(dict(material=p,error=str(e)))
    for name,rows in [("mesh-skin",meshes),("skeletons",[dict(path=k,**v) for k,v in skels.items()]),("layer-materials",matrows),("errors",errors)]:audit.write(a.out,name,rows)
    result=dict(source_commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),models=len(models),unique_skeletons=len(skels),counts=dict(counts),layer_materials=len(matrows),errors=len(errors),native_shader_parity=False,bind_matrix_semantics_verified=False,glb_exported=False)
    (a.out/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,indent=2))
    if not meshes or not matrows:raise SystemExit("no geometry/material coverage")
if __name__=="__main__":main()
