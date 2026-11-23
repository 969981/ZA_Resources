#!/usr/bin/env python3
"""Read-only ZA v2.0.2 Spawner -> Encounter -> scene -> PKHeX audit.

Use complete original resources. Static configuration != runtime spawn proof.
Writes five derived CSVs and a machine-readable summary, never game binaries.
"""
import argparse
import csv
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from za_resource_inspect import FB

ROOT = "world/ik_data/field/"
FILES = {
    "enc": ROOT+"pokemon/encount_data/encount_data/encount_data_array.bin",
    "sp": ROOT+"pokemon_spawner/pokemon_spawner_data/pokemon_spawner_data_array.bin",
    "tr": ROOT+"spawner_transform_data/pokemon_spawner_transform/pokemon_spawner_transform/pokemon_spawner_transform_array.bin",
    "dim": ROOT+"dimension/dimension_wild_pokemon/dimension_wild_pokemon/dimension_wild_pokemon_array.bin",
}
RARE = {0x1FFFFFFF:1, 0x2FFFFFFF:2, 0x3FFFFFFF:0}

def groups(f):
    return [(g,r,x) for g,a in enumerate(f.tables(f.root(),0))
            for r,x in enumerate(f.tables(a,0))]

def vec_strings(f,t,i):
    off,n=f.vec(t,i)
    return [bytes(f.data[(p:=f.link(off+4*k))+4:p+4+f.u32(p)]).decode("utf8","replace")
            for k in range(n)]

def read_sources(root):
    raw = {k:(root/path).read_bytes() for k,path in FILES.items()}
    f=FB(raw["enc"])
    enc=[dict(db=g,row=r,id=f.string(x,0),dev=f.number(x,1),
        lo=f.number(x,2),hi=f.number(x,3),sex=f.number(x,4),
        form=f.number(x,5),rare=f.number(x,6),nature=f.number(x,8),
        alpha=f.number(x,11,"f32"),boost=f.number(x,12),
        activation=f.vec(x,13)[1]) for g,r,x in groups(f)]
    f=FB(raw["sp"])
    sp=[]
    for g,r,x in groups(f):
        appearances=[]
        for a in f.tables(x,1):
            count=f.obj(a,8)
            appearances.append(dict(name=f.string(a,0),max=f.number(count,1) if count else None,
                min=f.number(count,0) if count else None,
                tags=vec_strings(f,a,5)))
        targets=[]
        for a in f.tables(x,5):
            targets.append(dict(id=f.string(a,0),weight=f.number(a,1),max=f.number(a,2),
                add=f.number(a,3),time=f.number(a,6),weather=f.number(a,7),
                conditions=f.vec(a,9)[1],ui_conditions=f.vec(a,10)[1]))
        cool=f.obj(x,4)
        sp.append(dict(db=g,row=r,id=f.string(x,0),appearances=appearances,
            targets=targets,conditions=f.vec(x,2)[1],ui_conditions=f.vec(x,3)[1],
            cooldown=f.number(cool,1,"f32") if cool else None))
    f=FB(raw["tr"])
    transforms=[f.string(x,0) for _,_,x in groups(f)]
    f=FB(raw["dim"])
    dimension=[]
    for _,_,x in groups(f):
        for rank in f.tables(x,1):
            for pat in f.tables(rank,1):
                for item in f.tables(pat,2):
                    dimension.append(dict(spawner=f.string(item,0),type=f.number(x,0),
                        rank=f.number(rank,0),pattern=f.number(pat,0),
                        pattern_weight=f.number(pat,1),weight=f.number(item,1)))
    return enc,sp,transforms,dimension,raw

def scene_sources(scene_info):
    entries=re.findall(r'ScenePathsT([123])\s*=.*?\[(.*?)\];',scene_info,re.S)
    if len(entries)!=3: raise ValueError("Expected three version-pinned scene lists")
    return [(f"t{t}",p) for t,content in entries
            for p in re.findall(r'"(world/ik_scene/[^"\r\n]+\.trscn)"',content)]

def manual_coordinates(source):
    match=re.search(r'private const string Import\s*=\s*"""(.*?)"""',source,re.S)
    if not match: raise ValueError("Missing ManualPositionRip.Import")
    coords=defaultdict(set)
    for line in match.group(1).strip().splitlines():
        v=line.split(",")
        coords[tuple(float(x) for x in v[2:])].add(int(v[0]))
    return [(xyz,sorted(ids)) for xyz,ids in coords.items()]

def scene_objects(root,scene_info,manual):
    result=[]
    for code,path in scene_sources(scene_info):
        file=root/path
        if not file.is_file(): raise FileNotFoundError(f"Scene missing: {file}")
        f=FB(file.read_bytes())
        for entry in f.tables(f.root(),4):
            if f.string(entry,0)!="trinity_ObjectTemplate": continue
            embedded=FB(f.blob(entry,1)); t=embedded.root()
            if embedded.string(t,4)!="trinity_SceneObject": continue
            obj=FB(embedded.blob(t,5)); o=obj.root()
            shape=obj.string(o,0)
            if shape not in ("pokemon_spawner_box_object","pokemon_spawner_sphere_object",
                             "pokemon_spawner_point_object"): continue
            srt=obj.obj(o,1)
            if srt is None: continue
            xyz=obj.vec3(srt,2)
            if xyz is None: continue
            if code=="t1":
                (nearest,ids)=min(manual,key=lambda z:sum((a-b)**2 for a,b in zip(z[0],xyz)))
                dist=math.dist(nearest,xyz)
            else: ids=[234 if code=="t2" else 235];dist=0
            result.append(dict(name=embedded.string(t,0),scene=path,map=code,
                shape=shape,x=xyz[0],y=xyz[1],z=xyz[2],
                locations="|".join(map(str,ids)),nearest_distance=round(dist,3)))
    return result

def species_map(text):
    m=re.search(r'Table9InternalToNational\s*=>\s*\[(.*?)\];',text,re.S)
    if not m: raise ValueError("Missing pkNX species converter")
    arr=[int(x) for x in re.findall(r'(?<!\w)[+-]?\d+(?!\w)',re.sub(r'//[^\n]*','',m.group(1)))]
    if len(arr)<100: raise ValueError("Species table too short")
    return lambda n:n+arr[n-917] if 917<=n<917+len(arr) else n

def pkl(path):
    b=path.read_bytes()
    if len(b)<8 or b[:2]!=b"za": raise ValueError(f"Invalid PKL: {path}")
    n=struct.unpack_from("<H",b,2)[0]
    offsets=struct.unpack_from("<"+"H"*(n+1),b,4)
    if offsets[0]!=4+(n+1)*2 or offsets[-1]!=len(b): raise ValueError(f"Bad offsets: {path}")
    entries=defaultdict(list)
    for i in range(n):
        begin,end=offsets[i:i+2]
        if (end-begin-4)%8: raise ValueError("PKL area not multiple of 8")
        loc=struct.unpack_from("<H",b,begin)[0]
        for j in range(begin+4,end,8):
            entries[loc].append(struct.unpack_from("<HBBBBBB",b,j))
    return entries

def template_classes(text):
    ids=defaultdict(set)
    for kind in ("Gifts","Static","Trades"):
        m=re.search(r'\b'+kind+r'\s*=\s*\[(.*?)\];',text,re.S)
        if not m: raise ValueError(f"Missing PKHeX {kind} block")
        for line in m.group(1).splitlines():
            if "new(" not in line or "//" not in line:continue
            for id_ in re.findall(r'\(([A-Za-z0-9_-]+)\)',line.split("//",1)[1]):
                ids[id_].add(kind.lower())
    return ids

def matches(slots,loc,key):
    # Scan every template: a partial overlap earlier in the file must not
    # shadow a full-covering template later in the same encounter area.
    has_overlap=False
    for s in slots.get(loc,()):
        if s[:3]==key[:3] and s[5:]==key[5:]:
            if s[3]<=key[3] and key[4]<=s[4]: return "covered"
            if s[3]<=key[4] and key[3]<=s[4]: has_overlap=True
    return "overlap" if has_overlap else "missing"

def write_csv(path,rows):
    if not rows:return
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def audit(enc,sp,transforms,dim,scenes,normal,hyper,convert,templates,out,evidence):
    by_enc=defaultdict(list)
    for e in enc:by_enc[e["id"]].append(e)
    by_scene=defaultdict(list)
    for s in scenes:by_scene[s["name"]].append(s)
    by_hyper=defaultdict(list)
    for d in dim:by_hyper[d["spawner"]].append(d)
    trans_names=set(transforms)
    edge_rows=[];sp_rows=[];enc_links=defaultdict(list);condition_counts=Counter()
    for s in sp:
        appearances=s["appearances"]
        placed=[p for a in appearances for p in by_scene.get(a["name"],())]
        loc=sorted({int(i) for p in placed for i in p["locations"].split("|") if i})
        hyper_ref=bool(by_hyper.get(s["id"]))
        groups=(["scene"] if placed else [])+(["hyperspace"] if hyper_ref else [])
        sp_rows.append(dict(db=s["db"],row=s["row"],id=s["id"],appearances=len(appearances),
            object_names="|".join(a["name"] for a in appearances),
            scene_placements=len(placed),locations="|".join(map(str,loc)),
            nearest_distance=max((p["nearest_distance"] for p in placed),default=""),
            transform_name_matches=sum(a["name"] in trans_names for a in appearances),
            hyperspace_refs=len(by_hyper[s["id"]]),maxcount_enabled=int(any(a["max"] and a["max"]>0 for a in appearances)),
            spawner_conditions=s["conditions"],spawner_ui_conditions=s["ui_conditions"],
            cooldown_time=s["cooldown"],target_count=len(s["targets"]),
            evidence_sources="|".join(groups) or "not_placed_or_dimension_referenced"))
        if s["conditions"] or s["ui_conditions"]:condition_counts["spawner_conditions"]+=1
        for target in s["targets"]:
            if target["conditions"] or target["ui_conditions"] or target["time"] not in (0,-1) or target["weather"] not in (0,-1):
                condition_counts["target_condition_candidates"]+=1
            for e in by_enc.get(target["id"],()):
                enc_links[e["id"]].append(s["id"])
                status=[]
                for kind in groups:
                    for location in (loc if kind=="scene" else [273]):
                        lo=e["lo"]+(target["add"] if kind=="hyperspace" else 0)
                        hi=e["hi"]+(target["add"] if kind=="hyperspace" else 0)
                        for alpha,low,high in ([(0,lo,hi)] if e["alpha"]<100 else [])+(
                            [(1,lo+e["boost"],hi+e["boost"])] if e["alpha"]>0 else []):
                            if e["rare"] not in RARE or e["nature"]!=-1 or not 1<=low<=high<=100:
                                status.append("unsupported");continue
                            table=hyper if kind=="hyperspace" else normal
                            status.append(matches(table,location,(convert(e["dev"]),e["form"],
                                e["sex"]&255,low,high,alpha,RARE[e["rare"]])))
                best=next((t for t in ("covered","overlap","missing","unsupported") if t in status),"no_official_location")
                edge_rows.append(dict(spawner_id=s["id"],encounter_id=e["id"],
                    dev=e["dev"],national=convert(e["dev"]),form=e["form"],level_min=e["lo"],level_max=e["hi"],
                    gender=e["sex"],rare=f'0x{e["rare"]:08X}',alpha=e["alpha"],
                    weight=target["weight"],additional_level=target["add"],time=target["time"],
                    weather=target["weather"],target_conditions=target["conditions"],
                    spawner_conditions=s["conditions"],
                    locations="|".join(map(str,loc)),hyperspace=int(hyper_ref),
                    sources="|".join(groups) or "unplaced_or_dynamic",
                    official_pkl_match=best,
                    official_template="|".join(sorted(templates.get(e["id"],())))))
    linked={e["encounter_id"] for e in edge_rows}
    edge_by_id=defaultdict(list)
    for e in edge_rows:edge_by_id[e["encounter_id"]].append(e)
    enc_rows=[]
    for e in enc:
        ee=edge_by_id[e["id"]]
        classes=sorted(templates.get(e["id"],()))
        scene_linked=any("scene" in r["sources"] or "hyperspace" in r["sources"] for r in ee)
        category=("official_"+("+".join(classes))) if classes else ("configured_spawn" if scene_linked else
            ("spawner_without_scene_or_dimension" if ee else "no_spawner_ref"))
        enc_rows.append(dict(db=e["db"],row=e["row"],id=e["id"],dev=e["dev"],national=convert(e["dev"]),
            form=e["form"],level_min=e["lo"],level_max=e["hi"],gender=e["sex"],
            rare=f'0x{e["rare"]:08X}',nature=e["nature"],alpha=e["alpha"],
            own_conditions=e["activation"],linked_spawners=len(set(enc_links[e["id"]])),
            official_pkl_covered=int(any(r["official_pkl_match"]=="covered" for r in ee)),
            official_template="|".join(classes),category=category))
    out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"za_spawners.csv",sp_rows)
    write_csv(out/"za_encounters.csv",enc_rows)
    write_csv(out/"za_spawner_encounter_edges.csv",edge_rows)
    write_csv(out/"za_dimension_refs.csv",dim)
    write_csv(out/"za_scene_points.csv",scenes)
    summary=dict(version="v2.0.2",status="STATIC_CONFIGURATION_NOT_RUNTIME_PROOF",
        counts=dict(spawners=len(sp),encounters=len(enc),transform_records=len(transforms),
            dimension_refs=len(dim),distinct_dimension_spawners=len({x["spawner"] for x in dim}),scene_points=len(scenes),
            spawners_scene_placed=sum(bool(x["scene_placements"]) for x in sp_rows),
            spawners_hyperspace_referenced=sum(bool(x["hyperspace_refs"]) for x in sp_rows),
            encounter_edges=len(edge_rows),encounters_referenced=len(linked),
            encounters_unreferenced=len(enc)-len(linked),
            encounters_official_pkl_covered=sum(x["official_pkl_covered"] for x in enc_rows)),
        categories=dict(Counter(x["category"] for x in enc_rows)),
        pkl_edge_matches=dict(Counter(x["official_pkl_match"] for x in edge_rows)),
        conditional_candidates=dict(condition_counts),
        missing_encounter_refs=sum(target["id"] not in by_enc for s in sp for target in s["targets"]),
        sources=evidence,
        limitations=["static links do not prove runtime spawning",
          "time/weather/flags raw values not runtime interpreted",
          "T1 locations use pkNX nearest manual coordinate",
          "missing scene reference may mean scripted spawn",
          "PKHeX static/gift/trade exact comment IDs only"])
    (out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for s in ("virtual-root","scene-info","manual","converter","pkhex-templates","pkhex-normal",
              "pkhex-hyperspace","output"):
        p.add_argument("--"+s,type=Path,required=True)
    p.add_argument("--strict",action="store_true")
    a=p.parse_args()
    enc,sp,trans,dim,raw=read_sources(a.virtual_root)
    if a.strict and (len(sp),len(enc),len(trans),len(dim))!=(2211,1966,2108,1500):
        raise ValueError(f"v2.0.2 source mismatch: {(len(sp),len(enc),len(trans),len(dim))}")
    scene_info=a.scene_info.read_text(encoding="utf8")
    scene=scene_objects(a.virtual_root,scene_info,manual_coordinates(a.manual.read_text(encoding="utf8")))
    paths={**{k:a.virtual_root/f for k,f in FILES.items()},
           "scene_info":a.scene_info,"manual":a.manual,"converter":a.converter,
           "pkhex_templates":a.pkhex_templates,"pkhex_normal":a.pkhex_normal,
           "pkhex_hyperspace":a.pkhex_hyperspace}
    evidence=[dict(name=k,size=v.stat().st_size,sha256=hashlib.sha256(v.read_bytes()).hexdigest())
              for k,v in paths.items()]
    summary=audit(enc,sp,trans,dim,scene,pkl(a.pkhex_normal),pkl(a.pkhex_hyperspace),
        species_map(a.converter.read_text(encoding="utf8")),
        template_classes(a.pkhex_templates.read_text(encoding="utf8")),a.output,evidence)
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
