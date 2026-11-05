#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

MOD = Path(__file__).resolve().parents[1] / "scripts/Convert-ZA-Virtual.py"
spec = importlib.util.spec_from_file_location("za_virtual_converter", MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ZAVirtualConverterTests(unittest.TestCase):
    def test_ahtb_exact_names(self):
        rows = [(0x123456789ABCDEF0, "hello"), (42, "msg_ui_example")]
        b = b"AHTB" + struct.pack("<I", len(rows))
        for key, name in rows:
            raw = name.encode() + b"\0"
            b += struct.pack("<QH", key, len(raw)) + raw
        parsed = m.ahtb(b)
        self.assertEqual(parsed["count"], 2)
        self.assertEqual(parsed["entries"][0]["hash"], "123456789ABCDEF0")
        self.assertEqual(parsed["entries"][1]["name"], "msg_ui_example")
        with self.assertRaises(ValueError):
            m.ahtb(b[:-2])

    def test_flatbuffer_table(self):
        # root_offset=12; vtable at 4; object size 8 and one 4-byte field.
        b = bytearray(24)
        struct.pack_into("<I", b, 0, 12)
        struct.pack_into("<HHH", b, 4, 6, 8, 4)
        struct.pack_into("<i", b, 12, 8)
        struct.pack_into("<I", b, 16, 123)
        parsed = m.flatbuffer_structure(bytes(b))
        self.assertEqual(parsed["fieldOffsets"], [4])
        self.assertEqual(parsed["vtableOffset"], 4)
        with self.assertRaises(ValueError):
            m.flatbuffer_structure(b"\xff" * 24)

    def test_message_header_not_text(self):
        b = struct.pack("<HHIIiI", 1, 2, 40, 0, 16, 40) + b"\0" * 32
        result = m.dat_header(b)
        self.assertEqual(result["textCount"], 2)
        self.assertIn("NOT decoded", result["note"])

    def test_transform_outputs_and_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            source, dest = Path(td) / "bag.tbl", Path(td) / "converted"
            source.write_bytes(b"AHTB" + struct.pack("<I", 0))
            state, outputs, _ = m.transform(source, "ik_message/dat/English/bag.tbl", dest)
            self.assertEqual(state, "CONVERTED")
            self.assertEqual(json.loads(outputs[0].read_text())["count"], 0)
            unknown = Path(td) / "blob.unsupported"
            unknown.write_bytes(b"random\x00\x01")
            state, paths, _ = m.transform(unknown, "ik_pokemon/blob.unsupported", dest)
            self.assertEqual(state, "UNSUPPORTED")
            self.assertEqual(paths, [])

    def test_existing_source_is_never_modified(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src = base / "virtual" / "avalon" / "x.foo"
            src.parent.mkdir(parents=True)
            src.write_bytes(b"\x00\x01")
            output = base / "virtual_converted"
            first = m.convert_one(src, base / "virtual", output, {}, "7z")
            self.assertEqual(first["status"], "UNSUPPORTED")
            self.assertEqual(src.read_bytes(), b"\x00\x01")
            second = m.convert_one(src, base / "virtual", output,
                                   {first["sourcePath"]: first}, "7z")
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
