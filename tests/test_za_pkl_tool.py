"""Synthetic tests for the Z-A encounter PKL packer (no game resources needed)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import struct
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "encounters"))
from za_pkl_tool import read_sets, pack, inspect, PKLError, encode_slot


def slot(species=25, low=5, high=6, shiny=0, alpha=False, nature=-1):
    return dict(Species=species, Form=0, Gender=-1, LevelMin=low,
                LevelMax=high, Nature=nature, IsAlpha=alpha, Shiny=shiny)


class PKLTests(unittest.TestCase):
    def test_pkl_header_and_shiny_mapping(self):
        s = encode_slot(slot(shiny=1), 't', 123)
        self.assertEqual(s[-1], 2)  # pkNX Always=1, PKL Always=2
        self.assertEqual(s[2], 255)
        raw = pack({123: [s]})
        self.assertEqual(raw[:4], b'za\x01\x00')
        self.assertEqual(struct.unpack_from('<HH', raw, 4), (8, 20))
        self.assertEqual(raw[8:12], b'{\x00\x00\x00')
        self.assertEqual(inspect(raw)['slot_count'], 1)

    def test_overlap_and_dedup_across_files(self):
        with TemporaryDirectory() as d:
            p = [Path(d)/'t1_slot_sets.json', Path(d)/'t2_slot_sets.json']
            p[0].write_text(json.dumps({'Wild (12)': [slot(low=1, high=3), slot(species=151)]}))
            p[1].write_text(json.dumps({'Wild (12)': [slot(low=3, high=8), slot(low=9, high=10)]}))
            areas, _ = read_sets(p)
            data = pack(areas)
            self.assertEqual(inspect(data)['slot_count'], 3)
            self.assertEqual(inspect(data)['area_count'], 1)

    def test_invalid_fixed_nature_rejected(self):
        with self.assertRaises(PKLError):
            encode_slot(slot(nature=12), 't', 4)

    def test_nature_and_shiny_correct(self):
        for v, target in [(0,0),(1,2),(2,1),('Always',2),('Never',1),('Random',0)]:
            self.assertEqual(encode_slot(slot(shiny=v), 't', 4)[-1], target)

    def test_wrong_bin_rejected(self):
        with self.assertRaises(PKLError):
            inspect(b'\x80\x04pickle')
        with self.assertRaises(PKLError):
            inspect(b'za\x01\x00\x08\x00\x14\x00')

    def test_build_refuses_overwrite_existing_pkl(self):
        with TemporaryDirectory() as d:
            src = Path(d)/'t1_slot_sets.json'
            src.write_text(json.dumps({'Wild (12)': [slot()]}), encoding='utf-8')
            original = Path(d)/'encounter_za.pkl'
            original.write_bytes(b'unchanged-source')
            tool = Path(__file__).resolve().parents[1]/'scripts'/'encounters'/'za_pkl_tool.py'
            process = subprocess.run(
                [sys.executable, str(tool), '--build', str(src), '--out', str(original)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(original.read_bytes(), b'unchanged-source')

    def test_max_offset_rejected(self):
        with self.assertRaises(PKLError):
            pack({x: [encode_slot(slot(species=x * 20 + j), 't', x) for j in range(20)] for x in range(1, 450)})


if __name__ == '__main__':
    unittest.main()
