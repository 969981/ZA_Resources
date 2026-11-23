"""PKHeX ZA BinLinker16 codec regression, entirely synthetic, stdlib only.

Optional official integration tested in CI using the two public PKHeX resource
files. No game resource binaries are committed in this test file.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "scripts" / "encounters"))
from za_pkl_codec import (
    PKLFormatError, check_original, diff, document, read_pkl, summary,
    validate_document, validate_slot, write_pkl,
)

CODEC = HERE / "scripts" / "encounters" / "za_pkl_codec.py"


def make_slot(species=25, gender=255, alpha=False, shiny="Random",
              low=5, high=6):
    return {"Species":species, "Form":0, "Gender":gender,
            "LevelMin":low, "LevelMax":high,
            "IsAlpha":alpha, "Shiny":shiny}


def sample():
    return [
        {"Location":12, "Slots":[make_slot(), make_slot(species=661, low=6, high=9)]},
        {"Location":273, "Slots":[make_slot(species=150, low=70,
                                           high=70, alpha=True, shiny="Never")]},
    ]


class ZAPKLCodecTests(unittest.TestCase):
    def test_byte_roundtrip_and_summary(self):
        raw = write_pkl(sample())
        self.assertEqual(raw[:4], b"za\x02\x00")
        self.assertEqual(raw, write_pkl(read_pkl(raw)))
        self.assertEqual(summary(raw)["slot_count"],3)
        self.assertEqual(summary(raw)["alpha_slots"],1)
        self.assertEqual(summary(raw)["shiny_counts"]["Never"],1)
        self.assertEqual(len(raw),4+6+2*(4)+3*8)

    def test_slot_length_and_end_offsets(self):
        raw=write_pkl(sample())
        self.assertEqual(struct.unpack_from("<HHH",raw,4),
                         (10,30,42))
        self.assertEqual(len(raw),42)

    def test_shiny_and_gender_encoding(self):
        for name, code in (("Random",0),("Never",1),("Always",2)):
            rec=validate_slot(make_slot(shiny=name,gender=-1))
            self.assertEqual(rec[2],255)
            self.assertEqual(rec[6],code)
        self.assertEqual(validate_slot(make_slot(shiny=2))[-1],2)

    def test_do_not_merge_or_reorder_slots(self):
        areas=[{"Location":234,"Slots":[
            make_slot(species=16,low=5,high=8),
            make_slot(species=16,low=3,high=5),
            make_slot(species=16,low=3,high=5)]}]
        raw=write_pkl(areas)
        self.assertEqual(read_pkl(raw),areas)
        self.assertEqual(raw,write_pkl(read_pkl(raw)))

    def test_reject_corrupted_format_and_offsets(self):
        for binary in (b"\x80\x04pickle",b"za\x01\x00\x08\x00\x14\x00"):
            with self.assertRaises(PKLFormatError):
                read_pkl(binary)
        raw=bytearray(write_pkl(sample()))
        struct.pack_into("<H",raw,6,9)
        with self.assertRaises(PKLFormatError):
            read_pkl(bytes(raw))

    def test_reject_bad_gender_shiny_alpha(self):
        for item in (
            make_slot(gender=42),make_slot(shiny="Unknown"),
            {**make_slot(),"IsAlpha":1},
            make_slot(species=0),make_slot(low=80,high=40),
        ):
            with self.subTest(item=item), self.assertRaises(PKLFormatError):
                validate_slot(item)

    def test_source_sha_guard(self):
        src=write_pkl(sample())
        doc=document(src)
        self.assertEqual(validate_document(doc),sample())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"original.pkl";p.write_bytes(src)
            check_original(p,doc)
            p.write_bytes(write_pkl([{"Location":12,"Slots":[make_slot()]}]))
            with self.assertRaises(PKLFormatError):
                check_original(p,doc)

    def test_diff_reports_addition_removal(self):
        orig=write_pkl(sample())
        changed=copy.deepcopy(sample())
        changed[0]["Slots"][0]["Shiny"]="Never"
        update=write_pkl(changed)
        d=diff(orig,update)
        self.assertEqual((d["slots_added"],d["slots_removed"]),(1,1))
        self.assertEqual(d["added"][0]["Shiny"],"Never")
        self.assertEqual(d["removed"][0]["Shiny"],"Random")
        self.assertFalse(d["byte_identical"])

    def test_file_export_edit_import_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            raw=write_pkl(sample())
            origin=root/"original.pkl";origin.write_bytes(raw)
            js=root/"slots.json";rep=root/"repacked.pkl"
            subprocess.run([sys.executable,str(CODEC),"export",str(origin),
                            "--out",str(js)],check=True,capture_output=True)
            subprocess.run([sys.executable,str(CODEC),"import",str(js),
                            "--source-pkl",str(origin),
                            "--out",str(rep)],check=True,capture_output=True)
            self.assertEqual(raw,rep.read_bytes())
            self.assertEqual(hashlib.sha256(raw).digest(),
                             hashlib.sha256(rep.read_bytes()).digest())

    def test_patch_new_file_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/"baseline.pkl"
            base.write_bytes(write_pkl(sample()))
            patched=Path(tmp)/"patched.pkl"
            cmd=[sys.executable,str(CODEC),"patch",str(base),"--out",str(patched),
                 "--location","12","--index","0","--shiny","Never"]
            subprocess.run(cmd,check=True,capture_output=True)
            self.assertEqual(read_pkl(base.read_bytes())[0]["Slots"][0]["Shiny"],"Random")
            self.assertEqual(read_pkl(patched.read_bytes())[0]["Slots"][0]["Shiny"],"Never")
            again=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0)
            self.assertIn("File exists",again.stderr)

    def test_beyond_binlinker16_guard(self):
        with self.assertRaises(PKLFormatError):
            write_pkl([{"Location":1,"Slots":[make_slot() for _ in range(8192)]}])


if __name__=="__main__":
    unittest.main()
