#!/usr/bin/env python3
"""Analyze extracted ZA 2.0.2 native Lua 5.4 files without modifying originals.

Native opcode/constant evidence is separate from recovered original names.
Uses the pinned bytecode parser originally developed for SV native Lua, but
never applies SV SHA256 pins or assumes the two games share script content.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIRTUAL = ROOT / "Unpack/v2.0.2/romfs/arc/data.trpfs/virtual"
INDEX = ROOT / "Unpack/v2.0.2/romfs/arc/data.trpfs/_index"
UNKNOWN = ROOT / "tools/PokeDocs-Supplement/ZA/Hashlists/Lua/unresolved-symbol-index.tsv"
CORE_PATH = Path(__file__).parent / "_vendor/Analyze-SV-Lua54.py"
NAMES = ("dll_util", "event_ik", "main", "main_dynamic")
HASH_TOKEN = re.compile(rb"^[CSFE][0-9a-fA-F]{16}$")

def core_module():
    spec = importlib.util.spec_from_file_location("za_lua54_core", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Pinned Lua54 parser unavailable")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def read_unresolved(path: Path):
    tokens = set()
    with path.open(encoding="utf-8", newline="") as src:
        rows = list(csv.DictReader(src, delimiter="\t"))
    if len(rows) != 162:
        raise ValueError(f"Expected exactly 162 unresolved ZA hashes, got {len(rows)}")
    counts = Counter()
    for row in rows:
        k = row["kind"].lower()
        h = row["hash"].upper().replace("0X", "")
        if k not in ("s", "f", "e") or not re.fullmatch(r"[0-9A-F]{16}",h):
            raise ValueError("Malformed unresolved ZA hash")
        tokens.add((k.upper()+h).encode("ascii"))
        counts[k] += 1
    if counts != Counter({"s":116, "f":43, "e":3}) or len(tokens) != 162:
        raise ValueError("Pinned unresolved mapping was modified")
    return tokens

def indexed_operand(inst, pc, instructions):
    op,a,b,c,k,bx,ax = inst
    if op == "LOADK":
        return bx
    if op == "LOADKX" and pc+1 < len(instructions) and instructions[pc+1][0] == "EXTRAARG":
        return instructions[pc+1][6]
    if op in ("GETFIELD", "GETTABUP"):
        return c
    if op in ("SETFIELD", "SETTABUP", "EQK"):
        return b
    if op == "SELF" and k == 1:
        return c
    return None

def analyze(raw, source, wanted, core):
    lua = core.Lua54(raw)
    lua.parse()
    candidates = []
    refs = []
    for proto in lua.protos:
        consts = {i: token.upper() for i, token in enumerate(proto["constants"])
                  if token and HASH_TOKEN.fullmatch(token) and token.upper() in wanted}
        for i,token in consts.items():
            candidates.append([source,proto["id"],i,token.decode(),
                               "NATIVE_LUA54_CONSTANT_PRESENT_ONLY"])
        code = core.instructions(raw,proto)
        for pc,ins in enumerate(code):
            idx = indexed_operand(ins,pc,code)
            if idx not in consts:
                continue
            refs.append([source,consts[idx].decode(),proto["id"],proto["parent"],pc,
                         f"0x{proto['code_offset']+pc*4:X}",ins[0],idx,
                         "NATIVE_LUA54_OPCODE_CONSTANT_REFERENCE"])
    methods, rejected = core.direct_methods(lua,source)
    root = lua.protos[0]
    K=root["constants"]
    ins=core.instructions(raw,root)
    static=[]
    for pc in range(len(ins)-4):
        seq=ins[pc:pc+5]
        if tuple(x[0] for x in seq)!=("LOADK","GETTABLE","LOADK","CLOSURE","SETTABLE"):
            continue
        a=seq[1][1]
        if (seq[0][1]!=a+1 or seq[1][3]!=a+1 or seq[2][1]!=a+1 or
            seq[3][1]!=a+2 or seq[4][1:4]!=(a,a+1,a+2)):
            continue
        cidx,sidx=seq[0][5],seq[2][5]
        cls=K[cidx] if cidx<len(K) else None
        field=K[sidx] if sidx<len(K) else None
        child=seq[3][5]
        if not(cls and re.fullmatch(rb"C[0-9A-Fa-f]{16}",cls) and
               field and re.fullmatch(rb"S[0-9A-Fa-f]{16}",field) and child<len(root["children"])):
            continue
        static.append([source,cls.decode(),field.decode(),pc,pc+4,
                       root["children"][child],
                       "NATIVE_ROOT_CLASS_S_CLOSURE_ASSIGNMENT"])
    return lua,refs,candidates,methods,static,dict(rejected)

def write_tsv(path,columns,rows):
    with path.open("w",encoding="utf-8",newline="") as out:
        w=csv.writer(out,delimiter="\t",lineterminator="\n")
        w.writerow(columns)
        w.writerows(rows)

def run(index_path,virtual_root,unknown_path,out_dir,require_all=False):
    index=json.loads(index_path.read_text(encoding="utf-8"))
    if (index.get("version")!="v2.0.2" or
        index.get("target_pack_indices")!=[12145,12146,12147,12148] or
        index.get("all_unique") is not True):
        raise ValueError("Unexpected ZA Lua native pack-index manifest")
    core=core_module()
    wanted=read_unresolved(unknown_path)
    reports, refs, constants, methods, statics = {},[],[],[],[]
    for name in NAMES:
        target=index["targets"][name]["matches"][0]
        rel=target["virtual_path"].replace("\\","/")
        if (rel.startswith("/") or ":" in rel or ".." in rel.split("/") or
            not rel.lower().endswith("/"+name+".blua")):
            raise ValueError("Invalid native Lua virtual path: "+rel)
        source_file=virtual_root / rel
        if not source_file.is_file():
            reports[name]={"status":"MISSING_NATIVE_FILE","virtual_path":rel}
            continue
        raw=source_file.read_bytes()
        report={"virtual_path":rel,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
                "header_hex":raw[:32].hex(),"source_pack_index":target["pack_index"]}
        try:
            parsed,r,c,m,s,rejected=analyze(raw,name,wanted,core)
            report.update({"status":"PARSED_NATIVE_LUA54","prototypes":len(parsed.protos),
                           "unknown_opcode_refs":len(r),"unknown_constants":len(c),
                           "native_class_f_closures":len(m),"native_class_s_closures":len(s),
                           "method_pattern_rejections":rejected})
            refs.extend(r);constants.extend(c)
            methods.extend([[v["source"],v["class_hash"],v["function_hash"],v["root_pc"],
                            v["assignment_pc"],v["child_proto_id"],v["evidence"]] for v in m])
            statics.extend(s)
        except (core.FormatError, ValueError) as exc:
            report.update({"status":"UNSUPPORTED_NATIVE_LUA_FORMAT","reason":str(exc)})
        reports[name]=report
    out_dir.mkdir(parents=True,exist_ok=True)
    write_tsv(out_dir/"native-unknown-opcode-references.tsv",
              ["source","hash_token","proto_id","parent_proto_id","pc","file_offset_hex",
               "opcode","constant_index","evidence"],refs)
    write_tsv(out_dir/"native-unknown-constants.tsv",
              ["source","proto_id","constant_index","hash_token","evidence"],constants)
    write_tsv(out_dir/"native-c-f-method-edges.tsv",
              ["source","class_hash","function_hash","root_pc","assignment_pc",
               "child_proto_id","evidence"],methods)
    write_tsv(out_dir/"native-c-s-static-edges.tsv",
              ["source","class_hash","s_hash","root_pc","settable_pc",
               "closure_proto_id","evidence"],statics)
    summary={"game":"Pokemon Legends Z-A","version":"v2.0.2","files":reports,
             "native_files_parsed":sum(v["status"]=="PARSED_NATIVE_LUA54" for v in reports.values()),
             "native_files_missing":sum(v["status"]=="MISSING_NATIVE_FILE" for v in reports.values()),
             "native_files_unsupported":sum(v["status"]=="UNSUPPORTED_NATIVE_LUA_FORMAT" for v in reports.values()),
             "native_unknown_opcode_references":len(refs),
             "native_unknown_constant_occurrences":len(constants),
             "unique_unknown_tokens_with_opcode_references":len({r[1] for r in refs}),
             "native_class_f_closure_edges":len(methods),
             "native_class_s_closure_edges":len(statics),
             "original_names_recovered":0,
             "native_original_name_confirmations":0,
             "warning":"Game-native opcode references and class assignments are not recovered original symbol names. No Haxe-inferred name is written."}
    (out_dir/"native-lua-summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if require_all and summary["native_files_parsed"]!=4:
        raise RuntimeError("Native ZA Lua target extraction/format verification incomplete")
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack-report",type=Path,default=ROOT/"Unpack/v2.0.2/romfs/arc/data.trpfs/_index/lua_pack_locations.json")
    p.add_argument("--virtual-root",type=Path,default=VIRTUAL)
    p.add_argument("--unknown-index",type=Path,default=UNKNOWN)
    p.add_argument("--out",type=Path,default=INDEX/"lua-native")
    p.add_argument("--require-all",action="store_true")
    a=p.parse_args()
    print(json.dumps(run(a.pack_report,a.virtual_root,a.unknown_index,a.out,a.require_all),
                     indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
