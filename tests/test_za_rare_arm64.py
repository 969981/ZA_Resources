#!/usr/bin/env python3
"""Synthetic-only verification for ZA Rare static candidate scanner."""
import importlib.util
import struct
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts/Scan-ZA-Rare-ARM64.py"
spec = importlib.util.spec_from_file_location("za_rare_static_scan", MODULE)
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)

class RareArm64Tests(unittest.TestCase):
    def test_logical_imm_never(self):
        # ORR W0, W1, #0x1FFFFFFF
        word = 0x32000000 | (28 << 10) | (1 << 5)
        self.assertEqual(scan.logical_imm(word), (32, 0x1FFFFFFF, "ORR", 0, 1))

    def test_logical_imm_random(self):
        # ORR W3, W4, #0x3FFFFFFF
        word = 0x32000000 | (29 << 10) | (4 << 5) | 3
        self.assertEqual(scan.logical_imm(word), (32, 0x3FFFFFFF, "ORR", 3, 4))

    def test_anti_shiny_eor_opcode(self):
        # Observed opcode shape: EOR W9, W1, #0x10000000.
        self.assertEqual(scan.logical_imm(0x52040029), (32, 0x10000000, "EOR", 9, 1))

    def test_invalid_mask(self):
        self.assertIsNone(scan.logical_imm(0xD503201F))  # NOP
        self.assertIsNone(scan.logical_imm(0xFFFFFFFF))

    def test_branch(self):
        self.assertEqual(scan.branch_kind(0x94000001), "BL")
        self.assertEqual(scan.branch_dest(0x94000001, 0x1000), 0x1004)
        self.assertEqual(scan.branch_kind(0xD503201F), None)

    def test_synthetic_elf(self):
        b = bytearray(0x300)
        b[:6] = b"\x7fELF\x02\x01"
        struct.pack_into("<H", b, 18, 183)
        struct.pack_into("<Q", b, 32, 64)
        struct.pack_into("<HH", b, 54, 56, 1)
        struct.pack_into("<IIQQQQQQ", b, 64, 1, 5, 0x200, 0x4000, 0x4000, 16, 16, 0x1000)
        struct.pack_into("<I", b, 0x200, 0x32000000 | (28 << 10) | (1 << 5))
        struct.pack_into("<I", b, 0x204, 0x54000020)
        elf = scan.ELF(bytes(b))
        report = scan.scan(elf, 10)
        self.assertEqual(report["all_matching_instruction_count"], 1)
        self.assertEqual(report["ranked_groups"][0]["first_pc"], "0x4000")
        self.assertEqual(report["data_literal_count"], 0)
        self.assertIn("AArch64 logical-immediate use is not proof", report["warnings"][0])

    def test_synthetic_battle(self):
        # FlatBuffers root -> vector[1] -> table with field0 name and field1 actor
        b = bytearray(192)
        struct.pack_into("<I", b, 0, 12)       # root
        struct.pack_into("<i", b, 12, 6)       # vtable at 6
        struct.pack_into("<HHH", b, 6, 6, 8, 4)
        struct.pack_into("<I", b, 16, 4)       # vector at 20
        struct.pack_into("<I", b, 20, 1)
        struct.pack_into("<I", b, 24, 16)      # table at 40
        struct.pack_into("<i", b, 40, 12)      # vtable at 28
        struct.pack_into("<HHHH", b, 28, 8, 12, 4, 8)
        struct.pack_into("<I", b, 44, 32)      # string at 76
        struct.pack_into("<I", b, 48, 52)      # actor at 100
        s1, s2 = b"btl_sub_119", b"id_sub119_01"
        struct.pack_into("<I", b, 76, len(s1))
        b[80:80+len(s1)] = s1
        struct.pack_into("<I", b, 100, len(s2))
        b[104:104+len(s2)] = s2
        d = scan.fb_battle_records(bytes(b))
        self.assertEqual(d["record_count"], 1)
        self.assertEqual(d["matching_battles"][0]["actor_id"], "id_sub119_01")

if __name__ == "__main__":
    unittest.main()
