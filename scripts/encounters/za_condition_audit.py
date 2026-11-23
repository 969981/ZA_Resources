#!/usr/bin/env python3
"""Extract Z-A original ActivationConditionParam fields without guessing semantics.

Reads only original FlatBuffers; preserves each raw Condition/Op/Param
alongside its exact Spawner or EncountData ID. Static evidence only.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

from za_resource_inspect import FB
from za_encounter_crosswalk import FILES, rows, vec_strings


def flatten(f, table, field, record_type, record_id, db, row_index, target_id=""):
    result = []
    # ActivationCondition[] -> Element[] -> ActivationConditionParam[]
    for ci, cond in enumerate(f.tables(table, field)):
        for ei, element in enumerate(f.tables(cond, 0)):
            for pi, param in enumerate(f.tables(element, 0)):
                result.append(dict(
                    record_type=record_type, source_id=record_id,
                    db=db, row=row_index, target_id=target_id,
                    activation_index=ci, element_index=ei, param_index=pi,
                    condition=f.string(param, 0), operator=f.number(param, 1),
                    parameters=json.dumps(vec_strings(f, param, 2), ensure_ascii=False,
                                          separators=(",", ":"))))
    return result


def inspect(root):
    sp_path=root/FILES["sp"]
    enc_path=root/FILES["enc"]
    f=FB(sp_path.read_bytes())
    output=[]
    groups=Counter()
    for db,row,s in rows(f):
        spid=f.string(s,0)
        for idx,tag in ((2,"spawner"),(3,"spawner_ui")):
            seg=flatten(f,s,idx,tag,spid,db,row)
            output.extend(seg);groups[tag]+=len(seg)
        for target in f.tables(s,5):
            encid=f.string(target,0)
            for idx,tag in ((9,"target"),(10,"target_ui")):
                seg=flatten(f,target,idx,tag,spid,db,row,encid)
                output.extend(seg);groups[tag]+=len(seg)
    e=FB(enc_path.read_bytes())
    for db,row,item in rows(e):
        seg=flatten(e,item,13,"encounter",e.string(item,0),db,row)
        output.extend(seg);groups["encounter"]+=len(seg)
    types=Counter(z["condition"] for z in output)
    modes=Counter((z["record_type"],z["condition"]) for z in output)
    exact_keys=defaultdict(set)
    for z in output:
        exact_keys[(z["record_type"],z["condition"])].add(z["source_id"])
    summary={
        "version":"v2.0.2",
        "status":"RAW_ACTIVATION_PARAMETER_NOT_EXECUTION_PROOF",
        "extracted_parameter_rows":len(output),
        "by_record_type":dict(groups),
        "by_condition_name":dict(types.most_common()),
        "condition_sources":[
            dict(record_type=k[0], condition=k[1], parameter_rows=n,
                 distinct_source_ids=len(exact_keys[k]))
            for k,n in modes.most_common()],
        "source_sha256":{
            "spawner":hashlib.sha256(sp_path.read_bytes()).hexdigest(),
            "encounter":hashlib.sha256(enc_path.read_bytes()).hexdigest()},
        "limitations":[
            "Condition/Op/Param are source values, not evaluated runtime predicates",
            "an activation entry can be unconditional or combined with other conditions",
            "condition time and weather integers still require enum/runtime verification",
            "no actual encounters, shiny legality, or spawn odds are inferred from counts"]
    }
    return output, summary


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--virtual-root",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    rows_out,summary=inspect(args.virtual_root)
    args.output.mkdir(parents=True,exist_ok=True)
    if rows_out:
        with (args.output/"za_activation_conditions.csv").open("w",newline="",encoding="utf8") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows_out[0]))
            writer.writeheader();writer.writerows(rows_out)
    (args.output/"za_condition_summary.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"extracted_parameter_rows":len(rows_out),
                      "condition_types":len(summary["by_condition_name"]),
                      "by_record_type":summary["by_record_type"]},
                     indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
