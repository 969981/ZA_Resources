"""Independent rig/palette evidence: no bind-pose-only acceptance."""
import collections, hashlib, struct
import numpy as np
def examine(geo,m,b,sk):
    f=geo.FB(m);g=geo.FB(b);shapes=f.tables(f.u("I",0),1);bufs=g.tables(g.u("I",0),1)
    audit=geo.mesh_pair(m,b,sk);all_rows=[];reference=collections.defaultdict(set);pending=[]
    for t,u,row in zip(shapes,bufs,audit):
        ds=row["declarations"]
        if len(ds)!=1 or len(ds[0]["strides"])!=1 or row["issues"]:continue
        d=ds[0];w=d.get("weights",{});attrs={(a["usage"],a["layer"]):a for a in d["attrs"]}
        if any(k not in attrs for k in [(1,0),(7,0),(8,0)]):continue
        pa,ja,wa=[attrs[k] for k in [(1,0),(7,0),(8,0)]]
        if (pa["type"],ja["type"],wa["type"])!=(51,22,39):continue
        raw=g.bytes_vector(g.tables(u,1)[0],0);stride=d["strides"][0];pal=row["palette_raw"];bad=[]
        for i in range(d["vertex_count"]):
            o=i*stride;p=struct.unpack_from("<3f",raw,o+pa["offset"]);j=struct.unpack_from("<4B",raw,o+ja["offset"]);wt=struct.unpack_from("<4H",raw,o+wa["offset"])
            pairs=tuple(sorted((k,x) for k,x in zip(j,wt) if x))
            key=(tuple(round(x,6) for x in p),pairs)
            if d["binding_candidate"]=="DIRECT_RIG_ONLY":reference[key].add(row["name"])
            if any(k not in pal for k,x in pairs):bad.append((i,key))
        used=d.get("used_raw_joint_ids",[])
        direct=all(len(sk["rig_map"].get(k,[]))==1 and k<len(sk["bones"]) for k in used)
        local=all(k<len(pal) and len(sk["rig_map"].get(pal[k],[]))==1 for k in used)
        result=dict(shape=row["name"],candidate=d["binding_candidate"],rig_offset=sk["rig_offset"],palette=pal,used=used,raw_joint_nodes={str(k):sk["nodes"][sk["rig_map"][k][0]]["name"] for k in used if len(sk["rig_map"].get(k,[]))==1},direct_all_valid=direct,local_all_valid=local,palette_missing=w.get("direct_not_in_palette",0),direct_invalid=w.get("direct_rig_invalid",0),local_invalid=w.get("local_palette_invalid",0),bad_vertices=len(bad),zero_weight_vertices=w.get("zero_weight_vertices",0),nonunit_weight_vertices=w.get("nonunit_weight_vertices",0),status="STRICT_GATE_UNCHANGED")
        all_rows.append(result);pending.append((result,bad))
    for row,bad in pending:
        matched=[(i,sorted(reference[key]-{row["shape"]})) for i,key in bad if reference[key]-{row["shape"]}]
        row["same_position_weight_reference_vertices"]=len(matched)
        row["reference_shapes"]=sorted({s for _,ss in matched for s in ss})
        if bad and row["direct_all_valid"] and not row["local_all_valid"]:
            row["status"]="DIRECT_RIG_CANDIDATE_WITH_PALETTE_CONFLICT"
            row["candidate_joint_mapping"]={str(k):k for k in row["used"]}
        # No proof from bind pose alone; even a duplicate is only supporting evidence.
        row["native_consumer_verified"]=False
    return all_rows
