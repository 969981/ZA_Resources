#!/usr/bin/env python3
"""Z-A v2.0.2 static, read-only AArch64 Rare-value candidate scan.

Never labels candidate instruction addresses as verified runtime functions.
Only operates on checked, unmodified game resources.
No external dependencies.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ELF = ROOT / "Unpack/v2.0.2/exefs/main/main.elf"
DEFAULT_BATTLE = ROOT / "Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/ik_event/bin/event_wild_battle_data/wild_btl_data_global.bin"
MANIFEST = ROOT / "Unpack/v2.0.2/exefs/exefs-manifest.json"
OUTPUT = ROOT / "docs/research/v2.0.2/za-rare-arm64-static-candidates.json"
MAPPED_RARE = {0x1FFFFFFF: "Never", 0x2FFFFFFF: "Always", 0x3FFFFFFF: "Random"}
WATCH = {0x1FFFFFFF, 0x2FFFFFFF, 0x3FFFFFFF, 0x0FFFFFFF, 0x10000000,
         0x20000000, 0x30000000, 0xC0000000, 0xE0000000, 0xF0000000}

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sgn(x: int, bits: int) -> int:
    return x - (1 << bits) if x & (1 << (bits - 1)) else x

def ror(value: int, rot: int, bits: int) -> int:
    mask = (1 << bits) - 1
    rot %= bits
    return ((value >> rot) | (value << (bits - rot))) & mask

def logical_imm(w: int):
    """Decode the AArch64 logical-immediate N:immr:imms bitmask."""
    if (w & 0x1F800000) != 0x12000000:
        return None
    bits = 64 if (w >> 31) & 1 else 32
    n, immr, imms = (w >> 22) & 1, (w >> 16) & 63, (w >> 10) & 63
    if bits == 32 and n:
        return None
    value = (n << 6) | ((~imms) & 63)
    if value == 0:
        return None
    length = value.bit_length() - 1
    if length < 1:
        return None
    esize = 1 << length
    levels = esize - 1
    s, r = imms & levels, immr & levels
    if s == levels:
        return None
    elem = ror((1 << (s + 1)) - 1, r, esize)
    result = 0
    for shift in range(0, bits, esize):
        result |= elem << shift
    opc = (w >> 29) & 3
    op = ("AND", "ORR", "EOR", "ANDS")[opc]
    return bits, result, op, w & 31, (w >> 5) & 31

def branch_kind(w: int):
    if (w & 0xFC000000) == 0x94000000:
        return "BL"
    if (w & 0xFC000000) == 0x14000000:
        return "B"
    if (w & 0xFF000010) == 0x54000000:
        return "B.cond"
    if (w & 0x7E000000) == 0x34000000:
        return "CBZ/CBNZ"
    if (w & 0x7E000000) == 0x36000000:
        return "TBZ/TBNZ"
    if (w & 0xFFFFFC1F) == 0xD63F0000:
        return "BLR"
    return None

def branch_dest(w: int, pc: int):
    if (w & 0xFC000000) in (0x94000000, 0x14000000):
        return pc + (sgn(w & 0x03FFFFFF, 26) << 2)
    if (w & 0xFF000010) == 0x54000000 or (w & 0x7E000000) == 0x34000000:
        return pc + (sgn((w >> 5) & 0x7FFFF, 19) << 2)
    if (w & 0x7E000000) == 0x36000000:
        return pc + (sgn((w >> 5) & 0x3FFF, 14) << 2)
    return None

class ELF:
    def __init__(self, raw: bytes):
        self.raw = raw
        if len(raw) < 64 or raw[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H", raw, 18)[0] != 183:
            raise ValueError("expected AArch64 ELF64 little-endian")
        phoff = struct.unpack_from("<Q", raw, 32)[0]
        esize, num = struct.unpack_from("<HH", raw, 54)
        if esize < 56 or num > 100 or phoff + esize * num > len(raw):
            raise ValueError("invalid program header layout")
        self.segments = []
        for i in range(num):
            kind, flags, offset, va, _, filesz, _, _ = struct.unpack_from("<IIQQQQQQ", raw, phoff + esize * i)
            if offset + filesz > len(raw):
                raise ValueError("segment out of bounds")
            if kind == 1 and filesz:
                self.segments.append({"offset": offset, "va": va, "size": filesz, "flags": flags})
        if not self.segments:
            raise ValueError("no PT_LOAD segments")
    def executable(self):
        return [seg for seg in self.segments if seg["flags"] & 1]
    def data(self):
        return [seg for seg in self.segments if not seg["flags"] & 1]

def fb_battle_records(data: bytes):
    """Read only observed fields 0/1/9/14; do not assume unknown field semantics."""
    def check(p, n=4):
        if p < 0 or n < 0 or p + n > len(data):
            raise ValueError("out of bounds")
    def u32(p):
        check(p)
        return struct.unpack_from("<I", data, p)[0]
    def i32(p):
        check(p)
        return struct.unpack_from("<i", data, p)[0]
    def u16(p):
        check(p, 2)
        return struct.unpack_from("<H", data, p)[0]
    def pointer(p):
        return p + u32(p)
    def field(t, index):
        vt = t - i32(t)
        n = u16(vt)
        if n < 4 or n > 256:
            raise ValueError("invalid vtable")
        if 4 + 2 * index >= n:
            return None
        off = u16(vt + 4 + 2 * index)
        return t + off if off else None
    def string(f):
        if f is None:
            return None
        at = pointer(f)
        n = u32(at)
        if n > 10000:
            raise ValueError("unexpected string length")
        check(at + 4, n)
        return data[at+4:at+4+n].decode("utf-8", "replace")
    root = u32(0)
    root_vec_off = field(root, 0)
    if root_vec_off is None:
        raise ValueError("missing root vector")
    v = pointer(root_vec_off)
    count = u32(v)
    if count > 10000:
        raise ValueError("unexpected record count")
    out = []
    for j in range(count):
        ep = v + 4 + j * 4
        t = pointer(ep)
        name = string(field(t, 0))
        if name in ("btl_sub_119", "btl_sub_120"):
            out.append({
                "record_index": j,
                "table_file_offset": "0x%X" % t,
                "battle_id": name,
                "actor_id": string(field(t, 1)),
                "event_id": string(field(t, 9)),
                "optional_context_id": string(field(t, 14)),
            })
    return {"record_count": count, "matching_battles": out}

def scan(elf: ELF, limit: int):
    hits = []
    opcounts = Counter()
    regions = elf.executable()
    for region in regions:
        chunk = elf.raw[region["offset"]:region["offset"] + region["size"]]
        for o in range(0, len(chunk) - 3, 4):
            w = struct.unpack_from("<I", chunk, o)[0]
            imm = logical_imm(w)
            if imm is None:
                continue
            bits, mask, op, rd, rn = imm
            if mask not in WATCH:
                continue
            pc = region["va"] + o
            opcounts["0x%X" % mask] += 1
            ctx = []
            for rel in range(-32, 36, 4):
                off = o + rel
                if off < 0 or off + 4 > len(chunk):
                    continue
                word = struct.unpack_from("<I", chunk, off)[0]
                kind = branch_kind(word)
                if kind:
                    dest = branch_dest(word, region["va"] + off)
                    ctx.append({"pc": "0x%X" % (region["va"]+off), "kind": kind,
                                "target": "0x%X" % dest if dest is not None else None})
            hits.append({"pc": "0x%X" % pc, "pc_int": pc,
                         "file_offset": "0x%X" % (region["offset"] + o),
                         "instruction": "0x%08X" % w, "operation": op,
                         "registers": [rn, rd], "width": bits,
                         "immediate": "0x%X" % mask,
                         "nearby_branches": ctx[:30]})
    hits.sort(key=lambda h: h["pc_int"])
    # Group same-class candidate sites within a bounded 256-byte window.
    groups = []
    for h in hits:
        if groups and h["pc_int"] - groups[-1][-1]["pc_int"] <= 256:
            groups[-1].append(h)
        else:
            groups.append([h])
    def score(g):
        distinct = len(set(x["immediate"] for x in g))
        return distinct * 10 + len(g) * 2 + min(20, sum(len(x["nearby_branches"]) for x in g))
    top = sorted(groups, key=lambda g: (-score(g), g[0]["pc_int"]))[:limit]
    candidates = [{"first_pc": "0x%X" % g[0]["pc_int"],
                   "last_pc": "0x%X" % g[-1]["pc_int"], "score_heuristic": score(g),
                   "distinct_immediates": sorted(set(x["immediate"] for x in g)),
                   "sites": [{k:v for k,v in x.items() if k != "pc_int"} for x in g[:20]]}
                  for g in top]
    literals = []
    for region in elf.data():
        chunk = elf.raw[region["offset"]:region["offset"]+region["size"]]
        for value, tag in MAPPED_RARE.items():
            needle = struct.pack("<I", value)
            idx = 0
            while True:
                idx = chunk.find(needle, idx)
                if idx < 0:
                    break
                literals.append({"value": "0x%X" % value, "shiny": tag,
                                 "va": "0x%X" % (region["va"]+idx),
                                 "file_offset": "0x%X" % (region["offset"]+idx)})
                idx += 1
    exact_never = [{k:v for k,v in h.items() if k != "pc_int"}
                   for h in hits if h["immediate"] == "0x1FFFFFFF"]
    anti_shiny_xor_candidates = [{k:v for k,v in h.items() if k != "pc_int"}
                                   for h in hits if h["immediate"] == "0x10000000" and h["operation"] == "EOR" and h["width"] == 32]
    return {"executable_segments": len(regions), "logical_immediate_counts": dict(opcounts),
            "all_matching_instruction_count": len(hits), "candidate_groups_count": len(groups),
            "exact_never_instruction_sites": exact_never,
            "anti_shiny_xor_candidates": anti_shiny_xor_candidates,
            "anti_shiny_candidates_explanation": "EOR W*,W*,#0x10000000 is only an opcode-pattern clue from PKHeX LumioseRNG.AntiShiny. It does not prove a PID source or shiny state.",
            "ranked_groups": candidates, "data_literal_count": len(literals),
            "data_literals": literals[:200],
            "warnings": ["AArch64 logical-immediate use is not proof of Rare field use",
                         "Shared bitmasks and code dataflow can create false positives",
                         "Missing exact matches does not disprove compiled lock logic",
                         "PC values are ELF virtual addresses, not validated runtime main+offset"]}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--elf", type=Path, default=DEFAULT_ELF)
    p.add_argument("--battle", type=Path, default=DEFAULT_BATTLE)
    p.add_argument("--output", type=Path, default=OUTPUT)
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--skip-sha-check", action="store_true", help="synthetic fixtures only")
    args = p.parse_args()
    elfdata = args.elf.read_bytes()
    digest = sha256(elfdata)
    expected = json.loads(MANIFEST.read_text(encoding="utf-8"))["modules"]["main"]["elfSha256"]
    if not args.skip_sha_check and digest != expected:
        raise SystemExit("main.elf SHA mismatch; refusing to assign v2.0.2 address provenance")
    report = {
        "version": "ZA v2.0.2", "source_elf": str(args.elf),
        "elf_sha256": digest,
        "expected_elf_sha256": expected,
        "build_id_manifest": json.loads(MANIFEST.read_text(encoding="utf-8"))["modules"]["main"]["buildIdHex"],
        "evidence_level": "STATIC_CANDIDATE_ONLY",
        "runtime_call_chain_verified": False,
        "shiny_lock_branch_verified": False,
        "rare_mapping_pkNX": { "0x%X" % k:v for k,v in MAPPED_RARE.items() },
        "battles": fb_battle_records(args.battle.read_bytes()),
        "arm64_scan": scan(ELF(elfdata), max(1, args.limit)),
        "next_validation": [
            "Follow battle actor id_sub119_01/id_sub120_01 to encounter-data consumer",
            "Disassemble ranked candidates and prove field load from EncountData.Rare",
            "Trace caller/callee into Pokemon PID generation with GDB",
            "Compare Shiny.Never against Shiny.Always and Shiny.Random using same build",
            "Only label main+offset CONFIRMED after instruction, registers and before/after bytes are recorded",
        ]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "source_sha256":digest, "battle_matches":report["battles"]["matching_battles"],
        "logical_immediate_counts":report["arm64_scan"]["logical_immediate_counts"],
        "candidate_groups_count":report["arm64_scan"]["candidate_groups_count"],
        "top_10_candidate_pcs":[x["first_pc"] for x in report["arm64_scan"]["ranked_groups"][:10]],
        "runtime_verified":False,
    },indent=2))

if __name__ == "__main__":
    main()
