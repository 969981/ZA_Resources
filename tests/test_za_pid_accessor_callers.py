import hashlib
import importlib.util
import struct
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/Trace-ZA-PID-Accessor-Callers.py"
spec = importlib.util.spec_from_file_location("za_pid_accessor_callers", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def fixture():
    b = bytearray(0x300)
    b[:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<H", b, 18, 183)
    struct.pack_into("<Q", b, 32, 64)
    struct.pack_into("<HH", b, 54, 56, 1)
    base = 0xE50000
    struct.pack_into("<IIQQQQQQ", b, 64, 1, 5, 0x200, base, base, 0x40, 0x40, 0x1000)
    for i, name in enumerate(("species_set", "pid_set", "tid_sid_set", "experience_set")):
        pc = base + i * 8
        delta = (mod.KNOWN[name] - pc) // 4
        struct.pack_into("<I", b, 0x200 + i*8, 0x94000000 | (delta & 0x03FFFFFF))
        struct.pack_into("<I", b, 0x204 + i*8, 0xD503201F)
    return bytes(b)

class PIDAccessorTests(unittest.TestCase):
    def test_sign(self):
        self.assertEqual(mod.sign(0x03FFFFFF,26), -1)
        self.assertEqual(mod.sign(5,26), 5)
    def test_direct_branch(self):
        w = 0x94000001
        self.assertEqual(mod.branch_target(w, 0x1000), ("BL",0x1004))
        self.assertEqual(mod.branch_target(0x14000001, 0x1000), ("B",0x1004))
        self.assertIsNone(mod.branch_target(0xD503201F,0x1000))
    def test_scan_and_rank(self):
        raw=fixture()
        sha=hashlib.sha256(raw).hexdigest()
        report=mod.run(raw,sha,0x100,20)
        self.assertEqual(len(report["direct_refs"]),4)
        self.assertEqual(report["direct_ref_counts"]["pid_set"],1)
        self.assertGreaterEqual(len(report["ranked_callsite_windows"]),1)
        kinds=report["ranked_callsite_windows"][0]["target_kinds"]
        self.assertTrue({"pid_set","species_set","tid_sid_set","experience_set"}.issubset(kinds))
        self.assertFalse(report["verified_runtime_shiny_branch"])
    def test_refuse_mismatched_elf(self):
        with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
            mod.run(fixture(),"not-the-sha",0x800,20)
    def test_reject_invalid_elf(self):
        with self.assertRaisesRegex(ValueError,"ELF required|AArch64"):
            mod.load_segments(b"not ELF")

if __name__=="__main__":unittest.main()
