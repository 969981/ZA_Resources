#!/usr/bin/env python3
"""Bounded reference-backed Maxwell mnemonic subset, not a complete disassembler.
ISA reference: envytools/envydis/gm107.c at f102b82381f3f11cee113d16374c87091db039d9
https://github.com/envytools/envytools/blob/f102b82381f3f11cee113d16374c87091db039d9/envydis/gm107.c
The original file is MIT-licensed, Copyright 2014 Red Hat Inc.
Only a small set of numeric opcode masks and names is used here.
"""
import collections, hashlib, importlib.util, json, sqlite3, struct
from pathlib import Path
def load(name):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
core=load("ZANativeShaderCore")
# (masked opcode, mask, mnemonic, operand-family)
RULES=[
    (0xe300,0xfff0,"EXIT","control"),
    (0xe240,0xfff0,"BRA","control"),
    (0x50b0,0xfff8,"NOP","control"),
    (0x5080,0xfff8,"MUFU","sfu"),
    (0x4c98,0xfff8,"MOV","constant"),
    (0x4c68,0xfff8,"FMUL","constant"),
    (0x4c58,0xfff8,"FADD","constant"),
    (0x4980,0xff80,"FFMA","constant"),
    (0x5c98,0xfff8,"MOV","register"),
    (0x5c68,0xfff8,"FMUL","register"),
    (0x5c58,0xfff8,"FADD","register"),
    (0x5980,0xff80,"FFMA","register"),
    (0xdeb8,0xfff8,"TEX","bindless_candidate"),
    (0xc038,0xfc38,"TEX","texture"),
    (0xdc38,0xff38,"TLD","texture"),
    (0xdd38,0xff38,"TLD","bindless_candidate"),
]
SFU={0:"COS",1:"SIN",2:"EX2",3:"LG2",4:"RCP",5:"RSQ",6:"RCP64H",7:"RSQ64H",8:"SQRT"}
def decode(w):
    hits=[(name,family) for op,mask,name,family in RULES if (w>>48)&mask==op]
    if len(hits)!=1:return {"mnemonic":"UNKNOWN","family":"unknown"}
    name,family=hits[0]
    row=dict(mnemonic=name,family=family,predicate_raw=(w>>16)&15)
    if family=="sfu":
        row.update(subop_raw=(w>>20)&15,subop=SFU.get((w>>20)&15,"UNKNOWN"),dst_raw=w&255,src_raw=(w>>8)&255)
    if family in ("constant","register"):row.update(dst_raw=w&255,src8_raw=(w>>8)&255,operand20_raw=(w>>20)&255)
    if family=="texture":row["texture_field_raw"]=(w>>36)&8191
    return row
def analyze(y):
    if len(y)<160 or y[:8]!=bytes.fromhex("7856341200000000") or (len(y)-128)%32:return None
    rows=[];counts=collections.Counter()
    for off in range(128,len(y),32):
        q=struct.unpack_from("<4Q",y,off)
        if not any(q):continue
        for i,w in enumerate(q[1:],1):
            if not w:continue
            row=decode(w);counts[row["mnemonic"]+("."+row["subop"] if "subop" in row else "")]+=1
            rows.append(dict(offset=off+i*8,**row))
    return dict(instructions=len(rows),recognized=sum(v for k,v in counts.items() if k!="UNKNOWN"),counts=dict(counts),sfu=[r for r in rows if r["family"]=="sfu"],texture=[r for r in rows if r["family"] in ("texture","bindless_candidate")],code_sha256=hashlib.sha256(y[128:]).hexdigest(),complete_decoder=False)
def main():
    assert decode(0x5080000000100000)["subop"]=="SIN"
    assert decode(0x5080000000000000)["subop"]=="COS"
    assert decode(0xe30000000007000f)["mnemonic"]=="EXIT"
    assert decode(0x4c98079400770003)["mnemonic"]=="MOV"
    assert decode(0)["mnemonic"]=="UNKNOWN"
    out=Path(".za-work/ZANativeShaderCore");db=sqlite3.connect(out/"shader-core.sqlite");db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""CREATE TABLE opcode_segment(sha256 TEXT PRIMARY KEY,metadata_json TEXT);
    CREATE TABLE opcode_stage(binary_path TEXT,ordinal INTEGER,stage TEXT,segment_sha256 TEXT REFERENCES opcode_segment(sha256),PRIMARY KEY(binary_path,ordinal,stage),FOREIGN KEY(binary_path,ordinal,stage) REFERENCES stage(path,ordinal,stage));""")
    paths=core.audit.tree();seen={};links=[];skipped=0
    for bp, in db.execute("SELECT DISTINCT binary_path FROM maxwell_evidence").fetchall():
        raw=core.get(bp,paths)
        for ordinal,stage,meta in db.execute("SELECT ordinal,stage,metadata_json FROM stage WHERE path=?",(bp,)).fetchall():
            st=json.loads(meta);key=st.get("segment_b_sha256")
            if not key:skipped+=1;continue
            if key not in seen:
                start=st["segment_b_offset"];y=raw[start:start+st["segment_b_size"]]
                if hashlib.sha256(y).hexdigest()!=key:raise ValueError("segment hash mismatch")
                result=analyze(y)
                if result is None:skipped+=1;continue
                seen[key]=result;db.execute("INSERT INTO opcode_segment VALUES(?,?)",(key,json.dumps(result)))
            links.append(dict(binary_path=bp,ordinal=ordinal,stage=stage,segment_sha256=key))
            db.execute("INSERT INTO opcode_stage VALUES(?,?,?,?)",(bp,ordinal,stage,key))
    db.commit();integrity=db.execute("PRAGMA integrity_check").fetchone()[0];fk=db.execute("PRAGMA foreign_key_check").fetchall();db.close()
    core.audit.write(out,"maxwell-opcodes",[dict(segment_sha256=k,**v) for k,v in seen.items()]);core.audit.write(out,"maxwell-opcode-links",links)
    counts=collections.Counter()
    for v in seen.values():counts.update(v["counts"])
    summary=dict(unique_segments=len(seen),stage_links=len(links),skipped=skipped,instructions=sum(v["instructions"] for v in seen.values()),recognized=sum(v["recognized"] for v in seen.values()),mnemonics=dict(counts),integrity=integrity,foreign_key_errors=len(fk),complete_decoder=False,runtime_variant_mapping_verified=False)
    (out/"opcode-summary.json").write_text(json.dumps(summary,indent=2)+"\n");print("OPCODE_SUMMARY",json.dumps(summary))
    # Compare actual candidate vertex stage subsets for one- and two-UV fire.
    for link in links:
        if link["binary_path"].endswith("/unlit.bnsh") and link["stage"]=="vertex" and 64<=link["ordinal"]<=95:
            v=seen[link["segment_sha256"]]
            print("UNLIT_VERTEX_SAMPLE",json.dumps(dict(**link,counts=v["counts"],sin_offsets=[x["offset"] for x in v["sfu"] if x["subop"]=="SIN"],texture_fields=sorted({x["texture_field_raw"] for x in v["texture"] if "texture_field_raw" in x}))))
    if integrity!="ok" or fk or not seen:raise SystemExit("opcode core integrity/coverage failure")
if __name__=="__main__":main()
