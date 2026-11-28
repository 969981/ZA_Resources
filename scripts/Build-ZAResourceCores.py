#!/usr/bin/env python3
"""Four ZA resource cores. Direct native fields, exact paths, and candidate links are separate."""
import argparse, collections, hashlib, importlib.util, json, re, sqlite3, subprocess, tempfile
from pathlib import Path, PurePosixPath

V=Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual")
ITEM="world/exl/item_data/item_data/item_data.bin"
CAT="ik_pokemon/catalog/catalog/poke_resource_table.trpmcatalog"
PERSONAL="avalon/data/personal_array.bin"
def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
native=load("Probe-ZA-PokemonConfig")
census=load("Build-ZACompleteResourceCatalog")
def read_jsonl(p):
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip(): yield json.loads(line)
def sha(b): return hashlib.sha256(b).hexdigest()
def rid(path): return sha(("2.0.2\0"+path).encode())
def item_rows(b):
    f=native.FB(b); result=[]
    for i,o in enumerate(f.rows(0)):
        id=f.scalar(o,0,"i")
        internal=f.string(f.field(o,2)); icon=f.string(f.field(o,3))
        if internal is None or icon is None: raise ValueError("required ItemData string missing")
        result.append((id,i,o,internal,icon))
    if len({r[0] for r in result})!=len(result): raise ValueError("duplicate ItemID")
    return result

SCHEMA="""
PRAGMA foreign_keys=ON;
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE source(resource_id TEXT PRIMARY KEY,path TEXT UNIQUE NOT NULL,blob TEXT,representation TEXT NOT NULL,kind TEXT NOT NULL,domain TEXT NOT NULL,category TEXT NOT NULL);
CREATE TABLE pokemon_catalog(catalog_index INTEGER PRIMARY KEY,table_offset INTEGER NOT NULL,species_key INTEGER NOT NULL,form_key INTEGER NOT NULL,appearance_key INTEGER NOT NULL,personal_national_raw INTEGER,personal_present INTEGER,resource_dir TEXT,UNIQUE(species_key,form_key,appearance_key));
CREATE TABLE catalog_slot(catalog_index INTEGER REFERENCES pokemon_catalog,slot INTEGER NOT NULL,raw_path TEXT NOT NULL,resolved_id TEXT REFERENCES source,status TEXT NOT NULL,PRIMARY KEY(catalog_index,slot));
CREATE TABLE pokemon_icon(resource_id TEXT PRIMARY KEY REFERENCES source,resource_dir TEXT NOT NULL,name_tokens TEXT,gender INTEGER,shiny INTEGER,status TEXT NOT NULL);
CREATE TABLE pokemon_icon_candidate(resource_id TEXT REFERENCES pokemon_icon,catalog_index INTEGER REFERENCES pokemon_catalog,evidence TEXT NOT NULL,PRIMARY KEY(resource_id,catalog_index));
CREATE TABLE item(item_id INTEGER PRIMARY KEY,row_index INTEGER NOT NULL,table_offset INTEGER NOT NULL,internal_name TEXT NOT NULL,icon_name TEXT NOT NULL,icon_resource_id TEXT REFERENCES source,status TEXT NOT NULL);
CREATE TABLE ui_texture(blob TEXT,member_index INTEGER,texture_index INTEGER,name TEXT NOT NULL,category TEXT,width INTEGER,height INTEGER,format TEXT,rgba_sha256 TEXT,decode_status TEXT,member_name TEXT,member_sha256 TEXT,PRIMARY KEY(blob,member_index,texture_index));
CREATE TABLE ui_texture_source(blob TEXT,member_index INTEGER,texture_index INTEGER,resource_id TEXT REFERENCES source,PRIMARY KEY(blob,member_index,texture_index,resource_id),FOREIGN KEY(blob,member_index,texture_index) REFERENCES ui_texture);
CREATE TABLE ui_candidate(blob TEXT,member_index INTEGER,texture_index INTEGER,semantic TEXT NOT NULL,evidence TEXT NOT NULL,game_id INTEGER,PRIMARY KEY(blob,member_index,texture_index,semantic),FOREIGN KEY(blob,member_index,texture_index) REFERENCES ui_texture);
CREATE TABLE model_group(group_path TEXT PRIMARY KEY,model_count INTEGER NOT NULL,group_status TEXT NOT NULL);
CREATE TABLE model_member(group_path TEXT REFERENCES model_group,resource_id TEXT REFERENCES source,role TEXT NOT NULL,evidence TEXT NOT NULL,PRIMARY KEY(group_path,resource_id));
CREATE INDEX source_blob ON source(blob);
CREATE INDEX item_icon ON item(icon_resource_id);
CREATE INDEX candidate_catalog ON pokemon_icon_candidate(catalog_index);
CREATE INDEX texture_source_resource ON ui_texture_source(resource_id);
CREATE VIEW item_icon_usage AS SELECT icon_name,COUNT(*) AS item_count FROM item GROUP BY icon_name;
CREATE VIEW item_texture_candidates AS SELECT i.item_id,i.icon_name,t.* FROM item i JOIN ui_texture_source s ON i.icon_resource_id=s.resource_id JOIN ui_texture t USING(blob,member_index,texture_index) WHERE i.icon_name=t.name;
CREATE VIEW pokemon_icon_keys AS SELECT p.*,c.catalog_index,k.species_key,k.form_key,k.appearance_key,k.personal_national_raw FROM pokemon_icon p LEFT JOIN pokemon_icon_candidate c USING(resource_id) LEFT JOIN pokemon_catalog k USING(catalog_index);
"""
def semantic(name,category):
    s=name.lower(); out=set()
    if category in {"types","balls","moves","badges","ribbons","items","donuts","pokemon","maps","characters"}:
        out.add(category+"_category_candidate")
    if re.search(r"ribbon|akashi",s): out.add("ribbon_or_mark_keyword")
    if re.search(r"icon_marking_0[0-5]",s): out.add("box_marking_name")
    if "medal" in s: out.add("medal_keyword")
    if "icon_ball" in s: out.add("ball_ui_name")
    if "icon_type" in s: out.add("type_ui_name")
    return sorted(out)

def core(db,records,catalog,items):
    paths={r[1]:r for r,m in records}; bydir=collections.defaultdict(list); groups=collections.defaultdict(list)
    db.executemany("INSERT INTO source VALUES(?,?,?,?,?,?,?)",
        ((r[0],r[1],r[8],r[7],r[4],r[5],r[6]) for r,m in records))
    for c in catalog:
        idx=c["index"]; p=c["personal"] or {}; key=c["key_raw"]; d=c["resource_dir"]
        db.execute("INSERT INTO pokemon_catalog VALUES(?,?,?,?,?,?,?,?)",(idx,c["table_offset"],*key,p.get("national_raw"),p.get("present"),d))
        if d: bydir[d].append(idx)
        for slot,raw in c["slots"].items():
            if raw is None: continue
            target=paths.get("ik_pokemon/data/"+raw)
            db.execute("INSERT INTO catalog_slot VALUES(?,?,?,?,?)",(idx,int(slot),raw,target[0] if target else None,"EXACT_NATIVE_PATH" if target else "MISSING_PATH"))
    for path,r in paths.items():
        if path.startswith("ik_pokemon/data/") and "/icon/" in path and r[3]==".bntx":
            d="/".join(path.split("/")[2:4]); ids=bydir[d]
            tokens=re.fullmatch(r"pm(\d{4})_(\d+)_(\d+)_(\d+)_(\d+)",PurePosixPath(path).stem)
            db.execute("INSERT INTO pokemon_icon VALUES(?,?,?,?,?,?)",(r[0],d,json.dumps(tokens.groups()) if tokens else None,None,None,"DIRECTORY_CANDIDATE" if ids else "UNMATCHED"))
            db.executemany("INSERT INTO pokemon_icon_candidate VALUES(?,?,?)",((r[0],idx,"CANDIDATE_DIRECTORY_JOIN") for idx in ids))
        if r[5]=="model" and r[4] in {"model","texture","animation"}:
            # Group by exact directory, not inferred mesh/material dependencies.
            d=str(PurePosixPath(path).parent); groups[d].append(r)
    for d,rs in groups.items():
        count=sum(r[3]==".trmdl" for r in rs)
        db.execute("INSERT INTO model_group VALUES(?,?,?)",(d,count,"DIRECTORY_GROUP_CANDIDATE"))
        db.executemany("INSERT INTO model_member VALUES(?,?,?,?)",((d,r[0],r[3],"CANDIDATE_COLOCATION") for r in rs))
    for id,i,o,name,icon in items:
        # Native IconName exact path, not ItemID formatting.
        target=paths.get("ui/tex/icon_item/"+icon+"/"+icon+".bntx") if re.fullmatch(r"[A-Za-z0-9_]+",icon) else None
        db.execute("INSERT INTO item VALUES(?,?,?,?,?,?,?)",(id,i,o,name,icon,target[0] if target else None,"NATIVE_ICON_NAME_EXACT_PATH" if target else "MISSING_OR_UNSUPPORTED_ICON_PATH"))

def import_ui(db,pack):
    report=json.loads((pack/"summary.json").read_text(encoding="utf-8"))
    ref=report["source_commit"]
    aliases=collections.defaultdict(list); mismatch=[]; included=set()
    for s in read_jsonl(pack/"source.jsonl"):
        if s["status"]!="PARSED": continue
        row=db.execute("SELECT resource_id,blob FROM source WHERE path=?",(s["path"],)).fetchone()
        if not row or row[1]!=s["blob"]:
            mismatch.append(s["path"]); continue
        aliases[s["blob"]].append(row[0]); included.add(s["path"])
    if mismatch: raise ValueError("UI source blob mismatches: "+repr(mismatch[:10]))
    if not aliases: raise ValueError("no verified UI source aliases")
    members={(m["blob"],m["member_index"]):m for m in read_jsonl(pack/"member.jsonl")}
    rejected=0
    for t in read_jsonl(pack/"texture.jsonl"):
        b=t["blob"]; mi=t["member_index"]; ti=t["texture_index"]; k=(b,mi,ti)
        if b not in aliases: rejected+=1; continue
        m=members[(b,mi)]
        db.execute("INSERT INTO ui_texture VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(*k,t["name"],t["category"],t["width"],t["height"],t["format"],t["rgba_sha256"],t["status"],m["name"],m["sha256"]))
        db.executemany("INSERT INTO ui_texture_source VALUES(?,?,?,?)",((*k,id) for id in aliases[b]))
        db.executemany("INSERT INTO ui_candidate VALUES(?,?,?,?,?,?)",((*k,s,"CANDIDATE_NAME_ONLY",None) for s in semantic(t["name"],t["category"])))
    db.execute("INSERT INTO metadata VALUES(?,?)",("ui_source_commit",ref))
    return dict(verified_alias_paths=len(included),excluded_texture_rows=rejected,ui_source_commit=ref)

def summarize(db):
    def count(q): return db.execute(q).fetchone()[0]
    return dict(
        pokemon_catalog=count("SELECT COUNT(*) FROM pokemon_catalog"),
        pokemon_icons=count("SELECT COUNT(*) FROM pokemon_icon"),
        pokemon_icons_unmatched=count("SELECT COUNT(*) FROM pokemon_icon WHERE status='UNMATCHED'"),
        pokemon_icons_ambiguous=count("SELECT COUNT(*) FROM (SELECT resource_id FROM pokemon_icon_candidate GROUP BY resource_id HAVING COUNT(*)>1)"),
        pokemon_gender_shiny_confirmed=0,
        items=count("SELECT COUNT(*) FROM item"),
        distinct_native_icon_names=count("SELECT COUNT(DISTINCT icon_name) FROM item"),
        item_exact_path=count("SELECT COUNT(*) FROM item WHERE icon_resource_id IS NOT NULL"),
        item_missing=count("SELECT COUNT(*) FROM item WHERE icon_resource_id IS NULL"),
        item_exact_brti_name=count("SELECT COUNT(DISTINCT item_id) FROM item_texture_candidates"),
        shared_icon_names=count("SELECT COUNT(*) FROM item_icon_usage WHERE item_count>1"),
        ui_textures=count("SELECT COUNT(*) FROM ui_texture"),
        ui_decoded_candidates=count("SELECT COUNT(*) FROM ui_texture WHERE decode_status='DECODED_CANDIDATE'"),
        ribbon_mark_keyword_rows=count("SELECT COUNT(*) FROM ui_candidate WHERE semantic='ribbon_or_mark_keyword'"),
        catalog_exact_paths=count("SELECT COUNT(*) FROM catalog_slot WHERE resolved_id IS NOT NULL"),
        catalog_missing_paths=count("SELECT COUNT(*) FROM catalog_slot WHERE resolved_id IS NULL"),
        model_directory_groups=count("SELECT COUNT(*) FROM model_group"),
        model_members=count("SELECT COUNT(*) FROM model_member"),
        model_geometry_verified=False,ui_business_ids_confirmed=False,independent_pixel_parity=False)

def self_test():
    def rec(p,kind,domain,cat):
        return ((rid(p),p,PurePosixPath(p).name,PurePosixPath(p).suffix,kind,domain,cat,"RAW","a"*40),[])
    records=[rec("ik_pokemon/data/pm0001/pm0001_00_00/a.trmdl","model","model","pokemon"),
        rec("ik_pokemon/data/pm0001/pm0001_00_00/icon/pm0001_00_00_00_0.bntx","texture","image","pokemon"),
        rec("ui/tex/icon_item/item_0001/item_0001.bntx","texture","image","items")]
    c=dict(index=1,table_offset=12,key_raw=[1,0,0],personal=dict(national_raw=1,present=True),resource_dir="pm0001/pm0001_00_00",slots={"1":"pm0001/pm0001_00_00/a.trmdl","6":"absent.bntx"})
    with sqlite3.connect(":memory:") as db:
        db.executescript(SCHEMA)
        core(db,records,[c],[(1,0,10,"A","item_0001"),(999,1,20,"B","item_0001"),(3,2,30,"C","missing")])
        s=summarize(db); assert s["item_exact_path"]==2 and s["item_missing"]==1 and s["shared_icon_names"]==1
        assert s["catalog_exact_paths"]==1 and s["catalog_missing_paths"]==1
        assert db.execute("SELECT gender,shiny FROM pokemon_icon").fetchone()==(None,None)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        assert "box_marking_name" in semantic("icon_marking_00^s","ui")
        assert "ribbon_or_mark_keyword" not in semantic("icon_marking_00^s","ui")
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/"summary.json").write_text(json.dumps({"source_commit":"fixture"}))
            for name,rows in {"source":[dict(path=records[2][0][1],blob="a"*40,status="PARSED")],
                "member":[dict(blob="a"*40,member_index=-1,name=None,sha256="fixture")],
                "texture":[dict(blob="a"*40,member_index=-1,texture_index=0,name="item_0001",category="items",width=160,height=160,format="BC7",rgba_sha256="fixture",status="DECODED_CANDIDATE")]}.items():
                (p/(name+".jsonl")).write_text("".join(json.dumps(r)+"\n" for r in rows))
            import_ui(db,p)
            assert summarize(db)["item_exact_brti_name"]==2
            assert not db.execute("PRAGMA foreign_key_check").fetchall()
    print("Four resource cores synthetic tests passed")

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--self-test",action="store_true"); p.add_argument("--ui-manifests",type=Path,required=False); p.add_argument("--out",type=Path,default=Path(".za-work/ZAResourceCores")); a=p.parse_args()
    if a.self_test: self_test(); return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()) or a.out.resolve()==Path(".za-work").resolve(): p.error("local output required")
    if a.out.exists() and any(a.out.iterdir()): p.error("output must be empty")
    ref=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    records=list(census.inventory(subprocess.check_output(["git","ls-tree","-rz",ref,"--",str(V)])))
    paths={r[1]:r for r,m in records}
    def checked(path):
        b=(V/path).read_bytes()
        if hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()!=paths[path][8]: raise ValueError("native blob mismatch "+path)
        return b
    cb,pb,ib=checked(CAT),checked(PERSONAL),checked(ITEM)
    catalog=native.catalog(cb,native.personal(pb)); items=item_rows(ib)
    if len(catalog)!=637 or len(items)!=535: raise ValueError("unexpected v2.0.2 native row count")
    a.out.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(a.out/"resource-cores.sqlite") as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO metadata VALUES(?,?)",[("source_commit",ref),("version","2.0.2"),("catalog_sha256",sha(cb)),("personal_sha256",sha(pb)),("item_sha256",sha(ib)),("item_schema","tools/pkNX/FlatBuffers/ZA/Item/Schemas/ItemDataArray.fbs")])
        core(db,records,catalog,items)
        ui=import_ui(db,a.ui_manifests) if a.ui_manifests else {"ui_import":"NOT_REQUESTED"}
        if not a.ui_manifests: print("UI artifact not supplied; UI tables empty")
        s=dict(source_commit=ref,source_paths=len(records),**ui,**summarize(db))
        assert db.execute("PRAGMA integrity_check").fetchone()==("ok",)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        for table in ("item","pokemon_icon_keys","catalog_slot","ui_candidate","model_group"):
            cur=db.execute("SELECT * FROM "+table)
            cols=[x[0] for x in cur.description]
            with (a.out/(table+".jsonl")).open("w",encoding="utf-8") as f:
                for row in cur: f.write(json.dumps(dict(zip(cols,row)),ensure_ascii=True)+"\n")
    (a.out/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8"); print(json.dumps(s,indent=2))
if __name__=="__main__": main()
