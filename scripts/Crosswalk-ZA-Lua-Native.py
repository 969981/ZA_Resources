#!/usr/bin/env python3
"""Join verified native ZA Lua opcode evidence to 258 THIRD-PARTY Haxe references.

The join is by exact 64-bit hash, NOT inferred original identifier names.
Neither a reconstructed Haxe call site nor a native opcode constant reference
alone proves the original semantic function name.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SUP=ROOT/"tools/PokeDocs-Supplement/ZA/Hashlists/Lua"
NATIVE=ROOT/"Unpack/v2.0.2/romfs/arc/data.trpfs/_index/lua-native"
HASH_INDEX=SUP/"unresolved-symbol-index.tsv"
HAXE=SUP/"unresolved-s-references.tsv"
NATIVE_OP=NATIVE/"native-unknown-opcode-references.tsv"
NATIVE_STATIC=NATIVE/"native-c-s-static-edges.tsv"
SUMMARY=NATIVE/"native-lua-summary.json"
DEST=NATIVE

def read_tsv(path):
    with path.open(encoding="utf-8",newline="") as src:
        return list(csv.DictReader(src,delimiter="\t"))

def run(hash_index=HASH_INDEX,haxe_path=HAXE,op_path=NATIVE_OP,
        static_path=NATIVE_STATIC,summary_path=SUMMARY,out=DEST):
    hashes=read_tsv(hash_index)
    if len(hashes)!=162 or Counter(x["kind"] for x in hashes)!=Counter({"s":116,"f":43,"e":3}):
        raise ValueError("Pinned unresolved ZA hash corpus changed")
    source=json.loads(summary_path.read_text(encoding="utf-8"))
    if source.get("version")!="v2.0.2" or int(source.get("native_files_parsed",0))==0:
        raise ValueError("No verified ZA Lua 5.4 native analysis to crosswalk")
    known={x["kind"].upper()+x["hash"][2:].upper():x for x in hashes}
    haxe=defaultdict(list)
    for h in read_tsv(haxe_path):
        token="S"+h["hash"][2:].upper()
        if token not in known or h["kind"]!="s":
            raise ValueError("Untracked Haxe source token "+token)
        if h.get("commit")!="c7bc243ac4d28356dff9f06b6723330ea92247d5":
            raise ValueError("Unpinned Haxe source reference")
        haxe[token].append(h)
    ops=defaultdict(list)
    for x in read_tsv(op_path):
        token=x["hash_token"].upper()
        if token not in known or x["evidence"]!="NATIVE_LUA54_OPCODE_CONSTANT_REFERENCE":
            raise ValueError("Native opcode evidence not recognized: "+token)
        ops[token].append(x)
    statics=defaultdict(list)
    for x in read_tsv(static_path):
        token=x["s_hash"].upper()
        if token in known:
            if x["evidence"]!="NATIVE_ROOT_CLASS_S_CLOSURE_ASSIGNMENT":
                raise ValueError("Invalid native class S edge")
            statics[token].append(x)
    rows=[]
    fields=["kind","hash","original_line","native_opcode_refs","native_distinct_prototypes",
            "native_class_s_closure_edges","haxe_reference_rows","haxe_calls",
            "haxe_reads","haxe_writes","haxe_declarations","native_first_source",
            "native_first_pc","native_first_opcode","haxe_first_path","haxe_first_line",
            "crosswalk_grade","original_name_confirmed"]
    for token,h in sorted(known.items()):
        nr=ops[token];hs=haxe[token];sr=statics[token]
        roles=Counter(x["role"] for x in hs)
        first=nr[0] if nr else None
        hfirst=hs[0] if hs else None
        grade=("NATIVE_OPCODE_AND_HAXE_REFERENCES_NOT_NAME_CONFIRMED" if nr and hs
               else "NATIVE_OPCODE_ONLY" if nr else "HAXE_RECONSTRUCTION_ONLY" if hs
               else "NO_SUPPORTED_OPCODE_OR_HAXE_REFERENCE")
        rows.append({
            "kind":h["kind"],"hash":h["hash"],"original_line":h["original_line"],
            "native_opcode_refs":len(nr),
            "native_distinct_prototypes":len({(x["source"],x["proto_id"]) for x in nr}),
            "native_class_s_closure_edges":len(sr),
            "haxe_reference_rows":len(hs),
            "haxe_calls":roles["CALL"],"haxe_reads":roles["READ"],
            "haxe_writes":roles["WRITE"],"haxe_declarations":roles["DECLARATION"],
            "native_first_source":first["source"] if first else "",
            "native_first_pc":first["pc"] if first else "",
            "native_first_opcode":first["opcode"] if first else "",
            "haxe_first_path":hfirst["path"] if hfirst else "",
            "haxe_first_line":hfirst["line"] if hfirst else "",
            "crosswalk_grade":grade,"original_name_confirmed":"NO",
        })
    out.mkdir(parents=True,exist_ok=True)
    with (out/"native-haxe-crosswalk.tsv").open("w",encoding="utf-8",newline="") as dst:
        w=csv.DictWriter(dst,fieldnames=fields,delimiter="\t",lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    counts=Counter(x["crosswalk_grade"] for x in rows)
    result={
        "scope":"ZA native Lua opcode references joined to third-party Haxe by 64-bit Hash only",
        "version":"v2.0.2",
        "total_unknown":len(rows),
        "unresolved_s":116,"unresolved_f":43,"unresolved_e":3,
        "haxe_reference_rows":sum(len(x) for x in haxe.values()),
        "native_opcode_reference_rows":sum(len(x) for x in ops.values()),
        "unique_s_with_native_opcode_and_haxe":sum(x["kind"]=="s" and
            x["crosswalk_grade"]=="NATIVE_OPCODE_AND_HAXE_REFERENCES_NOT_NAME_CONFIRMED" for x in rows),
        "native_class_s_static_edges":sum(len(x) for x in statics.values()),
        "evidence_grades":dict(counts),
        "original_names_recovered":0,
        "native_symbol_names_confirmed":0,
        "warning":"No original name is inferred; crosswalk is between independent evidence levels."
    }
    (out/"native-haxe-crosswalk-summary.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--unknown-index",type=Path,default=HASH_INDEX)
    p.add_argument("--haxe",type=Path,default=HAXE)
    p.add_argument("--native-opcodes",type=Path,default=NATIVE_OP)
    p.add_argument("--native-statics",type=Path,default=NATIVE_STATIC)
    p.add_argument("--native-summary",type=Path,default=SUMMARY)
    p.add_argument("--out",type=Path,default=DEST)
    a=p.parse_args()
    print(json.dumps(run(a.unknown_index,a.haxe,a.native_opcodes,a.native_statics,
                         a.native_summary,a.out),indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
