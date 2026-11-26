#!/usr/bin/env python3
"""Offline audit of exact prior metadata: zero-length flag, FLTS frame ordering, capture gaps."""
import argparse, collections, json, math
from pathlib import Path
def rows(path):
    with path.open(encoding="utf-8") as f:
        for l in f:
            if l.strip():yield json.loads(l)
def audit(material,dynamic,out):
    out.mkdir(parents=True,exist_ok=True);counts=collections.Counter();flag=collections.Counter();flag815=collections.Counter();orders=collections.Counter();examples=collections.defaultdict(list)
    def ex(k,v):
        if len(examples[k])<5:examples[k].append(v)
    with (out/"flag815.jsonl").open("w",encoding="utf-8") as f:
        for m in rows(material/"materials.jsonl"):
            counts["materials"]+=1
            if m["status"]=="PARTIAL":flag[(m["flags"],m["size"],m.get("reason"))]+=1
            if m["flags"]!=0x815:continue
            counts["flag815"]+=1
            # 0x800 not interpreted; test whether base parser consumed entire record.
            empty=m.get("unparsed_tail_hex")==""
            blocks=m.get("blocks",[])
            exact=(m["size"]==84 and empty and [(x["kind"],x["offset"],x["size"]) for x in blocks]==[("map",44,4),("srt",48,20),("coord_candidate",68,16)])
            counts["flag815_boundary_match" if exact else "flag815_other"]+=1
            flag815[(m["size"],m.get("unknown_bits"),m.get("reason"))]+=1
            f.write(json.dumps(dict(path=m["path"],member=m["member"],index=m["index"],name=m["name"],sha256=m["record_sha256"],flags=m["flags"],size=m["size"],boundary_match=exact,semantic_verified=False))+"\n")
    with (out/"flts-order.jsonl").open("w",encoding="utf-8") as f:
        for a in rows(dynamic/"flts.jsonl"):
            counts["flts_tracks"]+=1
            ks=a["keys"];frames=[k["frame"] for k in ks]
            desc=sum(x>y for x,y in zip(frames,frames[1:]));eq=sum(x==y for x,y in zip(frames,frames[1:]))
            byframe=collections.defaultdict(set)
            for k in ks:byframe[k["frame"]].add((k.get("value"),k.get("tangent"),k.get("value_raw")))
            conflict=sum(len(v)>1 for v in byframe.values())
            label="DESCENDING" if desc else "DUPLICATE_CONFLICT" if conflict else "DUPLICATE_IDENTICAL" if eq else "STRICT"
            orders[label]+=1
            if eq or desc:
                row=dict(path=a["path"],member=a["member"],target=a["target"],index=a["index"],property=a["property"],offset=a["offset"],key_count=len(ks),descending_pairs=desc,equal_pairs=eq,conflicting_frames=conflict,classification=label,keys=ks)
                f.write(json.dumps(row)+"\n");ex(label,dict(**{k:row[k] for k in ("path","member","target","index","property","key_count","descending_pairs","equal_pairs","conflicting_frames")},first_keys=ks[:5]))
    gaps=[]
    for c in rows(dynamic/"captures.jsonl"):
        counts["capture_records"]+=1
        if c["status"]!="CAPTURE_SOURCE_UNIQUE":gaps.append(dict(path=c["path"],blob=c["blob"],member=c["member"],name=c["name"],source_pane=c["source_pane"],status=c["status"]))
    result=dict(counts=dict(counts),frame_order=dict(orders),partial_flags=[dict(flags=f"0x{a:08X}",size=b,reason=c,count=n) for (a,b,c),n in flag.most_common()],flag815_profiles=[dict(size=a,unknown_bits=b,reason=c,count=n) for (a,b,c),n in flag815.most_common()],capture_gaps=gaps,examples=dict(examples),native_semantics_verified=False)
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,indent=2))
    if not counts["materials"] or not counts["flts_tracks"]:raise SystemExit("missing inputs")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--material",type=Path,default=Path(".za-work/ui-material"));p.add_argument("--dynamic",type=Path,default=Path(".za-work/ui-dynamic"));p.add_argument("--out",type=Path,default=Path(".za-work/ui-edge"));a=p.parse_args()
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("local output only")
    audit(a.material,a.dynamic,a.out)
if __name__=="__main__":main()
