#!/usr/bin/env python3
"""ZA native shader structural metadata core; not a GPU decompiler."""
import argparse, collections, hashlib, importlib.util, json, posixpath, sqlite3, struct, subprocess
from pathlib import Path
def load(name):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
audit=load("Audit-ZANativePokemonModels")
FB=audit.FB
def get(path,paths):
    p=audit.V/path
    b=p.read_bytes() if p.is_file() else subprocess.check_output(["git","cat-file","blob",paths[path]])
    if hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()!=paths[path]:raise ValueError("blob hash mismatch")
    return b
def sha(b):return hashlib.sha256(b).hexdigest()
def trsha(b):
    f=FB(b);o=f.u("I",0);groups={}
    for i,scope in [(2,"shader"),(3,"global")]:
        groups[scope]=[dict(name=f.txt(t,0),values=[dict(value=f.txt(x,0),code=f.scalar(x,1,"I")) for x in f.tables(t,1)],
           flags=[f.scalar(t,j,"B") for j in (2,3,4)],slot_index=f.scalar(t,5,"B"),mask_raw=f.scalar(t,6,"I")) for t in f.tables(o,i)]
        if any(not x["name"] for x in groups[scope]):raise ValueError("missing option name")
    return dict(name=f.txt(o,0),filename=f.txt(o,1),groups=groups,param_buffer=[f.u("I",p) for p in f.vec(o,4)],flags_raw=[f.scalar(o,i,"B") for i in (5,6)])
def bnsh(b):
    def u(fmt,p):return struct.unpack_from("<"+fmt,b,p)[0]
    def bounded(p,n):
        if p<0 or n<0 or p+n>len(b):raise ValueError("BNSH pointer outside file")
    if len(b)<32 or b[:4]!=b"BNSH" or b[12:14]!=b"\xff\xfe" or u("I",28)!=len(b):raise ValueError("BNSH header mismatch")
    h=u("H",22);bounded(h,48)
    if b[h:h+4]!=b"grsc":raise ValueError("GRSC magic")
    count=u("I",h+28);table=u("Q",h+32)
    if count>100000:raise ValueError("variation count")
    bounded(table,count*64);rows=[]
    for i in range(count):
        off=table+i*64;src,unknown,program,back=struct.unpack_from("<4Q",b,off)
        if back!=h:raise ValueError("variation GRSC backpointer")
        p=src+program;bounded(p,56);typ,fmt=b[p:p+2];stages=[]
        for k,name in enumerate(("vertex","tess_control_candidate","tess_eval_candidate","geometry","fragment","compute")):
            ptr=u("Q",p+8+8*k)
            if not ptr:continue
            bounded(ptr,32)
            stage=dict(stage=name,descriptor_offset=ptr,format=fmt)
            if fmt==0:
                a,c=u("Q",ptr+8),u("Q",ptr+16);size_c,size_a=u("I",ptr+24),u("I",ptr+28)
                bounded(a,size_a);bounded(c,size_c)
                stage.update(segment_a_offset=a,segment_a_size=size_a,segment_a_sha256=sha(b[a:a+size_a]),segment_b_offset=c,segment_b_size=size_c,segment_b_sha256=sha(b[c:c+size_c]))
            else:stage["status"]="UNSUPPORTED_STAGE_FORMAT"
            stages.append(stage)
        rows.append(dict(ordinal=i,program_offset=p,source_pointer=src,program_pointer=program,type_raw=typ,format=fmt,stages=stages))
    return dict(version_raw=u("I",8),grsc_offset=h,variation_count=count,variation_table_offset=table,variations=rows)
def technique(b):
    f=FB(b);o=f.u("I",0);return [dict(param=f.txt(t,0),shader=f.txt(t,1),destination=f.txt(t,2)) for t in f.tables(o,1)]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--out",type=Path,default=Path(".za-work/ZANativeShaderCore"));a=p.parse_args()
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()) or a.out.resolve()==Path(".za-work").resolve():p.error("local output only")
    if a.out.exists() and any(a.out.iterdir()):p.error("empty output required")
    a.out.mkdir(parents=True,exist_ok=True);paths=audit.tree()
    db=sqlite3.connect(a.out/"shader-core.sqlite")
    db.executescript("""PRAGMA foreign_keys=ON;
    CREATE TABLE source(path TEXT PRIMARY KEY,blob TEXT NOT NULL,sha256 TEXT NOT NULL,bytes INTEGER NOT NULL,kind TEXT NOT NULL);
    CREATE TABLE shader(path TEXT PRIMARY KEY REFERENCES source(path),name TEXT NOT NULL,bnsh_ref TEXT,flags_json TEXT,parameter_words_json TEXT);
    CREATE TABLE shader_option(path TEXT REFERENCES shader(path),scope TEXT,ordinal INTEGER,name TEXT,flags_json TEXT,slot_index INTEGER,mask_raw INTEGER,PRIMARY KEY(path,scope,ordinal));
    CREATE TABLE option_value(path TEXT,scope TEXT,ordinal INTEGER,value_ordinal INTEGER,value TEXT,code INTEGER,PRIMARY KEY(path,scope,ordinal,value_ordinal),FOREIGN KEY(path,scope,ordinal) REFERENCES shader_option(path,scope,ordinal));
    CREATE TABLE binary(path TEXT PRIMARY KEY REFERENCES source(path),version_raw INTEGER,grsc_offset INTEGER,variation_count INTEGER,variation_table_offset INTEGER);
    CREATE TABLE variation(path TEXT REFERENCES binary(path),ordinal INTEGER,program_offset INTEGER,source_pointer INTEGER,program_pointer INTEGER,type_raw INTEGER,format INTEGER,PRIMARY KEY(path,ordinal));
    CREATE TABLE stage(path TEXT,ordinal INTEGER,stage TEXT,descriptor_offset INTEGER,format INTEGER,metadata_json TEXT,PRIMARY KEY(path,ordinal,stage),FOREIGN KEY(path,ordinal) REFERENCES variation(path,ordinal));
    CREATE TABLE technique(path TEXT REFERENCES source(path),ordinal INTEGER,param TEXT,shader TEXT,destination TEXT,PRIMARY KEY(path,ordinal));
    CREATE TABLE material_shader(path TEXT,material TEXT,ordinal INTEGER,shader_name TEXT,options_json TEXT,exact_definition_count INTEGER,PRIMARY KEY(path,material,ordinal));
    CREATE TABLE error(path TEXT,reason TEXT);
    """)
    defs=collections.defaultdict(list);descriptors={};binaries={};errors=[];tech=[]
    for path in sorted(paths):
        kind=Path(path).suffix.lower()
        if kind not in (".trsha",".bnsh",".trtch"):continue
        try:
            raw=get(path,paths)
            parsed=trsha(raw) if kind==".trsha" else bnsh(raw) if kind==".bnsh" else technique(raw)
            with db:
                db.execute("INSERT INTO source VALUES(?,?,?,?,?)",(path,paths[path],sha(raw),len(raw),kind))
                if kind==".trsha":
                    name=parsed["name"];filename=parsed["filename"]
                    if not name or not filename:raise ValueError("missing descriptor identity")
                    target=posixpath.normpath(posixpath.join(posixpath.dirname(path),filename))
                    db.execute("INSERT INTO shader VALUES(?,?,?,?,?)",(path,name,target,json.dumps(parsed["flags_raw"]),json.dumps(parsed["param_buffer"])))
                    for scope,opts in parsed["groups"].items():
                        for i,o in enumerate(opts):
                            db.execute("INSERT INTO shader_option VALUES(?,?,?,?,?,?,?)",(path,scope,i,o["name"],json.dumps(o["flags"]),o["slot_index"],o["mask_raw"]))
                            for j,v in enumerate(o["values"]):db.execute("INSERT INTO option_value VALUES(?,?,?,?,?,?)",(path,scope,i,j,v["value"],v["code"]))
                    defs[name].append(path);descriptors[path]=dict(path=path,target=target,**parsed)
                elif kind==".bnsh":
                    db.execute("INSERT INTO binary VALUES(?,?,?,?,?)",(path,parsed["version_raw"],parsed["grsc_offset"],parsed["variation_count"],parsed["variation_table_offset"]))
                    for v in parsed["variations"]:
                        db.execute("INSERT INTO variation VALUES(?,?,?,?,?,?,?)",(path,v["ordinal"],v["program_offset"],v["source_pointer"],v["program_pointer"],v["type_raw"],v["format"]))
                        for st in v["stages"]:db.execute("INSERT INTO stage VALUES(?,?,?,?,?,?)",(path,v["ordinal"],st["stage"],st["descriptor_offset"],st["format"],json.dumps(st)))
                    binaries[path]=parsed
                else:
                    for i,v in enumerate(parsed):db.execute("INSERT INTO technique VALUES(?,?,?,?,?)",(path,i,v["param"],v["shader"],v["destination"]))
                    tech.extend(dict(path=path,**v) for v in parsed)
        except Exception as e:errors.append(dict(path=path,reason=type(e).__name__+": "+str(e)))
    matches=[];unmatched=collections.Counter();mats=0
    for path in sorted(paths):
        if not path.startswith("ik_pokemon/data/") or not path.endswith(".trmtr"):continue
        try:
            f=FB(get(path,paths));o=f.u("I",0)
            with db:
                for t in f.tables(o,1):
                    name=f.txt(t,0)
                    for i,s in enumerate(f.tables(t,1)):
                        sh=f.txt(s,0);options={f.txt(x,0):f.txt(x,1) for x in f.tables(s,1)};candidates=defs.get(sh,[])
                        db.execute("INSERT INTO material_shader VALUES(?,?,?,?,?,?)",(path,name,i,sh,json.dumps(options),len(candidates)));mats+=1
                        if len(candidates)!=1:unmatched[sh]+=1
        except Exception as e:errors.append(dict(path=path,reason=type(e).__name__+": "+str(e)))
    for path,d in descriptors.items():
        b=binaries.get(d["target"]);matches.append(dict(path=path,name=d["name"],target=d["target"],exact_target=d["target"] in paths,binary_parsed=b is not None,param_words=len(d["param_buffer"]),variation_count=b["variation_count"] if b else None,variant_mapping_status="UNRESOLVED"))
    db.executemany("INSERT INTO error VALUES(:path,:reason)",errors);db.commit()
    counts={t:db.execute("SELECT count(*) FROM "+t).fetchone()[0] for t in ("source","shader","shader_option","option_value","binary","variation","stage","technique","material_shader","error")}
    integrity=db.execute("PRAGMA integrity_check").fetchone()[0];foreign=db.execute("PRAGMA foreign_key_check").fetchall();db.close()
    audit.write(a.out,"shader-descriptors",descriptors.values());audit.write(a.out,"shader-binaries",[dict(path=p,**b) for p,b in binaries.items()]);audit.write(a.out,"shader-links",matches);audit.write(a.out,"techniques",tech);audit.write(a.out,"errors",errors)
    summary=dict(source_commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),counts=counts,requested_shader_files=sum(Path(x).suffix.lower() in (".trsha",".bnsh",".trtch") for x in paths),exact_links=sum(x["exact_target"] for x in matches),parsed_binary_links=sum(x["binary_parsed"] for x in matches),unresolved_material_names=dict(unmatched),integrity=integrity,foreign_key_errors=len(foreign),runtime_variant_mapping_verified=False,gpu_instructions_decompiled=False)
    (a.out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print("SHADER_CORE_SUMMARY",json.dumps(summary))
    for x in matches:
        if x["name"] in ("Unlit","FresnelEffect","Transparent","InsideEmissionParallax","IkCharacter"):print("SHADER_CORE_SAMPLE",json.dumps(x))
    if integrity!="ok" or foreign or not descriptors or not binaries or not mats:raise SystemExit("shader core integrity/coverage failure")
if __name__=="__main__":main()
