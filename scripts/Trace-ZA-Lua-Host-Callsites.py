#!/usr/bin/env python3
"""Bounded read-only Z-A host ELF xref context and pointer/RELA triage.

Build on the SHA256-pinned probe, with byte-accurate AArch64 PC-relative
references to Lua-related strings. Nearby BL/BLR instructions are only
*investigation candidates*, NEVER proof a Lua loader calls the target.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
import struct
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXEFS=ROOT/"Unpack/v2.0.2/exefs"
NATIVE=ROOT/"Unpack/v2.0.2/romfs/arc/data.trpfs/_index/lua-native"
PROBER=ROOT/"scripts/Probe-ZA-Lua-Host-ELF.py"
TARGETS={
    "_ENV", "LUA_NOENV", "LUA_PATH", "LUA_CPATH", "lua_helper",
    "script/lua/bin/release/", ".blua",
    "arc/data.trpfs", "data:/arc/data.trpfd",
    "TrinityHeapType::Lua"
}
SITE_COLUMNS=("target_string","string_virtual_addr_hex","string_file_offset_hex",
              "string_region","native_adr_xref_pcs","adr_xref_count",
              "literal_pointer_data_sites","relative_relocation_data_sites",
              "native_callsite_binding_confirmed")
CONTEXT_COLUMNS=("target_string","xref_pc_hex","xref_file_offset_hex","pc_hex",
                 "file_offset_hex","relative_instruction_offset","word_hex",
                 "decoded_hint","evidence")
PTR_COLUMNS=("target_string","pointer_location_virtual_addr_hex","pointer_location_file_offset_hex",
             "target_virtual_addr_hex","pointer_kind","section","evidence")


def load_probe():
    spec=importlib.util.spec_from_file_location("za_host_elf_probe",PROBER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Native checksum-pinned ExeFS prober missing")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tsv(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))


def write_tsv(path,cols,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(cols)
        w.writerows(rows)


def instruction_hint(word,pc,probe):
    # Pseudocode labels only; full disassembly must be done separately in Ghidra/IDA.
    if (word&0xFC000000)==0x94000000:
        imm=probe.signed(word&0x3FFFFFF,26)*4
        return f"BL_IMMEDIATE 0x{pc+imm:X}"
    if (word&0xFC000000)==0x14000000:
        imm=probe.signed(word&0x3FFFFFF,26)*4
        return f"B_IMMEDIATE 0x{pc+imm:X}"
    if (word&0xFFFFFC1F)==0xD63F0000:
        return f"BLR_REGISTER X{(word>>5)&31}"
    if (word&0xFFFFFC1F)==0xD65F0000:
        return f"RET X{(word>>5)&31}"
    adrp=probe.decode_adrp(word,pc)
    if adrp:return f"ADRP X{adrp[0]},PAGE(0x{adrp[1]:X})"
    adr=probe.decode_adr(word,pc)
    if adr:return f"ADR X{adr[0]},0x{adr[1]:X}"
    add=probe.decode_add_x_imm(word)
    if add:return f"ADD X{add[0]},X{add[1]},#{add[2]}"
    if (word&0xFFC00000)==0xF9400000:
        return f"LDR X{word&31},[X{(word>>5)&31},#{((word>>10)&0xfff)*8}]"
    if (word&0xFFC00000)==0xF9000000:
        return f"STR X{word&31},[X{(word>>5)&31},#{((word>>10)&0xfff)*8}]"
    return "UNDECODED_NO_SEMANTIC_CLAIM"


def xref_context(elf,xref_pc,target,probe,window=20):
    # All PCs must be mapped through actual executable section, never
    # file offsets guessed from VA.
    for region in elf.text_regions():
        begin=region["addr"]
        end=begin+region["size"]
        if not begin<=xref_pc<end or (xref_pc-begin)%4:
            continue
        off0=region["off"]
        rows=[]
        center=(xref_pc-begin)//4
        for step in range(-window,window+1):
            i=center+step
            if i<0 or (i+1)*4>region["size"]:
                continue
            fileoff=off0+i*4
            word=struct.unpack_from("<I",elf.raw,fileoff)[0]
            pc=begin+i*4
            rows.append((target,f"0x{xref_pc:X}",f"0x{off0+center*4:X}",
                         f"0x{pc:X}",f"0x{fileoff:X}",step,f"0x{word:08X}",
                         instruction_hint(word,pc,probe),
                         "NATIVE_BOUNDED_INSTRUCTION_CONTEXT_NOT_EXECUTION_PROOF"))
        return rows
    raise ValueError(f"AArch64 xref PC not in executable mapping: {xref_pc:x}")


def pointer_and_relocations(elf,targets):
    # Targets are {literal: virtualaddr}; first try actual initialized file
    # pointers. A match to a pointer literal alone is not proof of its reader.
    rows=[]
    target_va={va:string for string,va in targets.items()}
    for region in elf.data_regions():
        data=elf.raw[region["off"]:region["off"]+region["size"]]
        for string,va in targets.items():
            needle=struct.pack("<Q",va)
            begin=0
            while True:
                pos=data.find(needle,begin)
                if pos<0:break
                off=region["off"]+pos
                rows.append((string,f"0x{region['addr']+pos:X}",f"0x{off:X}",
                             f"0x{va:X}","ELF_QWORD_RAW_LITERAL",
                             region["name"],"NATIVE_ELF_POINTER_BYTES_ONLY"))
                begin=pos+1
    rels=Counter()
    for sec in elf.sections:
        if sec["stype"]!=4:continue  # SHT_RELA, Elf64_Rela
        if sec["entsize"]<24 or sec["size"]%sec["entsize"]:
            raise ValueError("Invalid ELF RELA structure")
        symtab=None
        if sec["link"] < len(elf.sections):
            candidate=elf.sections[sec["link"]]
            if candidate["stype"] in (2,11):
                symtab=candidate
        for idx in range(sec["size"]//sec["entsize"]):
            off=sec["off"]+idx*sec["entsize"]
            r_offset,r_info,r_addend=struct.unpack_from("<QQq",elf.raw,off)
            typ=r_info&0xFFFFFFFF
            symidx=r_info>>32
            rels[typ]+=1
            target=None
            if typ==1027 and symidx==0:  # R_AARCH64_RELATIVE
                target=r_addend
            elif typ==257: # R_AARCH64_ABS64, against a symbol's st_value
                if symidx==0:
                    target=r_addend
                elif symtab is not None and symtab["entsize"]>=24 and (
                    (symidx+1)*symtab["entsize"]<=symtab["size"]
                ):
                    symoff=symtab["off"]+symidx*symtab["entsize"]
                    nameoff,info,other,shndx,val,size=struct.unpack_from(
                        "<IBBHQQ",elf.raw,symoff)
                    if shndx!=0:  # undefined dynamic symbol cannot be resolved statically
                        target=val+r_addend
            if target not in target_va:continue
            string=target_va[target]
            loc=""
            reg=""
            for sec2 in elf.sections:
                if (sec2["stype"]!=8 and sec2["addr"]<=r_offset<sec2["addr"]+sec2["size"]
                    and sec2["flags"]&2):
                    loc=f"0x{sec2['off']+r_offset-sec2['addr']:X}"
                    reg=sec2["name"]
                    break
            rows.append((string,f"0x{r_offset:X}",loc,f"0x{target:X}",
                         ("ELF_R_AARCH64_RELATIVE_ADDEND" if typ==1027
                          else "ELF_R_AARCH64_ABS64_SYMBOL_PLUS_ADDEND"),
                         reg or sec["name"],
                         "ELF_STATIC_RELOCATION_NOT_RUNTIME_RESOLUTION"))
    return rows,dict(rels)


def run(root=ROOT,out=NATIVE,window=20):
    if not 1<=window<=64:
        raise ValueError("Window must be 1..64 instructions")
    probe=load_probe()
    exefs=root/"Unpack/v2.0.2/exefs"
    native=root/"Unpack/v2.0.2/romfs/arc/data.trpfs/_index/lua-native"
    manifest=json.loads((exefs/"exefs-manifest.json").read_text("utf-8"))
    item=manifest["modules"]["main"]
    source=exefs/"main/main.elf"
    raw=source.read_bytes()
    if (len(raw)!=item["elfSize"] or hashlib.sha256(raw).hexdigest()!=item["elfSha256"]
        or item["status"]!="VERIFIED_ARTIFACTS"):
        raise ValueError("Native game main ELF SHA and length mismatch")
    elf=probe.ELF64(raw)
    hits=tsv(native/"native-host-elf-string-locators.tsv")
    refs=tsv(native/"native-host-elf-adr-references.tsv")
    candidates={r["snippet"]:r for r in hits
                if r["module"]=="main" and r["snippet"] in TARGETS}
    if not candidates:
        raise ValueError("Expected pinned main ELF Lua host clue string corpus")
    # Validate each source string's exact bytes; convert virtual locations
    # from ELF allocated sections, rather than trusting the old TSV.
    for text,row in candidates.items():
        off=int(row["file_offset_hex"],16)
        va,region=elf.location(off)
        if va != int(row["virtual_addr_hex"],16) or region != row["region"] or (
            elf.raw[off:off+len(text)] != text.encode("ascii")
        ):
            raise ValueError("Historical ELF string locator disagrees with original bytes")
    target_va={text:int(row["virtual_addr_hex"],16) for text,row in candidates.items()}
    pointers,rela_counts=pointer_and_relocations(elf,target_va)
    targeted=[r for r in refs if r["module"]=="main" and r["target_string"] in candidates]
    ctx=[]
    for row in targeted:
        if int(row["target_virtual_addr_hex"],16)!=target_va[row["target_string"]]:
            raise ValueError("Prior ARM64 string xref has incorrect VA")
        ctx.extend(xref_context(elf,int(row["instruction_pc_hex"],16),
                                row["target_string"],probe,window))
    pcount=Counter(x[0] for x in pointers)
    rcount=Counter(r["target_string"] for r in targeted)
    sites=[]
    for text in sorted(candidates):
        old=candidates[text]
        refs_here=sorted({int(r["instruction_pc_hex"],16) for r in targeted
                          if r["target_string"]==text})
        sites.append((text,old["virtual_addr_hex"],old["file_offset_hex"],old["region"],
                      ",".join(f"0x{x:X}" for x in refs_here),len(refs_here),
                      sum(1 for p in pointers if p[0]==text and p[4]=="ELF_QWORD_RAW_LITERAL"),
                      sum(1 for p in pointers if p[0]==text and p[4].startswith("ELF_R_AARCH64_")),
                      "NO"))
    result={
        "game":"Pokemon Legends Z-A","version":"v2.0.2",
        "main_elf_sha256":item["elfSha256"],"input_locator_sha256":hashlib.sha256(
            (native/"native-host-elf-string-locators.tsv").read_bytes()).hexdigest(),
        "input_xref_sha256":hashlib.sha256(
            (native/"native-host-elf-adr-references.tsv").read_bytes()).hexdigest(),
        "target_strings":len(candidates),"target_string_names":sorted(candidates),
        "exact_adr_references_for_targets":len(targeted),
        "bounded_context_instructions":len(ctx),
        "literal_and_relocation_pointer_sites":len(pointers),
        "rela_types_in_elf":{str(k):v for k,v in sorted(rela_counts.items())},
        "per_target":{
            row[0]:{"str_va":row[1],"exact_adr_ref_pcs":row[4],
                    "adr_ref_count":row[5],"raw_qword_pointer_count":row[6],
                    "relative_relocation_pointer_count":row[7]}
            for row in sites
        },
        "lua_chunk_loader_call_graph_confirmed":False,
        "root_chunk_upvalue_runtime_value_confirmed":False,
        "original_names_recovered":0,
        "warning":"Only exact static addresses and bounded instruction words. Nearby BL/BLR, pointer literals, and RELA entries are investigation leads, never runtime loader/VM proof."
    }
    out.mkdir(parents=True,exist_ok=True)
    write_tsv(out/"native-host-elf-highsignal-sites.tsv",SITE_COLUMNS,sites)
    write_tsv(out/"native-host-elf-bounded-context.tsv",CONTEXT_COLUMNS,ctx)
    write_tsv(out/"native-host-elf-pointer-sites.tsv",PTR_COLUMNS,pointers)
    (out/"native-host-elf-callsites-summary.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root",type=Path,default=ROOT)
    ap.add_argument("--out",type=Path,default=NATIVE)
    ap.add_argument("--window",type=int,default=20)
    args=ap.parse_args()
    print(json.dumps(run(args.repo_root,args.out,args.window),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
