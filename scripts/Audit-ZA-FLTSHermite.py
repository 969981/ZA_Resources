#!/usr/bin/env python3
"""Evaluate duplicate-frame Hermite hypotheses without claiming native semantics."""
import argparse, collections, json, math, bisect
from pathlib import Path
def groups(keys):
    out=[]
    for k in keys:
        if out and k["frame"]<out[-1][0]["frame"]:raise ValueError("descending frames")
        if out and k["frame"]==out[-1][0]["frame"]:out[-1].append(k)
        else:out.append([k])
    return out
def evaluate(gs,t,mode):
    frames=[g[0]["frame"] for g in gs];i=bisect.bisect_right(frames,t)-1
    if i<0:return gs[0][0]["value"]
    if t==frames[i] or i==len(gs)-1:return gs[i][-1 if mode!="first" else 0]["value"]
    a=gs[i][0 if mode=="first" else -1]
    b=gs[i+1][-1 if mode=="last" else 0]
    d=b["frame"]-a["frame"];x=(t-a["frame"])/d
    return (2*x**3-3*x*x+1)*a["value"]+(x**3-2*x*x+x)*d*a["tangent"]+(-2*x**3+3*x*x)*b["value"]+(x**3-x*x)*d*b["tangent"]
def audit(src,out):
    out.mkdir(parents=True,exist_ok=True);c=collections.Counter();examples=[]
    with src.open(encoding="utf-8") as f,(out/"tracks.jsonl").open("w",encoding="utf-8") as w:
        for line in f:
            a=json.loads(line);c["tracks"]+=1;ks=a["keys"]
            if a["data_type"]!=2 or not ks:c["unsupported"]+=1;continue
            gs=groups(ks);duplicates=[g for g in gs if len(g)>1]
            if duplicates:c["duplicate_tracks"]+=1
            valuejump=any(len({k["value"] for k in g})>1 for g in duplicates)
            tangents=any(len({k["tangent"] for k in g})>1 for g in duplicates)
            if valuejump:c["value_jump_tracks"]+=1
            if tangents:c["tangent_change_tracks"]+=1
            c["duplicate_groups"]+=len(duplicates)
            diff=0;maxdelta=0
            for l,r in zip(gs,gs[1:]):
                for fraction in (.25,.5,.75):
                    t=l[0]["frame"]+(r[0]["frame"]-l[0]["frame"])*fraction
                    vs=[evaluate(gs,t,m) for m in ("first","last","split")]
                    delta=max(vs)-min(vs)
                    if delta>1e-6:diff+=1;maxdelta=max(maxdelta,delta)
            if diff:c["interpolation_disagreement_tracks"]+=1
            row=dict(path=a["path"],member=a["member"],target=a["target"],offset=a["offset"],property=a["property"],duplicate_groups=len(duplicates),value_jump=valuejump,tangent_change=tangents,differing_sample_count=diff,max_sample_delta=maxdelta,native_verified=False)
            w.write(json.dumps(row)+"\n")
            if diff and len(examples)<5:examples.append(row)
    s=dict(counts=dict(c),examples=examples,native_verified=False,models=["first","last","split outgoing-last/incoming-first; exact frame last"])
    (out/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8");print(json.dumps(s,indent=2))
def self_test():
    k=lambda f,v,t:dict(frame=f,value=v,tangent=t)
    gs=groups([k(0,0,1),k(1,1,1),k(1,1,0),k(2,1,0)])
    assert abs(evaluate(gs,.5,"split")-.5)<1e-9
    assert evaluate(gs,1.5,"split")==1 and evaluate(gs,1.5,"first")>1
    assert evaluate(gs,.5,"last")!=evaluate(gs,.5,"split")
    print("duplicate-frame three-model fixtures passed")
def main():
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--src",type=Path,default=Path(".za-work/ui-dynamic/flts.jsonl"));p.add_argument("--out",type=Path,default=Path(".za-work/flts-eval"));a=p.parse_args()
    if a.self_test:self_test();return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("local output only")
    audit(a.src,a.out)
if __name__=="__main__":main()
