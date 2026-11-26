#!/usr/bin/env python3
"""Locate candidate native icon consumers in SHA-pinned ZA ELF; not a confirmed selector."""
import argparse, hashlib, importlib.util, json, re, struct, csv
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--out",type=Path,default=Path(".za-work/pokemon-selector")); a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    raw=Path("Unpack/v2.0.2/exefs/main/main.elf").read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if len(raw)!=66579944 or sha!="470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d": raise ValueError("unexpected ELF")
    spec=importlib.util.spec_from_file_location("elf_helper",Path(__file__).with_name("Probe-ZA-Lua-Host-ELF.py")); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.TERMS=re.compile(rb"(?i)(?:trpokecfg|trpmcatalog|poke_resource_table|ik_pokemon[/\\]|icon_pokemon|pokemonicon|pokeicon|pokemon_icon|poke_icon|pm%[0-9a-z]*[diu]|/icon/pm|/icon/.*bntx|PokemonResource|PokeResource)")
    elf=m.ELF64(raw); hits,total,truncated=m.scan_strings(elf,"main",limit=10000); refs=m.scan_adr_xrefs(elf,"main",hits,limit=10000)
    m.dump(a.out/"elf-icon-strings.tsv",m.HIT_COLS,hits); m.dump(a.out/"elf-icon-xrefs.tsv",m.XREF_COLS,refs)
    # Exact addresses are candidates, not function boundaries. Record instructions in windows.
    from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
    dis=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
    windows=[]
    for pc in sorted({int(r[3],16) for r in refs}):
        for region in elf.text_regions():
            start=region["addr"]; end=start+region["size"]
            if start<=pc<end:
                lo=max(start,pc-64); hi=min(end,pc+128); off=region["off"]+lo-start
                ins=[dict(va=hex(i.address),bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in dis.disasm(raw[off:off+hi-lo],lo)]
                windows.append(dict(xref_va=hex(pc),region=region["name"],instructions=ins,evidence="LOCAL_XREF_WINDOW_NOT_FUNCTION"))
                break
    (a.out/"elf-icon-windows.jsonl").write_text("".join(json.dumps(r)+"\n" for r in windows))
    syms=elf.symbols(); (a.out/"elf-icon-symbols.json").write_text(json.dumps(syms,indent=2))
    summary=dict(elf_sha256=sha,string_hits=total,reported_strings=len(hits),strings_truncated=truncated,adr_xref_candidates=len(refs),xref_limit_reached=len(refs)>=10000,windows=len(windows),matching_symbols=len(syms),selector_confirmed=False,note="Exact target string addresses or short ADRP/ADD candidates; register clobber, callers, function boundaries and runtime semantics require further verification.")
    (a.out/"elf-summary.json").write_text(json.dumps(summary,indent=2)+"\n"); print(json.dumps(summary,indent=2))
if __name__=="__main__": main()
