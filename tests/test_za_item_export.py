#!/usr/bin/env python3
"""Synthetic tests for the dependency-free ZA ItemData exporter."""
import importlib.util
import struct
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "Export-ZA-Items.py"
spec = importlib.util.spec_from_file_location("za_item_export", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestZAItems(unittest.TestCase):
    def test_schema_field_annotations(self):
        schema = """table ItemData {
    Id:int (key);
    ItemType:ItemType;
    InternalName:string (required);
    MachineWaza:WazaID;
}
table ItemDataArray { Table:[ItemData] (required); }"""
        self.assertEqual(
            module.schema_fields(schema),
            [("Id", "int"), ("ItemType", "ItemType"),
             ("InternalName", "string"), ("MachineWaza", "WazaID")],
        )

    def test_single_record_ushort_enum(self):
        data = bytearray(128)
        struct.pack_into("<I", data, 0, 20)  # root object
        struct.pack_into("<HHH", data, 8, 6, 8, 4)  # root vtable
        struct.pack_into("<iI", data, 20, 12, 12)  # field at 24 -> vector 36
        struct.pack_into("<II", data, 36, 1, 60)  # vector[0] at 40 -> table 100
        struct.pack_into("<HHHHH", data, 64, 10, 16, 4, 8, 12)
        struct.pack_into("<i", data, 100, 36)  # table -> vtable at 64
        struct.pack_into("<i", data, 104, 777)
        struct.pack_into("<i", data, 108, 7)
        struct.pack_into("<H", data, 112, 65535)
        fields = [("Id", "int"), ("ItemType", "ItemType"), ("MachineWaza", "WazaID")]
        self.assertEqual(module.FlatReader(bytes(data)).records(fields),
                         [{"Id": 777, "ItemType": 7, "MachineWaza": 65535}])

    def test_bounds(self):
        with self.assertRaises(ValueError):
            module.FlatReader(b"\x00\x01").read("I", 0)

    def test_mega_and_orb_group(self):
        self.assertEqual(module.group({"NameZH": "耿鬼进化石", "NameEN": "Gengarite"}), "MegaStone")
        self.assertEqual(module.group({"NameZH": "进化奇石", "NameEN": "Eviolite"}), "Other")
        self.assertEqual(module.group({"NameZH": "朱红色宝珠", "NameEN": "Red Orb"}), "PrimalOrb")
        self.assertEqual(module.group({"NameZH": "靛蓝色宝珠", "NameEN": "Blue Orb"}), "PrimalOrb")

    def test_real_resource_if_available(self):
        repo = Path(__file__).resolve().parents[1]
        path = repo / "Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/world/exl/item_data/item_data/item_data.bin"
        schema_path = repo / "tools/pkNX/FlatBuffers/ZA/Item/Schemas/ItemDataArray.fbs"
        if not path.is_file() or not schema_path.is_file():
            self.skipTest("real item resource and/or schema not in sparse checkout")
        rows = module.FlatReader(path.read_bytes()).records(
            module.schema_fields(schema_path.read_text(encoding="utf-8"))
        )
        self.assertEqual(len(rows), 535)
        self.assertEqual(len({x["Id"] for x in rows}), 535)


if __name__ == "__main__":
    unittest.main()
