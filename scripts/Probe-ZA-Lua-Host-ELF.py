#!/usr/bin/env python3
"""Read-only ZA v2.0.2 host-ELF triage for Lua chunk loading / environment binding.

This is a *static locator* for specific strings, symbol names, AArch64
ADR/ADRP+ADD references, and five absent S hashes. It never claims a loader
function, runtime value, symbol name recovery or executable call chain unless
supported by subsequent disassembly/runtime evidence.

Only standard-library Python. ELF inputs are checksum-pinned in exefs-manifest.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXEFS = ROOT / "Unpack/v2.0.2/exefs"
NATIVE = ROOT / "Unpack/v2.0.2/romfs/arc/data.trpfs/_index/lua-native"
MODULES = ("main", "sdk", "rtld")
S_GAPS = ("062729EC443620C2", "1463948047021356", "34AD86B7E5BB1526",
          "81E0610BF8B9337C", "D0F61B3481E43C08")
CLASS_IK = "0C062DE5AED06885"
STRING_PATTERN = re.compile(rb"[\x20-\x7e]{4,}")
TERMS = re.compile(
    rb"(?i)(?:\.blua|script[/\\]lua|event_ik|dll_util|main_dynamic|"
    rb"luaL_|lua_[A-Za-z]|luaopen_|lua54|lua5\.4|trinity|"
    rb"data\.trpf|loadbufferx|loadfilex|(?<![A-Za-z0-9])_ENV(?![A-Za-z0-9])|LuaManager|LuaScript|"
    rb"ScriptManager|IkScriptCommand)"
)
HIT_COLS = ("module", "evidence", "token", "file_offset_hex", "virtual_addr_hex",
            "region", "snippet")
XREF_COLS = ("module", "target_virtual_addr_hex", "target_string",
             "instruction_pc_hex", "instruction_offset_hex", "evidence",
             "target_region", "instruction_region")
HASH_COLS = ("module", "hash_kind", "hash_hex", "needle_kind", "file_offset_hex",
             "virtual_addr_hex", "region", "evidence")


class ELF64:
    def __init__(self, raw: bytes):
        self.raw = raw
        if (len(raw) < 64 or raw[:4] != b"\x7fELF" or raw[4:6] != b"\x02\x01" or
            struct.unpack_from("<H",raw,18)[0] != 183):
            raise ValueError("Expected little-endian ELF64 AArch64")
        self.phoff = struct.unpack_from("<Q",raw,32)[0]
        self.shoff = struct.unpack_from("<Q",raw,40)[0]
        self.phentsize, self.phnum, self.shentsize, self.shnum, self.shstrndx = struct.unpack_from(
            "<HHHHH",raw,54
        )
        if self.phnum > 500 or self.shnum > 3000:
            raise ValueError("Suspicious ELF program or section count")
        self.segments = self._parse_segments()
        self.sections = self._parse_sections()

    def _parse_segments(self):
        out=[]
        if not self.phnum:
            return out
        if self.phentsize < 56 or self.phoff + self.phnum * self.phentsize > len(self.raw):
            raise ValueError("ELF program header bounds invalid")
        for i in range(self.phnum):
            ptype,flags,off,addr,paddr,filesz,memsz,align=struct.unpack_from(
                "<IIQQQQQQ",self.raw,self.phoff+i*self.phentsize)
            if off > len(self.raw) or filesz > len(self.raw)-off:
                raise ValueError("ELF segment outside file")
            if ptype == 1 and filesz:
                out.append({"name":f"PT_LOAD[{i}]","off":off,"addr":addr,
                            "size":filesz,"flags":flags,"kind":"segment"})
        return out

    def _parse_sections(self):
        out=[]
        if not self.shnum:
            return out
        if self.shentsize < 64 or self.shoff + self.shnum*self.shentsize > len(self.raw):
            raise ValueError("ELF section header bounds invalid")
        hdr=[]
        for i in range(self.shnum):
            vals=struct.unpack_from("<IIQQQQIIQQ",self.raw,self.shoff+i*self.shentsize)
            name,stype,flags,addr,off,size,link,info,align,entsize=vals
            if stype != 8 and (off > len(self.raw) or size > len(self.raw)-off):
                raise ValueError("ELF section outside file")
            if stype in (2,11) and (link >= self.shnum or entsize < 24):
                raise ValueError("Broken ELF symbol table linkage")
            hdr.append({"nameoff":name,"stype":stype,"flags":flags,"addr":addr,
                        "off":off,"size":size,"link":link,"entsize":entsize,
                        "kind":"section"})
        strings=b""
        if self.shstrndx < self.shnum:
            st=hdr[self.shstrndx]
            if st["stype"] == 3:
                strings=self.raw[st["off"]:st["off"]+st["size"]]
        for i,section in enumerate(hdr):
            nameoff=section["nameoff"]
            end=strings.find(b"\x00",nameoff) if nameoff<len(strings) else -1
            section["name"]=(strings[nameoff:end].decode("utf-8","replace")
                             if end>=0 else f"SH[{i}]")
        return hdr

    def data_regions(self):
        # SHF_ALLOC but not SHF_EXECINSTR or SHT_NOBITS; if no sections,
        # use non-executable load segments.
        regions=[s for s in self.sections
                 if s["stype"] in (1,3) and (s["flags"]&2) and not (s["flags"]&4)
                 and s["size"]]
        if regions:return regions
        return [s for s in self.segments if not(s["flags"]&1)]

    def text_regions(self):
        regions=[s for s in self.sections if s["stype"] == 1
                 and (s["flags"]&2) and (s["flags"]&4) and s["size"]]
        if regions:return regions
        return [s for s in self.segments if s["flags"]&1]

    def location(self,off):
        # Prefer named allocated section; fallback to load segment.
        for group in (self.sections,self.segments):
            for r in group:
                if r["size"] and r["off"] <= off < r["off"]+r["size"] and (
                    r["kind"]=="segment" or (r["flags"]&2 and r["stype"]!=8)
                ):
                    return r["addr"]+off-r["off"],r["name"]
        return None,"NO_ALLOCATED_FILE_MAPPING"

    def symbols(self):
        out=[]
        for section in self.sections:
            if section["stype"] not in (2,11) or not section["entsize"]:
                continue
            link=self.sections[section["link"]]
            if link["stype"]!=3:
                raise ValueError("ELF symbol section does not point to STRTAB")
            names=self.raw[link["off"]:link["off"]+link["size"]]
            n=section["size"]//section["entsize"]
            if n>1_000_000:
                raise ValueError("ELF symbol table unreasonably long")
            for i in range(n):
                pos=section["off"]+i*section["entsize"]
                nameoff,info,other,shndx,val,size=struct.unpack_from("<IBBHQQ",self.raw,pos)
                if nameoff>=len(names):
                    continue
                end=names.find(b"\x00",nameoff)
                if end<0:continue
                name=names[nameoff:end]
                if name and TERMS.search(name):
                    out.append((name.decode("ascii","replace"),val,shndx,section["name"]))
        return out


def signed(value,bits):
    return value-(1<<bits) if value&(1<<(bits-1)) else value


def decode_adrp(word,pc):
    if (word&0x9F000000) != 0x90000000:
        return None
    imm=signed((((word>>5)&0x7FFFF)<<2)|((word>>29)&3),21)
    return (word&31,(pc&~4095)+(imm<<12))


def decode_adr(word,pc):
    if (word&0x9F000000) != 0x10000000:
        return None
    imm=signed((((word>>5)&0x7FFFF)<<2)|((word>>29)&3),21)
    return (word&31,pc+imm)


def decode_add_x_imm(word):
    # AArch64 64-bit ADD immediate; rd, rn and scaled imm12.
    if (word & 0xFF000000) not in (0x91000000,):
        return None
    rn=(word>>5)&31
    rd=word&31
    shift=(word>>22)&1
    imm=((word>>10)&4095) << (12 if shift else 0)
    return rd,rn,imm


def scan_strings(elf:ELF64,module,limit=2500):
    seen=set()
    hits=[]
    for region in elf.data_regions():
        off=region["off"]
        chunk=elf.raw[off:off+region["size"]]
        for m in STRING_PATTERN.finditer(chunk):
            txt=m.group()
            found=TERMS.search(txt)
            if not found:continue
            file_off=off+m.start()
            key=(file_off,region["name"])
            if key in seen:continue
            seen.add(key)
            va=region["addr"]+m.start()
            # Avoid dumping giant opaque strings or copyrighted resource data.
            snippet=txt[:180].decode("ascii","replace")
            token=found.group().decode("ascii","replace")
            hits.append((module,"ELF_ALLOCATED_ASCII_STRING",token,
                         f"0x{file_off:X}",f"0x{va:X}",region["name"],snippet))
    hits.sort(key=lambda r:int(r[3],16))
    return hits[:limit],len(hits),len(hits)>limit


def scan_adr_xrefs(elf:ELF64,module,hits,limit=1500):
    # Exact ADR/ADRP+ADD observed instruction references only, never call graph.
    target={int(row[4],16):row for row in hits}
    if not target:return []
    out=[]
    for region in elf.text_regions():
        chunk=elf.raw[region["off"]:region["off"]+region["size"]]
        n=len(chunk)//4
        for i in range(n):
            w=struct.unpack_from("<I",chunk,i*4)[0]
            pc=region["addr"]+4*i
            adr=decode_adr(w,pc)
            if adr and adr[1] in target:
                found=target[adr[1]]
                out.append((module,f"0x{adr[1]:X}",found[6],f"0x{pc:X}",
                            f"0x{region['off']+i*4:X}",
                            "NATIVE_AARCH64_ADR_EXACT_STRING_ADDR",found[5],region["name"]))
            page=decode_adrp(w,pc)
            if page:
                reg,base=page
                for gap in (1,2,3):
                    j=i+gap
                    if j>=n:break
                    add=decode_add_x_imm(struct.unpack_from("<I",chunk,j*4)[0])
                    if add and add[1]==reg and add[0]==reg:
                        addr=base+add[2]
                        if addr in target:
                            found=target[addr]
                            out.append((module,f"0x{addr:X}",found[6],f"0x{pc:X}",
                                        f"0x{region['off']+i*4:X}",
                                        f"NATIVE_AARCH64_ADRP_ADD_GAP{gap}",
                                        found[5],region["name"]))
    out.sort(key=lambda r:(int(r[3],16),r[1]))
    return out[:limit]


def scan_hashes(elf:ELF64,module):
    out=[]
    for kind,ident in [("S",s) for s in S_GAPS]+[("C",CLASS_IK)]:
        value=int(ident,16)
        for variant,needle in (
            ("ASCII_PREFIXED",(kind+ident).encode("ascii")),
            ("ASCII_HEX",ident.encode("ascii")),
            ("LITTLE_ENDIAN_UINT64",struct.pack("<Q",value)),
            ("BIG_ENDIAN_UINT64",struct.pack(">Q",value)),
        ):
            at=0
            while True:
                at=elf.raw.find(needle,at)
                if at<0:break
                address,region=elf.location(at)
                out.append((module,kind,ident,variant,f"0x{at:X}",
                            "" if address is None else f"0x{address:X}",region,
                            "ELF_BYTE_MATCH_NOT_PROVEN_RUNTIME_HASH_USE"))
                if len(out)>2000:
                    raise ValueError("Too many exact hash probes; audit input interpretation")
                at+=1
    return out


def dump(path,head,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.writer(f,delimiter="\t",lineterminator="\n")
        writer.writerow(head)
        writer.writerows(rows)


def run(root=ROOT,out=NATIVE,modules=MODULES):
    exefs=root/"Unpack/v2.0.2/exefs"
    manifest_path=exefs/"exefs-manifest.json"
    manifest=json.loads(manifest_path.read_text("utf-8"))
    if manifest.get("version")!="v2.0.2":
        raise ValueError("Missing pinned v2.0.2 ExeFS manifest")
    hits,xrefs,probes=[],[],[]
    per={}
    for module in modules:
        if module not in MODULES:
            raise ValueError("Only pinned main/sdk/rtld module names permitted")
        item=manifest["modules"][module]
        file=exefs/module/(module+".elf")
        raw=file.read_bytes()
        sha=hashlib.sha256(raw).hexdigest()
        if (item["status"]!="VERIFIED_ARTIFACTS" or item["elfSize"]!=len(raw)
            or item["elfSha256"].lower()!=sha):
            raise ValueError("Game ELF bytes differ from original verified SHA/length: "+module)
        elf=ELF64(raw)
        seen,total,truncated=scan_strings(elf,module)
        ref=scan_adr_xrefs(elf,module,seen)
        hash_matches=scan_hashes(elf,module)
        syms=elf.symbols()
        hits.extend(seen)
        xrefs.extend(ref)
        probes.extend(hash_matches)
        per[module]={
            "sha256":sha,"elf_bytes":len(raw),
            "machine":"ELF64_LE_AARCH64",
            "load_segments":len(elf.segments),"sections":len(elf.sections),
            "executable_regions":len(elf.text_regions()),
            "string_regions":len(elf.data_regions()),
            "matching_lua_loader_related_strings":total,
            "reported_string_records":len(seen),
            "string_list_truncated":truncated,
            "exact_adr_or_adrp_add_xrefs":len(ref),
            "matching_named_symbols":len(syms),
            "symbol_examples":syms[:50],
            "exact_missing_s_or_ik_c_hash_byte_occurrences":len(hash_matches)
        }
    out.mkdir(parents=True,exist_ok=True)
    dump(out/"native-host-elf-string-locators.tsv",HIT_COLS,hits)
    dump(out/"native-host-elf-adr-references.tsv",XREF_COLS,xrefs)
    dump(out/"native-host-elf-hash-probes.tsv",HASH_COLS,probes)
    result={
        "game":"Pokemon Legends Z-A","version":"v2.0.2",
        "manifest_sha256":hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "modules":per,"total_candidate_strings":sum(x["matching_lua_loader_related_strings"] for x in per.values()),
        "total_exact_string_address_references":len(xrefs),
        "total_exact_hash_byte_matches":len(probes),
        "host_lua_loader_confirmed":False,"lua_root_upvalue_runtime_binding_confirmed":False,
        "ik_script_command_runtime_value_confirmed":False,
        "original_hash_names_recovered":0,
        "warning":"All ELF observations are offline bytes/string/symbol/PC references only. A string address xref is not a function callsite or a runtime environment binding. Missing byte patterns do not prove absent logic."
    }
    (out/"native-host-elf-probe-summary.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root",type=Path,default=ROOT)
    ap.add_argument("--out",type=Path,default=NATIVE)
    ap.add_argument("--modules",nargs="+",choices=MODULES,default=list(MODULES))
    args=ap.parse_args()
    result=run(args.repo_root,args.out,tuple(args.modules))
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
