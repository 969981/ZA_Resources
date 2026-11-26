#!/usr/bin/env python3
"""Inspect full resolver output without confusing UI keywords with native IDs."""
import argparse, collections, json, re
from pathlib import Path
def rows(p):
    with p.open(encoding="utf-8") as f:
        for l in f:
            if l.strip():yield json.loads(l)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--resolver",type=Path,default=Path(".za-work/ui-resolver"));p.add_argument("--layout",type=Path,default=Path(".za-work/ui-layout"));p.add_argument("--out",type=Path,default=Path(".za-work/ui-names"));a=p.parse_args()
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("local output only")
    a.out.mkdir(parents=True,exist_ok=True);families=collections.defaultdict(collections.Counter);strict=collections.defaultdict(set);missing=collections.Counter();errors=collections.Counter()
    for t in rows(a.resolver/"semantic-candidates.jsonl"):
        n=t["name"]
        for d in t["domains"]:families[d][n]+=1
        for d,pat in {"award_strict":r"badge|medal|achievement|trophy|kunsho|kunsyo|shogo|shougou","ribbon_strict":r"ribbon|akashi","move_category_strict":r"waza_category|move_category|skill_category|buturi|butsuri|tokushu|henka|physical|special","ball_strict":r"icon_ball|ball_icon|monsterball|monster_ball|pokeball"}.items():
            if re.search(pat,n,re.I):strict[d].add(n)
    for l in rows(a.resolver/"layout-refs.jsonl"):
        if l["status"]=="MISSING":missing[l["name"]]+=1
    for l in rows(a.layout/"errors.jsonl"):errors[l["error"]]+=1
    report=dict(families={k:dict(v.most_common()) for k,v in sorted(families.items())},strict={k:sorted(v) for k,v in strict.items()},missing_names=dict(missing.most_common()),layout_errors=dict(errors),native_id_mapping_complete=False)
    (a.out/"names.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(dict(strict=report["strict"],balls=report["families"].get("balls"),ribbons=report["families"].get("ribbons"),moves=report["families"].get("moves"),missing_distinct_names=len(missing),missing_top=missing.most_common(25),layout_errors=report["layout_errors"]),indent=2,ensure_ascii=False))
if __name__=="__main__":main()
