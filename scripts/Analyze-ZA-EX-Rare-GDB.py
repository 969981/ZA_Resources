#!/usr/bin/env python3
"""Summarize read-only Z-A EX1/EX2 GDB JSONL evidence without overstating identity.

Input files must come from real GDB sessions; tests use SYNTHETIC fixtures only.
A user-supplied EX1/EX2 label is not proof of an actual event encounter.
"""
from __future__ import annotations
import argparse, collections, json
from pathlib import Path

RAW_NEVER=0x1FFFFFFF
MODE_NEVER=0x1FFFFFFFF
EXPECTED={"EX1":719,"EX2":150}
OUTPUT=Path("docs/research/v2.0.2/za-ex1-ex2-gdb-runtime-summary.json")

def val(obj,key):
    v=obj.get(key)
    if v is None:return None
    if isinstance(v,int):return v
    if isinstance(v,str):
        try:return int(v,0)
        except ValueError:return None
    return None

def unique_counts(values):
    out=collections.Counter(f"0x{x:X}" for x in values if x is not None)
    return dict(sorted(out.items()))

def summarize(path,label):
    lines=path.read_text(encoding="utf-8").splitlines()
    records=[]
    for i,s in enumerate(lines,1):
        if not s.strip():continue
        try:item=json.loads(s)
        except json.JSONDecodeError as e:raise ValueError(f"{path}:{i}: invalid JSON: {e}") from e
        if item.get("label")!=label:raise ValueError(f"{path}:{i}: expected label {label}")
        records.append(item)
    if not records:raise ValueError(f"{path}: no GDB events")
    kinds=collections.Counter(x["event"] for x in records)
    raw=[val(x.get("values",{}),"descriptor_plus68_u32") for x in records if x["event"]=="rare_raw_load"]
    mode=[val(x.get("values",{}),"state_plus20_u64") for x in records if x["event"]=="native_mode_dispatch"]
    pokemon=[
        {"species":val(x.get("values",{}),"w1_species_candidate"),
         "ptr":x.get("values",{}).get("pokemon_object_pointer")}
        for x in records if x["event"]=="field_init_species_setter_call"]
    pid_pointers={x.get("regs",{}).get("x0") for x in records
                  if x["event"]=="field_init_pid_setter_call"}
    expected=EXPECTED[label]
    matched=[x for x in pokemon if x["species"]==expected]
    same_obj=[x for x in matched if x["ptr"] in pid_pointers]
    observed_raw_never=RAW_NEVER in raw
    observed_mode_never=MODE_NEVER in mode
    return {
        "label":label, "input":str(path), "records":len(records),
        "complete_trace_envelope":kinds["trace_started"]==1 and kinds["trace_stopped"]>=1,
        "event_counts":dict(sorted(kinds.items())),
        "raw_descriptor_plus68_values":unique_counts(raw),
        "native_dispatch_mode_values":unique_counts(mode),
        "native_never_call_hits":kinds["native_never_antishiny_call"],
        "native_always_call_hits":kinds["native_always_adjust_call"],
        "native_random_xor_test_hits":kinds["native_random_xor_check"],
        "native_anti_shiny_helper_hits":kinds["native_anti_shiny_entry"],
        "species_setter_values":unique_counts([x["species"] for x in pokemon]),
        "expected_species":expected,
        "expected_species_seen_at_field_setter":bool(matched),
        "pid_and_expected_species_on_same_object_seen":bool(same_obj),
        "original_raw_never_observed":observed_raw_never,
        "native_never_mode_observed":observed_mode_never,
        "raw_and_native_never_co_observed":observed_raw_never and observed_mode_never,
        "gdb_executed_events_present":len(records)>1 and kinds["trace_started"]>=1,
        "warnings":[
            "EX1/EX2 labels and manual markers are user supplied; not cryptographic proof of encounter identity",
            "Co-occurring raw +0x68 and mode values do not alone prove FlatBuffers EncountData.Rare was copied to that object",
            "Same-object PID/species writes strengthen correlation but cannot prove the upstream battle dispatcher",
            "elf_static_va values require verified runtime load bias; exact AArch64 probe match is checked by GDB source",
        ],
    }

def run(ex1,ex2):
    return {"version":"ZA 2.0.2","evidence_type":"USER_GDB_JSONL_SUMMARY",
            "runtime_sessions":[summarize(ex1,"EX1"),summarize(ex2,"EX2")],
            "confirmed_original_FlatBuffers_to_descriptor_assignment":False,
            "note":"Synthetic tests prove parsing only; never mark actual EX event as executed without user-provided real session logs and encounter correlation."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ex1",type=Path,required=True)
    p.add_argument("--ex2",type=Path,required=True)
    p.add_argument("--output",type=Path,default=OUTPUT)
    args=p.parse_args()
    result=run(args.ex1,args.ex2)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"out":str(args.output),"sessions":[{k:v for k,v in x.items() if k in
          ("label","records","expected_species_seen_at_field_setter","original_raw_never_observed","native_never_mode_observed","native_never_call_hits","pid_and_expected_species_on_same_object_seen")}
          for x in result["runtime_sessions"]]},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
