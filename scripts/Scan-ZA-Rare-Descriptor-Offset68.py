#!/usr/bin/env python3
"""Find native AArch64 load/store references to 32-bit descriptor field +0x68.

This is a *field-consumer/producer candidate* scan, not FlatBuffers provenance.
No modification to the ELF or the game. Check SHA against v2.0.2 manifest.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ELF=ROOT/"Unpack/v2.0.2/exefs/main/main.elf"
MANIFEST=ROOT/"Unpack/v2.0.2/exefs/exefs-manifest.json"
OUT=ROOT/"docs/research/v2.0.2/za-rare-descriptor-offset68-xrefs.json"
SEEDS={
    "mode_builder":0x656060,
    "mode_builder_call_battle_candidate":0x653F24,
    "mode_builder_call_spawner_candidate":0x5E6DC0,
    "mode_builder_call_other":0x49CCA4,
    "mode_builder_call_other_2":0x9CE758,
    "mode_builder_call_other_3":0x294F57C,
    "pid_generator":0x656F80,
    "field_init":0xE3EB64,
}
OPS={
  0xB9000000:("STR","W",4),
  0xB9400000:("LDR","W",4),
  0xF9000000:("STR","X",8),
  0xF9400000:("LDR","X",8),
}

def decode(word):
    opcode=word & 0xFFC00000
    if opcode not in OPS:return None
    kind,regwidth,scale=OPS[opcode]
    imm=((word>>10)&0xFFF)*scale
    if imm != 0x68:return None
    reg=word&31
    base=(word>>5)&31
    return {"kind":kind,"width":regwidth,"reg":reg,"base":base,
            "mem_disp":imm,"word":f"0x{word:08X}"}

def segments(raw):
    if len(raw)<64 or raw[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H",raw,18)[0]!=183:
        raise ValueError("AArch64 little-endian ELF64 required")
    phoff=struct.unpack_from("<Q",raw,32)[0]
    ents,n=struct.unpack_from("<HH",raw,54)
    if ents<56 or phoff+ents*n>len(raw) or n>100:raise ValueError("Bad ELF PHDR")
    out=[]
    for i in range(n):
        kind,flags,fo,va,_,filesz,_,_=struct.unpack_from("<IIQQQQQQ",raw,phoff+ents*i)
        if kind==1 and flags&1 and filesz:
            if fo+filesz>len(raw):raise ValueError("Segment outside ELF")
            out.append({"file_offset":fo,"va":va,"size":filesz})
    return out

def scan(raw,segs):
    out=[]
    for seg in segs:
        fo,va,sz=seg["file_offset"],seg["va"],seg["size"]
        for pos in range(0,sz-3,4):
            w=struct.unpack_from("<I",raw,fo+pos)[0]
            hit=decode(w)
            if hit is None: continue
            pc=va+pos
            nearest=min(SEEDS.items(),key=lambda kv:abs(pc-kv[1]))
            hit.update({"pc":f"0x{pc:X}","pc_value":pc,
                        "file_offset":f"0x{fo+pos:X}",
                        "nearest_known_site":nearest[0],
                        "distance_to_known_site":abs(pc-nearest[1])})
            out.append(hit)
    return out

def build(raw,expected,limit):
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=expected:raise ValueError("ELF SHA-256 mismatch")
    hits=scan(raw,segments(raw))
    hitcounts={}
    for kind in ("STR","LDR"):
        for width in ("W","X"):
            hitcounts[kind+"_"+width]=sum(h["kind"]==kind and h["width"]==width for h in hits)
    ranked=sorted(hits,key=lambda h:(h["kind"]!="STR",h["width"]!="W",h["distance_to_known_site"],h["pc_value"]))
    for h in hits:h.pop("pc_value")
    return {"input_sha256":sha, "status":"STATIC_FIELD_OFFSET_CANDIDATES_ONLY",
            "field_offset":"0x68","counts":hitcounts,"known_sites":{k:f"0x{v:X}" for k,v in SEEDS.items()},
            "nearest_writer_candidates": [{k:v for k,v in h.items() if k!="pc_value"} for h in ranked[:limit]],
            "all_reference_sites":hits,
            "limitations":[
                "Coincidence of +0x68 in different unrelated structs is common",
                "No def-use pointer provenance or FlatBuffers to descriptor copy verified",
                "Only unsigned-immediate LDR/STR W/X; excludes STUR, STP, memcpy, SIMD, indirect writes",
                "No runtime memory/PC observations; all addresses are static ELF VAs",
            ]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--elf",type=Path,default=ELF)
    p.add_argument("--manifest",type=Path,default=MANIFEST)
    p.add_argument("--output",type=Path,default=OUT)
    p.add_argument("--limit",type=int,default=120)
    a=p.parse_args()
    if a.limit<1: p.error("--limit must be >= 1")
    manifest=json.loads(a.manifest.read_text(encoding="utf-8"))
    expected=manifest["modules"]["main"]["elfSha256"]
    doc=build(a.elf.read_bytes(),expected,a.limit)
    doc["build_id"]=manifest["modules"]["main"]["buildIdHex"]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"sha256":doc["input_sha256"],"counts":doc["counts"],
                      "top_writers":[x for x in doc["nearest_writer_candidates"] if x["kind"]=="STR"][:12]},
                      ensure_ascii=False,indent=2))
if __name__=="__main__":main()
