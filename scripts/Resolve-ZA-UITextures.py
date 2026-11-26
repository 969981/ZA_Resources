#!/usr/bin/env python3
"""Static texture-pattern resolution and global UI texture name/pixel index."""
import argparse, collections, json, re, sqlite3
from pathlib import Path
def rows(p):
    with p.open(encoding="utf-8") as f:
        for l in f:
            if l.strip(): yield json.loads(l)
def key(t): return (t["blob"],t["member_index"],t["texture_index"])
def domain(name):
    n=name.lower()
    # Evidence labels, not native gameplay IDs. Keep overlaps.
    rules={
      "types":r"(?:icon_type|type_icon|type_text|type_bg|type_base)",
      "balls":r"(?:icon_ball|ball_icon|monsterball|monster_ball|pokeball|ball_(?:parts|set|bg|btn)|trainer_ball)",
      "badges":r"(?:badge|medal|achievement|trophy|kunsho|kunsyo|shogo|shougou|emblem|rank|ryl)",
      "ribbons":r"(?:ribbon|mark_icon|icon_mark|akashi)",
      "moves":r"(?:waza|move_category|skill_category|buturi|butsuri|tokushu|henka|physical|special)",
      "status":r"(?:icon_sick|icon_status|sick_icon|status_icon|condition|ailment)",
      "items":r"(?:icon_item|item_icon|^item_\d+)",
      "donuts":r"(?:donut|doughnut)",
      "hidden_ui":r"(?:dummy|placeholder|debug|unknown|secret|hidden|unreleased)",
    }
    return [k for k,v in rules.items() if re.search(v,n)]
def uv_class(uv):
    if not uv: return "NO_UV"
    if len(uv)!=1: return "MULTI_UV"
    a=uv[0]
    if len(a)!=8:return "INVALID"
    if a==[0,0,1,0,0,1,1,1]:return "FULL"
    x0,y0,x1,y1,x2,y2,x3,y3=a
    near=lambda x,y: abs(x-y)<1e-6
    if not (near(x0,x2) and near(x1,x3) and near(y0,y1) and near(y2,y3)):return "NON_AXIS_ALIGNED"
    if near(x0,x1) or near(y0,y2):return "DEGENERATE"
    if min(a)<-1e-6 or max(a)>1+1e-6:return "OUTSIDE_0_1"
    if x1<x0 or y2<y0:return "FLIPPED_RECT"
    return "SUBRECT"
def resolve(name,blob,local,global_index):
    if name is None:return "NO_NAME",[]
    loc=local.get((blob,name),[])
    if loc:return ("LOCAL_EXACT" if len(loc)==1 else "LOCAL_AMBIGUOUS"),loc
    matches=global_index.get(name,[])
    if not matches:return "MISSING",[]
    pixels={(x["width"],x["height"],x["rgba_sha256"]) for x in matches}
    if len(matches)==1:return "GLOBAL_UNIQUE_NAME_CANDIDATE",matches
    if len(pixels)==1 and None not in next(iter(pixels)):return "GLOBAL_PIXEL_EQUIVALENT_CANDIDATE",matches
    return "GLOBAL_AMBIGUOUS",matches
def compact(t):
    return dict(blob=t["blob"],member_index=t["member_index"],texture_index=t["texture_index"],name=t["name"],width=t["width"],height=t["height"],rgba_sha256=t["rgba_sha256"])
def audit(layout,pack,out):
    out.mkdir(parents=True,exist_ok=True)
    counts=collections.Counter(); local=collections.defaultdict(list); glob=collections.defaultdict(list); pixel=collections.defaultdict(list)
    aliases=collections.defaultdict(list); archive_layout=collections.defaultdict(list); hitnames=collections.defaultdict(set); hitpixels=collections.defaultdict(set); families=collections.Counter()
    for s in rows(pack/"source.jsonl"):
        if s["blob"]:aliases[s["blob"]].append(s["path"])
    db=sqlite3.connect(out/"ui-index.sqlite")
    db.executescript("""CREATE TABLE texture(blob TEXT,member_index INTEGER,texture_index INTEGER,name TEXT,width INTEGER,height INTEGER,rgba_sha256 TEXT,category TEXT,domains TEXT,PRIMARY KEY(blob,member_index,texture_index));
    CREATE INDEX by_name ON texture(name);
    CREATE INDEX by_pixels ON texture(width,height,rgba_sha256);
    CREATE TABLE source_alias(blob TEXT,path TEXT);
    CREATE TABLE pattern(blob TEXT,animation TEXT,track_offset INTEGER,target TEXT,target_type INTEGER,frame REAL,value_raw INTEGER,texture_name TEXT,status TEXT,target_status TEXT,candidates TEXT);
    CREATE TABLE layout_ref(blob TEXT,layout TEXT,texture_name TEXT,status TEXT,candidates TEXT);
    """)
    for oid,ps in aliases.items():db.executemany("INSERT INTO source_alias VALUES(?,?)",[(oid,p) for p in ps])
    with (out/"semantic-candidates.jsonl").open("w",encoding="utf-8") as f:
        for t in rows(pack/"texture.jsonl"):
            c=compact(t); name=t["name"]; local[(t["blob"],name)].append(c); glob[name].append(c)
            if t["rgba_sha256"]:pixel[(t["width"],t["height"],t["rgba_sha256"])].append(c)
            tags=domain(name); counts["textures"]+=1
            db.execute("INSERT INTO texture VALUES(?,?,?,?,?,?,?,?,?)",(*key(t),name,t["width"],t["height"],t["rgba_sha256"],t["category"],json.dumps(tags)))
            if tags:
                for tag in tags:
                    counts["candidate:"+tag]+=1; hitnames[tag].add(name)
                    if t["rgba_sha256"]:hitpixels[tag].add((t["width"],t["height"],t["rgba_sha256"]))
                f.write(json.dumps(dict(**c,domains=tags,source_paths=aliases[t["blob"]],status="NAME_CANDIDATE"),ensure_ascii=True)+"\n")
    counts["distinct_names"]=len(glob); counts["distinct_rgba_dimension_groups"]=len(pixel)
    counts["duplicate_pixel_rows"]=sum(len(v)-1 for v in pixel.values())
    for d in hitnames:counts["distinct_name:"+d]=len(hitnames[d]); counts["distinct_pixel:"+d]=len(hitpixels[d])
    with (out/"layout-refs.jsonl").open("w",encoding="utf-8") as f,(out/"uv-audit.jsonl").open("w",encoding="utf-8") as uvf:
        for l in rows(layout/"layouts.jsonl"):
            b=l["blob"]; member=l["member"]["name"]
            mats=collections.defaultdict(list)
            for m in l["materials"]:mats[m["name"]].append(dict(index=m["index"],texture_maps=m["texture_maps"],flags=m["flags"]))
            panes={p["name"] for p in l["panes"]}
            archive_layout[b].append((member,mats,panes))
            for name in l["textures"]:
                status,c=resolve(name,b,local,glob);counts["layout:"+status]+=1
                db.execute("INSERT INTO layout_ref VALUES(?,?,?,?,?)",(b,member,name,status,json.dumps(c)))
                if status!="LOCAL_EXACT":f.write(json.dumps(dict(blob=b,layout=member,name=name,status=status,candidates=c))+"\n")
            for p in l["pictures"]:
                status=uv_class(p["uv"]); counts["uv:"+status]+=1
                if status!="FULL":uvf.write(json.dumps(dict(blob=b,layout=member,pane=p["name"],uv=p["uv"],texture_names=p["texture_names"],uv_class=status,crop_verified=False))+"\n")
    with (out/"pattern-resolutions.jsonl").open("w",encoding="utf-8") as f:
        for a in rows(layout/"animations.jsonl"):
            b=a["blob"]; member=a["member"]["name"]
            for p in a["patterns"]:
                counts["pattern_tracks"]+=1; ts=[]
                for lay,mats,panes in archive_layout[b]:
                    if p["target_type"]==1:
                        for m in mats.get(p["target"],[]):ts.append(dict(layout=lay,**m))
                    elif p["target_type"]==0 and p["target"] in panes:ts.append(dict(layout=lay,pane=p["target"]))
                target_status="TARGET_UNIQUE_CANDIDATE" if len(ts)==1 else "TARGET_AMBIGUOUS" if ts else "TARGET_MISSING"
                counts[target_status]+=1; resolved=[]
                if p.get("unsupported_key_type"):counts["unsupported_pattern_key_type"]+=1
                frames=[k["frame"] for k in p["keys"]]
                if frames!=sorted(frames) or len(set(frames))!=len(frames):counts["non_strict_key_order"]+=1
                for k in p["keys"]:
                    name=k.get("texture_candidate"); status,c=resolve(name,b,local,glob); counts["pattern_key:"+status]+=1
                    db.execute("INSERT INTO pattern VALUES(?,?,?,?,?,?,?,?,?,?,?)",(b,member,p["offset"],p["target"],p["target_type"],k["frame"],k["value_raw"],name,status,target_status,json.dumps(c)))
                    resolved.append(dict(**k,status=status,candidates=c))
                f.write(json.dumps(dict(blob=b,animation=member,track=p,target_status=target_status,target_candidates=ts,resolved_keys=resolved,runtime_verified=False),ensure_ascii=True)+"\n")
    db.commit();db.close()
    result=dict(counts=dict(counts),native_id_mapping_complete=False,runtime_selector_verified=False,global_name_match_is_candidate=True,pixel_hash_identity_includes_dimensions=True)
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,indent=2))
    if not counts["textures"] or not counts["pattern_tracks"]:raise SystemExit("missing audit input")
def self_test():
    assert uv_class([[0,0,1,0,0,1,1,1]])=="FULL"
    assert uv_class([[0,0,.5,0,0,.5,.5,.5]])=="SUBRECT"
    assert uv_class([[1,0,0,0,1,1,0,1]])=="FLIPPED_RECT"
    assert uv_class([[0,0,2,0,0,1,2,1]])=="OUTSIDE_0_1"
    assert "types" in domain("grptxt_icon_type_00_normal_00^s")
    a=dict(width=32,height=32,rgba_sha256="a")
    assert resolve("x","b",{},{"x":[a,a]})[0]=="GLOBAL_PIXEL_EQUIVALENT_CANDIDATE"
    assert resolve("x","b",{},{"x":[a,dict(a,rgba_sha256="b")]})[0]=="GLOBAL_AMBIGUOUS"
    assert resolve("x","b",{("b","x"):[a]},{"x":[a,a]})[0]=="LOCAL_EXACT"
    print("UI name/pixel/UV resolver fixtures passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--layout",type=Path,default=Path(".za-work/ui-layout"));p.add_argument("--pack",type=Path,default=Path(".za-work/ZAImageResources/manifests"));p.add_argument("--out",type=Path,default=Path(".za-work/ui-resolver"));a=p.parse_args()
    if a.self_test:self_test();return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("output must be local")
    audit(a.layout,a.pack,a.out)
if __name__=="__main__":main()
