"""No-game-data NPDM extraction tests."""
import importlib.util
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("npdm_extractor", ROOT / "scripts" / "Extract-ZA-NPDM.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def fake_npdm():
    raw = bytearray(0x180)
    raw[:4] = b"META"
    raw[0x20:0x2b] = b"Application"
    struct.pack_into("<4I", raw, 0x70, 0x120, 0x30, 0x80, 0x60)
    raw[0x80:0x84] = b"ACID"
    raw[0x120:0x124] = b"ACI0"
    return raw

class TestNPDM(unittest.TestCase):
    def test_good(self):
        info, sections = module.extract_npdm(bytes(fake_npdm()))
        self.assertEqual([len(sections["ACID"]), len(sections["ACI0"])], [0x60, 0x30])
        self.assertEqual([x["offset"] for x in info["sections"]], [0x80, 0x120])
        self.assertEqual(info["titleAsciiCandidate"], "Application")

    def test_bad_bounds_and_magic(self):
        raw = fake_npdm()
        struct.pack_into("<I", raw, 0x74, 0x100000)
        with self.assertRaises(ValueError):
            module.extract_npdm(bytes(raw))
        raw = fake_npdm()
        raw[0x120:0x124] = b"NOPE"
        with self.assertRaises(ValueError):
            module.extract_npdm(bytes(raw))

    def test_overlap(self):
        raw = fake_npdm()
        struct.pack_into("<I", raw, 0x70, 0xC0)
        raw[0xC0:0xC4] = b"ACI0"
        with self.assertRaises(ValueError):
            module.extract_npdm(bytes(raw))

if __name__ == "__main__":
    unittest.main()
