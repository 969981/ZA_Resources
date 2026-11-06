#!/usr/bin/env python3
"""Synthetic FlatBuffers crosswalk tests; never uses game data."""
import importlib.util
import struct
import unittest
from pathlib import Path

p=Path(__file__).resolve().parents[1]/"scripts/Trace-ZA-EX-Spawner.py"
sp=importlib.util.spec_from_file_location("za_ex_spawner",p)
mod=importlib.util.module_from_spec(sp)
sp.loader.exec_module(mod)

def fixture():
    b=bytearray(256)
    def write(o,fmt,*x):struct.pack_into(fmt,b,o,*x)
    write(0,"<I",12)
    write(6,"<HHH",6,8,4)             # root vt
    write(12,"<i",6)
    write(16,"<I",4)                   # root Table->vec20
    write(20,"<I",1)
    write(24,"<I",16)                  # -> DB at40
    write(28,"<HHH",6,8,4)             # db vt
    write(40,"<i",12)
    write(44,"<I",20)                  # -> DB.Table vec64
    write(64,"<I",1)
    write(68,"<I",20)                  # -> spawner table88
    write(72,"<HHHHHHHH",16,12,4,0,0,0,0,8)
    write(88,"<i",16)
    write(92,"<I",64)                  # spawner.Id string at 156
    write(96,"<I",16)                  # spawner.EncountDataInfoList at112
    write(112,"<I",1)
    write(116,"<I",12)                 # -> enc table128
    write(120,"<HHH",6,8,4)           # enc vt
    write(128,"<i",8)
    write(132,"<I",48)                 # enc Id string at180
    spawner=b"id_sub119_01";enc=b"sub_119_diancie"
    write(156,"<I",len(spawner));b[160:160+len(spawner)]=spawner
    write(180,"<I",len(enc));b[184:184+len(enc)]=enc
    return bytes(b)

class CrosswalkTests(unittest.TestCase):
    def test_fixture(self):
        result=mod.extract(fixture())
        self.assertEqual(result["database_count"],1)
        self.assertEqual(result["spawner_count"],1)
        self.assertEqual(result["verified_exact_joins"]["diancie"][0]["spawner_id"],"id_sub119_01")
        self.assertFalse(result["verified_exact_joins"]["mewtwo"])
    def test_truncation(self):
        with self.assertRaises((ValueError,struct.error)):
            mod.extract(fixture()[:36])

if __name__=="__main__":
    unittest.main()
