"""Synthetic regression tests for ZA remaining RomFS Wwise / Trinity unpack."""
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "Extract-ZA-RomFS-Remainder.py"
spec = importlib.util.spec_from_file_location("za_remainder", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class RemainingRomFS(unittest.TestCase):
    def test_embedded_bank(self):
        riff = b"RIFF" + bytes(28)
        section = lambda t, p: t + struct.pack("<I", len(p)) + p
        raw = (section(b"BKHD", struct.pack("<II", 145, 444)) +
               section(b"DIDX", struct.pack("<III", 991, 0, len(riff))) +
               section(b"DATA", riff))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bank = root / "Example.bnk"
            bank.write_bytes(raw)
            result = mod.bnk(bank, root / "meta", root / "media")
            self.assertEqual(result["status"], "COMPLETE")
            self.assertEqual(result["embeddedMedia"][0]["id"], 991)
            self.assertEqual((root / "media/Example/991.wem").read_bytes(), riff)
            bank.write_bytes(raw[:-1])
            with self.assertRaises(ValueError):
                mod.bnk(bank, root / "meta", root / "media")

    def test_akpk_empty_and_media(self):
        languages = struct.pack("<III", 1, 12, 0) + b"sfx\x00"
        empty = struct.pack("<I", 0)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "LooseMedia.pck"
            size = 20 + 16 + 4 + 4 + 4
            pack.write_bytes(struct.pack("<4sIIIIII", b"AKPK", size, 1, 16, 4, 4, 4) +
                             languages + empty + empty + empty)
            result = mod.pck(pack, root / "meta", root / "media")
            self.assertEqual(result["items"], [])
            self.assertEqual(result["languages"], {"0": "sfx"})
            riff = b"RIFF" + bytes(20)
            size = 20 + 16 + 4 + 24 + 4
            position = 8 + size
            stream = struct.pack("<I", 1) + struct.pack("<IIIII", 123, 0, len(riff), position, 0)
            pack.write_bytes(struct.pack("<4sIIIIII", b"AKPK", size, 1, 16, 4, 24, 4) +
                             languages + empty + stream + empty + riff)
            result = mod.pck(pack, root / "meta", root / "media")
            self.assertEqual(result["items"][0]["id"], 123)
            self.assertEqual((root / "media/LooseMedia/stream/sfx/123.wem").read_bytes(), riff)
            pack.write_bytes(pack.read_bytes()[:-1])
            with self.assertRaises(ValueError):
                mod.pck(pack, root / "meta", root / "media")

    def test_trinity_config_no_invented_values(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "trinity_config.trowc"
            src.write_bytes(b"appHeap\x00\x07\x08graphics\x00\x00")
            result = mod.config(src, root / "out")
            self.assertEqual(result["status"], "PARTIAL")
            self.assertEqual([x["value"] for x in result["observedNullTerminatedStrings"]],
                             ["appHeap", "graphics"])
            self.assertEqual((root / "out/trinity_config.trowc").read_bytes(), src.read_bytes())

if __name__ == "__main__":
    unittest.main()
