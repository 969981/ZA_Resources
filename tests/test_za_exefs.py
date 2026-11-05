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
    raw = bytearray(0x500)
    raw[:4] = b"META"
    raw[0x20:0x2b] = b"Application"
    struct.pack_into("<4I", raw, 0x70, 0x420, 0x30, 0x80, 0x380)
    raw[0x280:0x284] = b"ACID"
    raw[0x420:0x424] = b"ACI0"
    return raw

class TestNPDM(unittest.TestCase):
    def test_good(self):
        info, sections = module.extract_npdm(bytes(fake_npdm()))
        self.assertEqual([len(sections["ACID"]), len(sections["ACI0"])], [0x380, 0x30])
        self.assertEqual([x["offset"] for x in info["sections"]], [0x80, 0x420])
        self.assertEqual(info["titleAsciiCandidate"], "Application")

    def test_bad_bounds_and_magic(self):
        raw = fake_npdm()
        struct.pack_into("<I", raw, 0x74, 0x100000)
        with self.assertRaises(ValueError):
            module.extract_npdm(bytes(raw))
        raw = fake_npdm()
        raw[0x420:0x424] = b"NOPE"
        with self.assertRaises(ValueError):
            module.extract_npdm(bytes(raw))

    def test_overlap(self):
        raw = fake_npdm()
        struct.pack_into("<I", raw, 0x70, 0x3C0)
        raw[0x3C0:0x3C4] = b"ACI0"
        with self.assertRaises(ValueError):
            module.extract_npdm(bytes(raw))

if __name__ == "__main__":
    unittest.main()
