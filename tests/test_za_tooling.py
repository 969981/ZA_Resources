"""Synthetic regression tests: no game data, external tools, or network required."""
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(filename):
    p = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(filename.replace("-", "_").replace(".py", ""), p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class TestZATools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = load("Build-ZA-GFPAKHashCache.py")
        cls.elf = load("Convert-ZA-ExeFS.py")

    def test_hash_cache_binary_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            hashlist = root / "hashes.txt"
            hashlist.write_text("0123456789abcdef za/test/file.bin\n0123456789abcdef za/test/file.bin\nBAD bad\n", encoding="utf-8")
            mapping, stats = self.cache.read_hashlists([hashlist])
            self.assertEqual(mapping, {0x0123456789abcdef: "za/test/file.bin"})
            self.assertEqual(stats["duplicates"], 1)
            output = self.cache.create_cache(root / "hashcache.bin", mapping)
            b = output.read_bytes()
            self.assertEqual(int.from_bytes(b[0:8], "little"), 1)
            self.assertEqual(int.from_bytes(b[8:16], "little"), 0x0123456789abcdef)
            self.assertEqual(b[16], len("za/test/file.bin"))
            self.assertEqual(b[17:], b"za/test/file.bin")

    def test_nso_header_and_elf_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nso = root / "main"
            raw = bytearray(0x60)
            raw[:4] = b"NSO0"
            raw[0x40:0x60] = bytes(range(32))
            nso.write_bytes(raw)
            self.assertEqual(self.elf.verify_nso(nso), bytes(range(32)).hex())
            elf = root / "main.elf"
            header = bytearray(64)
            header[:6] = b"\x7fELF\x02\x01"
            header[18:20] = (183).to_bytes(2, "little")
            elf.write_bytes(header + bytes(4096))
            self.elf.verify_elf(elf)
            elf.write_bytes(b"broken")
            with self.assertRaises(ValueError):
                self.elf.verify_elf(elf)

if __name__ == "__main__":
    unittest.main()
