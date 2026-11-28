#!/usr/bin/env python3
"""TRSHA key-row candidates, technique resolution and Maxwell bundle evidence.
Never equate a candidate row ordinal to a runtime-selected program without consumer evidence.
"""
import argparse, collections, hashlib, importlib.util, json, sqlite3, struct, subprocess
from pathlib import Path
def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
core=load("ZANativeShaderCore")
def encode(o,value,mode):
    vs=o["values"];matches=[(i,v["code"]) for i,v in enumerate(vs) if v["value"]==value]
    if len(matches)!=1:return None
    i,code=matches[0]
    code=code if mode=="raw" else code-min(v["code"] for v in vs) if mode=="min" else i
    x=code<<o["slot_index"]
    return x if x>=0 and x&o["mask_raw"]==x else None
def layout(d,count):
    w=d["param_buffer"];opts=[dict(scope=s,**o,word=o["flags"][1]) for s,os in d["groups"].items() for o in os]
    if not count or not w or len(w)%count:return None
    width=len(w)//count
    if not 1<=width<=16 or any(o["word"]>=width or o["flags"][2]!=o["word"] or not o["mask_raw"] for o in opts):return None
    masks=[0]*width
    for o in opts:
        if masks[o["word"]]&o["mask_raw"]:return None
        masks[o["word"]]|=o["mask_raw"]
    rows=[tuple(w[i:i+width]) for i in range(0,len(w),width)]
    if len(set(rows))!=count:return None
    unused=[0]*width
    for r in rows:
        for j,x in enumerate(r):unused[j]|=x&~masks[j]
    # Each option is judged independently; never assume numeric code==ordinal.
    for o in opts:
        observed={r[o["word"]]&o["mask_raw"] for r in rows}
        models={}
        for mode in ("raw","min","ordinal"):
            values={v["value"]:encode(o,v["value"],mode) for v in o["values"]}
            if None not in values.values() and observed<=set(values.values()) and len(set(values.values()))==len(values):
                models[mode]=values
        o.update(observed=sorted(observed),encodings=models)
    return dict(width=width,rows=rows,options=opts,unknown_bits=unused,ordered=rows==sorted(rows))
def candidate_rows(layout,options):
    constraints=[];unknown=[];unresolved=[]
    for name,value in sorted(options.items()):
        os=[o for o in layout["options"] if o["name"]==name]
        if not os:unknown.append([name,value]);continue
        if len(os)!=1:unresolved.append([name,value,"duplicate name"]);continue
        o=os[0]
        vals={m[value] for m in o["encodings"].values() if value in m}
        if not vals:unresolved.append([name,value,"no compatible encoding"]);continue
        constraints.append((o["word"],o["mask_raw"],vals))
    if unresolved:return [],unknown,unresolved,len(constraints)
    # Ambiguous encodings produce a union of possible rows, not a selected runtime variant.
    ids=[i for i,r in enumerate(layout["rows"]) if all(r[j]&m in v for j,m,v in constraints)]
    return ids,unknown,unresolved,len(constraints)
def bundle_evidence(raw,st):
    a=st.get("segment_a_offset");b=st.get("segment_b_offset")
    if a is None or b is None:return dict(status="NO_SEGMENT_METADATA")
    x=raw[a:a+st["segment_a_size"]];y=raw[b:b+st["segment_b_size"]]
    result=dict(a_magic=x[:8].hex(),b_magic=y[:8].hex(),b_size=len(y),b_sha256=hashlib.sha256(y).hexdigest())
    # Sample-specific structure: 0x30-byte preamble + 0x50-byte header candidate,
    # followed by one 64-bit scheduling word and three instruction words.
    if len(y)<160 or y[:8]!=bytes.fromhex("7856341200000000") or (len(y)-128)%32:
        return dict(**result,status="UNRECOGNIZED_BUNDLE_LAYOUT")
    bundles=[];nonzero=0;exit_like=[];sin_like=[];tex_like=[]
    for off in range(128,len(y),32):
        q=struct.unpack_from("<4Q",y,off)
        if not any(q):continue
        nonzero+=1
        for j,word in enumerate(q[1:],1):
            # These are raw high-bit fingerprints, not a verified disassembler.
            top=word>>48
            if top==0xe300:exit_like.append(off+8*j)
            if top==0x5080:sin_like.append(off+8*j)
            if top in (0xc038,0xc03a,0xc13a,0xde00,0xde80):tex_like.append(off+8*j)
        bundles.append(q)
    return dict(**result,status="MAXWELL_BUNDLE_LAYOUT_CANDIDATE",preamble_bytes=48,shader_header_candidate_bytes=80,first_bundle_offset=128,nonzero_bundles=nonzero,instruction_slots=nonzero*3,zero_bundles=(len(y)-128)//32-nonzero,exit_like_offsets=exit_like,sfu_like_5080_offsets=sin_like,texture_like_offsets=tex_like,code_region_sha256=hashlib.sha256(y[128:]).hexdigest(),opcodes_verified=False)
def self_test():
    d=dict(param_buffer=[0,0,1,0,1,1],groups={"shader":[dict(name="On",values=[dict(value="False",code=0),dict(value="True",code=1)],flags=[0,0,0],slot_index=0,mask_raw=1)],"global":[dict(name="UV",values=[dict(value="1",code=1),dict(value="2",code=2)],flags=[0,1,1],slot_index=0,mask_raw=1)]})
    l=layout(d,3);assert l and l["width"]==2 and l["unknown_bits"]==[0,0]
    assert candidate_rows(l,{"On":"True","UV":"2"})[0]==[2]
    assert candidate_rows(l,{"UV":"bogus"})[2]
    assert layout(dict(d,param_buffer=[0,0,0,0,1,1]),3) is None
def main():
    self_test()
    out=Path(".za-work/ZANativeShaderCore")
    paths=core.audit.tree()
    db=sqlite3.connect(out/"shader-core.sqlite");db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE key_layout(shader_path TEXT PRIMARY KEY REFERENCES shader(path),binary_path TEXT REFERENCES binary(path),width INTEGER,unknown_bits_json TEXT,ordered INTEGER,status TEXT);
    CREATE TABLE key_option(shader_path TEXT REFERENCES key_layout(shader_path),ordinal INTEGER,metadata_json TEXT,PRIMARY KEY(shader_path,ordinal));
    CREATE TABLE variant_key(shader_path TEXT REFERENCES key_layout(shader_path),row_ordinal INTEGER,key_json TEXT,PRIMARY KEY(shader_path,row_ordinal));
    CREATE TABLE material_resolution(path TEXT,material TEXT,ordinal INTEGER,technique_name TEXT,shader_name TEXT,render_target TEXT,shader_path TEXT REFERENCES shader(path),candidate_count INTEGER,candidate_ordinals_json TEXT,unknown_options_json TEXT,unresolved_options_json TEXT,status TEXT,PRIMARY KEY(path,material,ordinal));
    CREATE TABLE maxwell_evidence(binary_path TEXT,ordinal INTEGER,stage TEXT,metadata_json TEXT,PRIMARY KEY(binary_path,ordinal,stage),FOREIGN KEY(binary_path,ordinal,stage) REFERENCES stage(path,ordinal,stage));
    """)
    layouts={};names=collections.defaultdict(list);layout_rows=[];res_rows=[];maxwell_rows=[]
    for sp,name,bp in db.execute("SELECT path,name,bnsh_ref FROM shader").fetchall():
        names[name].append(sp);q=db.execute("SELECT variation_count FROM binary WHERE path=?",(bp,)).fetchone()
        if not q:continue
        d=core.trsha(core.get(sp,paths));l=layout(d,q[0])
        if l is None:layout_rows.append(dict(path=sp,name=name,status="UNRESOLVED_LAYOUT",words=len(d["param_buffer"]),variations=q[0]));continue
        layouts[sp]=l
        db.execute("INSERT INTO key_layout VALUES(?,?,?,?,?,?)",(sp,bp,l["width"],json.dumps(l["unknown_bits"]),int(l["ordered"]),"ORDINAL_CANDIDATE"))
        for i,o in enumerate(l["options"]):db.execute("INSERT INTO key_option VALUES(?,?,?)",(sp,i,json.dumps(o)))
        for i,row in enumerate(l["rows"]):db.execute("INSERT INTO variant_key VALUES(?,?,?)",(sp,i,json.dumps(row)))
        layout_rows.append(dict(path=sp,name=name,status="ORDINAL_CANDIDATE",width=l["width"],variations=q[0],unknown_bits=l["unknown_bits"],ordered=l["ordered"],options=len(l["options"]),options_without_encoding=sum(not o["encodings"] for o in l["options"])))
    techniques=collections.defaultdict(set)
    for p,s,d in db.execute("SELECT param,shader,destination FROM technique"):techniques[p].add((s,d))
    for path,material,ordinal,raw,opts in db.execute("SELECT path,material,ordinal,shader_name,options_json FROM material_shader").fetchall():
        # Explicit technique links take precedence, even when the name equals a descriptor.
        ts=techniques.get(raw,set());target=None;name=raw
        if len(ts)==1:name,target=next(iter(ts))
        candidates=names.get(name,[]);sp=candidates[0] if len(candidates)==1 and len(ts)<=1 else None
        ids=[];unknown=[];unresolved=[];n=0
        if sp in layouts:
            ids,unknown,unresolved,n=candidate_rows(layouts[sp],json.loads(opts))
            status="NO_CANDIDATE" if not ids else "UNIQUE_ROW_CANDIDATE" if len(ids)==1 else "MULTIPLE_ROW_CANDIDATES"
        else:status="UNRESOLVED_SHADER_OR_LAYOUT"
        row=dict(path=path,material=material,ordinal=ordinal,technique_name=raw,shader_name=name,render_target=target,shader_path=sp,candidate_count=len(ids),candidate_ordinals=ids,unknown_options=unknown,unresolved_options=unresolved,matched_constraints=n,status=status,runtime_verified=False)
        res_rows.append(row)
        db.execute("INSERT INTO material_resolution VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(path,material,ordinal,raw,name,target,sp,len(ids),json.dumps(ids),json.dumps(unknown),json.dumps(unresolved),status))
    # Analyze every unique stage segment in the priority shaders; cache duplicate content.
    target_names={"Unlit","FresnelEffect","IkCharacter","Transparent","InsideEmissionParallax"}
    for bp, in db.execute("SELECT DISTINCT bnsh_ref FROM shader WHERE name IN (?,?,?,?,?)",tuple(sorted(target_names))).fetchall():
        raw=core.get(bp,paths);cache={}
        for ordinal,stage,meta in db.execute("SELECT ordinal,stage,metadata_json FROM stage WHERE path=?",(bp,)).fetchall():
            st=json.loads(meta);k=(st.get("segment_a_sha256"),st.get("segment_b_sha256"))
            if k not in cache:cache[k]=bundle_evidence(raw,st)
            e=cache[k];row=dict(binary_path=bp,ordinal=ordinal,stage=stage,**e)
            maxwell_rows.append(row);db.execute("INSERT INTO maxwell_evidence VALUES(?,?,?,?)",(bp,ordinal,stage,json.dumps(e)))
    db.commit()
    integrity=db.execute("PRAGMA integrity_check").fetchone()[0];fk=db.execute("PRAGMA foreign_key_check").fetchall();db.close()
    core.audit.write(out,"variant-layouts",layout_rows);core.audit.write(out,"material-resolution",res_rows);core.audit.write(out,"maxwell-evidence",maxwell_rows)
    summary=dict(source_commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),descriptors=len(layout_rows),candidate_layouts=len(layouts),candidate_key_rows=sum(len(l["rows"]) for l in layouts.values()),material_resolutions=len(res_rows),resolution_status=dict(collections.Counter(r["status"] for r in res_rows)),technique_alias_rows=sum(r["technique_name"]!=r["shader_name"] for r in res_rows),unresolved_shader_names=dict(collections.Counter(r["technique_name"] for r in res_rows if r["shader_path"] is None)),maxwell_stages=len(maxwell_rows),maxwell_status=dict(collections.Counter(r["status"] for r in maxwell_rows)),integrity=integrity,foreign_key_errors=len(fk),runtime_variant_mapping_verified=False,gpu_instructions_decompiled=False)
    (out/"variant-summary.json").write_text(json.dumps(summary,indent=2)+"\n");print("VARIANT_SUMMARY",json.dumps(summary))
    for r in layout_rows:
        if r["name"] in target_names:print("VARIANT_LAYOUT",json.dumps(r))
    for r in res_rows:
        if any(x in r["path"] for x in ("pm0006_00_00/pm0006_00_00.trmtr","pm0006_52_00/pm0006_52_00.trmtr","pm0770_11_00/pm0770_11_00.trmtr")) and r["shader_name"] in ("Unlit","FresnelEffect") or r["technique_name"] in ("IkCharacterTransparent","IkCharacterTransparentInner") and "pm0770_11_00/pm0770_11_00.trmtr" in r["path"]:print("VARIANT_SAMPLE",json.dumps(r))
    if integrity!="ok" or fk or not layouts or not maxwell_rows:raise SystemExit("variant core integrity/coverage failure")
if __name__=="__main__":main()
