"""Synthetic ARM64 ELF fixture: native descriptor +0x68 exact access opcodes."""
from __future__ import annotations
import hashlib, importlib.util, struct, unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/Scan-ZA-Rare-Descriptor-Offset68.py"
s=importlib.util.spec_from_file_location("za_rare_offset68_scan", SCRIPT)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def elf():
    raw=bytearray(0x300);raw[:6]=b"\x7fELF\x02\x01"
    struct.pack_into("<H",raw,18,183)
    struct.pack_into("<Q",raw,32,64)
    struct.pack_into("<HH",raw,54,56,1)
    struct.pack_into("<IIQQQQQQ",raw,64,1,5,0x200,0x656000,0x656000,0x30,0x30,0x1000)
    enc=lambda base,imm,reg,breg:base|((imm//(8 if base&0x40000000 else 4))<<10)|(breg<<5)|reg
    # STR W8,[X20,#0x68]; LDR W8,[X24,#0x68].
    struct.pack_into("<I",raw,0x200,0xB9000000|((0x68//4)<<10)|(20<<5)|8)
    struct.pack_into("<I",raw,0x204,0xB9400000|((0x68//4)<<10)|(24<<5)|8)
    struct.pack_into("<I",raw,0x208,0xF9000000|((0x68//8)<<10)|(10<<5)|9)
    struct.pack_into("<I",raw,0x20c,0xD503201F)
    return bytes(raw)

class DescriptorOffset68Tests(unittest.TestCase):
    def test_detect_store_and_load(self):
        report=m.build(elf(),hashlib.sha256(elf()).hexdigest(),100)
        self.assertEqual(report["counts"]["STR_W"],1)
        self.assertEqual(report["counts"]["LDR_W"],1)
        self.assertEqual(report["counts"]["STR_X"],1)
        self.assertEqual(len(report["all_reference_sites"]),3)
        self.assertEqual(report["all_reference_sites"][0]["base"],20)
    def test_reject_unrelated_offsets(self):
        self.assertIsNone(m.decode(0xB9000000|((0x64//4)<<10)))
        self.assertIsNone(m.decode(0xD503201F))
    def test_reject_bad_sha(self):
        with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"):
            m.build(elf(),"abc",100)
    def test_reject_invalid_elf(self):
        with self.assertRaises(ValueError):m.segments(b"invalid")

if __name__=="__main__":unittest.main()
