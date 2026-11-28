#!/usr/bin/env python3
"""Read-only ZA v2.0.2 native path catalog; no asset bytes or guessed IDs."""
import argparse
import collections
import csv
import hashlib
import json
import re
import sqlite3
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

ROOT = "Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/"
VERSION = "2.0.2"
PART = re.compile(r"\.7z\.(\d+)$", re.I)
IMAGES = set(".bntx .dds .png .jpg .jpeg .tga .ktx .ktx2 .webp .bmp .bflim".split())
MODELS = set(".trmdl .trmsh .trmbf .trmtr .trmmt .trskl .trpokecfg .hkx".split())
ANIM = set(".tranm .tracm .traef .trcrv .tracl .tracn .tracp .tracr .tracs .tralk .trmdt .trslp .trmdd".split())
UI = set(".arc .truiv .bflyt .bflan .bffnt .bfotf .bfcpx".split())
PACKS = {
    "ZAImageResources": "pokemon items balls types moves ribbons marks markings badges status donuts characters clothing logos maps illustrations ui atlases".split(),
    "ZAModelResources": "pokemon characters clothing balls items buildings environment animations materials textures effects".split(),
    "ZAMapResources": "world wild_zones dungeons hyperspace minimap locations spawn_points navmesh geojson tiles".split(),
}
TEX_CATEGORIES = {"icon_item":"items","icon_donut":"donuts","chara":"characters","hud_shopping":"clothing",
                  "map_pic":"maps","logo_brand":"logos","onepicture":"illustrations","tips":"illustrations",
                  "ryl_npc":"characters","icon_pokemon_last":"pokemon","poke_spmg":"pokemon"}

def git(*args):
    return subprocess.check_output(["git", *args])

def classify(path):
    p = path.lower()
    ext = PurePosixPath(p).suffix
    top = p.split("/", 1)[0]
    kind = ("texture" if ext in IMAGES else "model" if ext in MODELS else
            "animation" if ext in ANIM else "ui_container" if ext in UI else "other")
    if p.startswith("ui/tex/"):
        return kind, "image", TEX_CATEGORIES.get(p.split("/")[2], "ui")
    if p.startswith("ui/data/") or p.startswith("ui/font/") or p.startswith("ui/system/"):
        if p.startswith(("ui/data/map_dungeon/","ui/data/hud_minimap_dungeon/")):
            return kind, "map", "dungeons"
        if p.startswith("ui/data/hud_minimap/"):
            return kind, "map", "minimap"
        if p.startswith("ui/data/map/"):
            return kind, "map", "hyperspace" if "map_field_dim" in p else "world"
        return kind, "image", "types" if p.endswith("/dummy_icon_type.arc") else "ui"
    if top == "ik_pokemon" and "/icon/" in p:
        return kind, "image", "pokemon"
    if top in {"ik_pokemon", "ik_chara", "field", "ik_effect"}:
        if p.startswith("field/navmesh/"):
            return kind, "map", "navmesh"
        if top == "ik_effect":
            return kind, "model", "effects"
        if kind == "animation" or p.startswith("ik_chara/motion_"):
            cat = "animations"
        elif ext in {".trmtr", ".trmmt"}:
            cat = "materials"
        elif ext in IMAGES:
            cat = "textures"
        elif top == "ik_pokemon":
            cat = "pokemon"
        elif p.startswith("ik_chara/model_ob/"):
            cat = "balls" if re.search(r"/ob\d+_\d+_[^/]*ball(?:/|$)", p) else "items"
        elif p.startswith("ik_chara/model_cc"):
            cat = "clothing"
        elif top == "ik_chara":
            cat = "characters"
        else:
            cat = "environment"
        return kind, "model", cat
    if top == "world":
        return kind, "map", "world"
    if top == "ik_message":
        return kind, "localization", "messages"
    return kind, "other", top

def inventory(data):
    groups = collections.defaultdict(list)
    for row in data.split(b"\0"):
        if not row:
            continue
        meta, raw = row.split(b"\t", 1)
        mode, typ, oid = meta.decode("ascii").split()
        full = raw.decode("utf-8")
        if typ != "blob" or not full.startswith(ROOT):
            continue
        path = full[len(ROOT):]
        m = PART.search(path)
        logical = path[:m.start()] if m else path
        groups[logical].append((full, oid, int(m.group(1)) if m else None, mode))
    for path, members in sorted(groups.items()):
        parts = sorted(m[2] for m in members if m[2] is not None)
        raws = [m for m in members if m[2] is None]
        regular = all(m[3] in {"100644","100755"} for m in members)
        if regular and len(raws) == 1 and not parts:
            state = "RAW"
        elif regular and not raws and parts and parts == list(range(1, max(parts)+1)):
            state = "VOLUMES_UNVERIFIED"
        else:
            state = "AMBIGUOUS_OR_GAPPED"
        kind, domain, category = classify(path)
        rid = hashlib.sha256((VERSION+"\0"+path).encode()).hexdigest()
        yield (rid, path, PurePosixPath(path).name, PurePosixPath(path).suffix.lower(),
               kind, domain, category, state, raws[0][1] if state == "RAW" else None), members

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE resource(
 resource_id TEXT PRIMARY KEY, native_path TEXT NOT NULL UNIQUE, native_name TEXT NOT NULL,
 extension TEXT NOT NULL, kind TEXT NOT NULL, domain TEXT NOT NULL, category TEXT NOT NULL,
 representation TEXT NOT NULL, git_blob_sha TEXT,
 source_sha256 TEXT, format TEXT, width INTEGER, height INTEGER, pixel_sha256 TEXT,
 export_path TEXT, evidence_level TEXT NOT NULL DEFAULT 'CONFIRMED',
 classification_evidence TEXT NOT NULL DEFAULT 'CANDIDATE',
 CHECK(evidence_level IN ('CONFIRMED','CANDIDATE','UNKNOWN','REJECTED')),
 CHECK(classification_evidence IN ('CONFIRMED','CANDIDATE','UNKNOWN','REJECTED'))
);
CREATE TABLE storage(
 resource_id TEXT NOT NULL REFERENCES resource(resource_id), stored_path TEXT PRIMARY KEY,
 git_blob_sha TEXT NOT NULL, part_number INTEGER, git_mode TEXT NOT NULL
);
CREATE TABLE mapping(
 mapping_id INTEGER PRIMARY KEY, resource_id TEXT NOT NULL REFERENCES resource(resource_id),
 archive_member TEXT, species_id INTEGER, form_id INTEGER, gender INTEGER, shiny INTEGER,
 item_id INTEGER, ball_id INTEGER, type_id INTEGER, move_id INTEGER, ribbon_id INTEGER,
 mark_id INTEGER, language TEXT, evidence_level TEXT NOT NULL,
 evidence_ref TEXT NOT NULL,
 CHECK(evidence_level IN ('CONFIRMED','CANDIDATE','UNKNOWN','REJECTED'))
);
CREATE INDEX resource_domain ON resource(domain,category,kind);
CREATE INDEX resource_blob ON resource(git_blob_sha);
CREATE INDEX mapping_resource ON mapping(resource_id);
CREATE VIEW source_index AS SELECT r.*,s.stored_path,s.part_number,s.git_mode
 FROM resource r JOIN storage s USING(resource_id);
"""

def write_db(path, rows, ref, scope):
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO metadata VALUES (?,?)", [
            ("source_commit",ref),("game_version",VERSION),("source_root",ROOT),
            ("schema_version","1"),("scope",scope),("mapping_status","UNKNOWN"),
            ("byte_verification","NOT_RUN")])
        for record, members in rows:
            db.execute("INSERT INTO resource(resource_id,native_path,native_name,extension,kind,domain,category,representation,git_blob_sha) VALUES (?,?,?,?,?,?,?,?,?)", record)
            db.executemany("INSERT INTO storage VALUES (?,?,?,?,?)",
                           [(record[0],p,oid,n,mode) for p,oid,n,mode in members])
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        assert db.execute("SELECT COUNT(*) FROM resource").fetchone()[0] == len(rows)

def build(rows, ref, out):
    if not rows:
        raise ValueError("empty source catalog")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("output must be new or empty; use a different directory")
    out.mkdir(parents=True, exist_ok=True)
    for pack, cats in PACKS.items():
        for cat in cats:
            (out/pack/cat).mkdir(parents=True, exist_ok=True)
    dbdir = out/"ZAResourceDatabase"
    dbdir.mkdir()
    write_db(dbdir/"catalog.sqlite", rows, ref, "all_virtual_paths")
    scopes = {
        "images": lambda r: r[5]=="image" or (r[5]=="map" and r[4] in {"texture","ui_container"}),
        "models": lambda r: r[5]=="model",
        "maps": lambda r: r[5]=="map" or (r[5]=="image" and r[6]=="maps"),
        "pokemon": lambda r: r[1].startswith("ik_pokemon/"),
        "localization": lambda r: r[5]=="localization" or bool(re.search(r"_(eng|fre|ger|ita|kor|ltm|spa|sch|tch)\.", r[1].lower())),
    }
    counts = {}
    for name, pred in scopes.items():
        subset = [(r,m) for r,m in rows if pred(r)]
        write_db(dbdir/(name+".sqlite"), subset, ref, name)
        counts[name] = len(subset)
    group = collections.Counter((r[5],r[6],r[4],r[3],r[7]) for r,m in rows)
    with (out/"category-summary.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f)
        w.writerow(["domain","category","kind","extension","representation","logical_paths"])
        w.writerows([(*k,v) for k,v in sorted(group.items())])
    with (out/"inventory.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f)
        w.writerow(["resource_id","native_path","native_name","extension","kind","domain","category","representation","git_blob_sha"])
        w.writerows(r for r,m in rows)
    summary = dict(source_commit=ref, game_version=VERSION, source_root=ROOT,
        logical_paths=len(rows), stored_paths=sum(len(m) for r,m in rows),
        representation=dict(collections.Counter(r[7] for r,m in rows)),
        domains=dict(collections.Counter(r[5] for r,m in rows)), database_scope_counts=counts,
        raw_distinct_git_blobs=len({r[8] for r,m in rows if r[8]}),
        original_hash_reconciled=False, archive_contents_verified=False,
        pixels_decoded=False, model_geometry_parsed=False, business_ids_confirmed=False,
        notes="Path-level census only. Domain subsets overlap. Volume tail completeness is not proven. No original bytes exported.")
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

def self_test():
    def entry(path, oid="a"*40):
        return ("100644 blob "+oid+"\t"+ROOT+path+"\0").encode()
    data = b"".join(entry(p) for p in [
        "ui/tex/icon_item/item_0001/item_0001.bntx",
        "ui/tex/icon_item/item_0002/item_0002.bntx",
        "ik_pokemon/data/pm0001/x/icon/a.bntx",
        "ik_pokemon/data/pm0001/x/a.trmdl",
        "ui/data/map/a.arc.7z.001","ui/data/map/a.arc.7z.002",
        "ui/data/map/b.arc.7z.002","field/navmesh/a.bin",
        "ik_message/a.dat","_unknown/abc","ui/data/box/a_sch.arc"])
    rows=list(inventory(data))
    assert len(rows)==10
    assert sum(len(m) for r,m in rows)==11
    assert sum(r[7]=="VOLUMES_UNVERIFIED" for r,m in rows)==1
    assert sum(r[7]=="AMBIGUOUS_OR_GAPPED" for r,m in rows)==1
    assert classify("ik_chara/model_ob/ob0201_00_masterball/a.trmdl")==("model","model","balls")
    assert classify("field/navmesh/a.bin")[1:]==("map","navmesh")
    with tempfile.TemporaryDirectory() as tmp:
        out=Path(tmp)/"result"
        build(rows,"synthetic",out)
        with sqlite3.connect(out/"ZAResourceDatabase/catalog.sqlite") as db:
            assert db.execute("SELECT count(*) FROM mapping").fetchone()[0]==0
            assert db.execute("SELECT count(*) FROM source_index").fetchone()[0]==11
        assert (out/"ZAImageResources/ribbons").is_dir()
    print("synthetic complete resource catalog tests passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ref",default="HEAD")
    p.add_argument("--out",type=Path,default=Path(".za-work/ZACompleteResources"))
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:
        self_test()
        return
    repo=Path(git("rev-parse","--show-toplevel").decode().strip()).resolve()
    out=args.out.resolve()
    local=repo/".za-work"
    if not out.is_relative_to(local) or out==local:
        p.error("--out must be a subdirectory of the repository .za-work directory")
    ref=git("rev-parse",args.ref+"^{commit}").decode().strip()
    data=git("-C",str(repo),"ls-tree","-rz",ref,"--",ROOT)
    build(list(inventory(data)),ref,out)

if __name__=="__main__":
    main()
