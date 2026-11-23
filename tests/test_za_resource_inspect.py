"""Synthetic FlatBuffers tests; no proprietary source files needed."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "encounters"))
from za_resource_inspect import FB, FlatBufferError


def scalar_root(value=42):
    b = bytearray(24)
    struct.pack_into("<I", b, 0, 12)          # root
    struct.pack_into("<HHH", b, 4, 6, 8, 4)   # vtable
    struct.pack_into("<iI", b, 12, 8, value)  # table body
    return bytes(b)


class FBTests(unittest.TestCase):
    def test_scalar_table_field(self):
        f = FB(scalar_root())
        self.assertEqual(f.root(), 12)
        self.assertEqual(f.field(12, 0), 16)
        self.assertEqual(f.number(12, 0), 42)
        self.assertIsNone(f.field(12, 1))
        self.assertEqual(f.number(12, 1), 0)

    def test_vector_of_table_offsets(self):
        b = bytearray(56)
        struct.pack_into("<I", b, 0, 12)
        struct.pack_into("<HHH", b, 4, 6, 8, 4)
        struct.pack_into("<iI", b, 12, 8, 4)     # field0 -> vector at 20
        struct.pack_into("<II", b, 20, 1, 16)    # 1 element, elem@24 -> table@40
        struct.pack_into("<HHH", b, 32, 6, 8, 4)
        struct.pack_into("<iI", b, 40, 8, 99)
        f = FB(bytes(b))
        self.assertEqual(f.tables(f.root(), 0), [40])
        self.assertEqual(f.number(40, 0), 99)

    def test_invalid_root(self):
        with self.assertRaises(FlatBufferError):
            FB(b"\xff\xff\xff\xff").root()

    def test_embedded_string(self):
        b = bytearray(32)
        struct.pack_into("<I", b, 0, 12)
        struct.pack_into("<HHH", b, 4, 6, 8, 4)
        struct.pack_into("<iI", b, 12, 8, 4)     # string at 20
        struct.pack_into("<I", b, 20, 3)
        b[24:27] = b"Z-A"
        self.assertEqual(FB(bytes(b)).string(12, 0), "Z-A")


if __name__ == "__main__":
    unittest.main()
