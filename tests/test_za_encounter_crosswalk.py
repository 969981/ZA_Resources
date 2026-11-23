"""Synthetic tests for ZA encounter crosswalk; no proprietary resource bytes."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import struct
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "encounters"))
from za_encounter_crosswalk import (
    scene_sources, manual_coordinates, species_map, pkl, matches,
    template_classes, audit, resolve_scene_location,
)

class CrosswalkTests(unittest.TestCase):
    def test_local_scene_location_is_unknown(self):
        ids, distance, authority = resolve_scene_location(
            "t1",
            "world/ik_scene/field/area/t1_i007a/sub_scene/t1_i007a_gimmick/x.trscn",
            [2.35, 0.01, 4.4],
            [((0, 0, 0), [202])])
        self.assertEqual(ids, [])
        self.assertEqual(distance, -1.0)
        self.assertIn("UNKNOWN", authority)
        valid = resolve_scene_location(
            "t1", "world/ik_scene/field/area/t1/a.trscn",
            [0, 0, 0], [((0, 0, 0), [12])])
        self.assertEqual(valid[0], [12])

    def test_scene_and_manual(self):
        text='''ScenePathsT1 = // comment
        ["world/ik_scene/a.trscn"];
        ScenePathsT2 = ["world/ik_scene/b.trscn"];
        ScenePathsT3 = ["world/ik_scene/c.trscn"];'''
        self.assertEqual(len(scene_sources(text)), 3)
        rows=manual_coordinates('private const string Import = """\n12, 12, 1, 2, 3\n13, 13, 1, 2, 3\n""";')
        self.assertEqual(rows, [((1., 2., 3.), [12, 13])])

    def test_species_converter(self):
        source="Table9InternalToNational => [" + ",".join(["65"]+["0"]*109) + "];"
        convert=species_map(source)
        self.assertEqual(convert(917), 982)
        self.assertEqual(convert(900), 900)

    def test_pkl_coverage(self):
        data=(b"za" + struct.pack("<HHH",1,8,20) +
              struct.pack("<HH",234,0) +
              struct.pack("<HBBBBBB",25,0,255,20,25,1,1))
        with TemporaryDirectory() as temp:
            f=Path(temp)/"encounter_za.pkl";f.write_bytes(data)
            records=pkl(f)
            self.assertEqual(matches(records,234,(25,0,255,20,25,1,1)), "covered")
            self.assertEqual(matches(records,234,(25,0,255,19,22,1,1)), "overlap")
            self.assertEqual(matches(records,273,(25,0,255,20,25,1,1)), "missing")

    def test_full_cover_beats_earlier_overlap(self):
        # PKHeX may store overlapping intervals: a 5-8 entry preceding
        # a 3-5 entry must still fully cover a source interval of 3-5.
        records={12:[(16,0,255,5,8,0,0),(16,0,255,3,5,0,0)]}
        self.assertEqual(matches(records,12,(16,0,255,3,5,0,0)), "covered")

    def test_template_ids(self):
        source='''Gifts = [ new(1,0,5,0) { Location = 5 }, // Gift (sub_gift)
        ]; Static = [ new(2,0,5,0) {}, // Boss (sub_boss)
        ]; Trades = [ new(names,0,2,0,5) {}, // Trade (sub_trade)
        ];'''
        self.assertEqual(template_classes(source)["sub_boss"], {"static"})

    def test_join_and_not_runtime_proof(self):
        enc=[dict(db=0,row=0,id="slot1",dev=25,lo=20,hi=25,sex=-1,form=0,
            rare=0x1FFFFFFF,nature=-1,alpha=0,boost=0,activation=0),
            dict(db=0,row=1,id="fixed",dev=150,lo=70,hi=70,sex=-1,form=0,
            rare=0x1FFFFFFF,nature=-1,alpha=0,boost=0,activation=0)]
        sp=[dict(db=0,row=0,id="sp1",
            appearances=[dict(name="obj1",max=1,min=1,tags=[])],
            targets=[dict(id="slot1",weight=100,max=1,add=0,time=2,weather=0,
                          conditions=0,ui_conditions=0)],
            conditions=0,ui_conditions=0,cooldown=0)]
        scenes=[dict(name="obj1",scene="t2",map="t2",shape="pokemon_spawner_box_object",
                     x=1,y=2,z=3,locations="234",nearest_distance=0)]
        with TemporaryDirectory() as tmp:
            result=audit(enc,sp,[],[],scenes,{234:[(25,0,255,20,25,0,1)]},{},
                         lambda dev:dev,{"fixed":{"static"}},Path(tmp),[])
            self.assertEqual(result["counts"]["encounter_edges"],1)
            self.assertEqual(result["counts"]["encounters_unreferenced"],1)
            self.assertEqual(result["counts"]["encounters_official_pkl_covered"],1)
            self.assertEqual(result["categories"]["official_static"],1)
            self.assertEqual(result["conditional_candidates"]["target_condition_candidates"],1)
            self.assertEqual(result["status"],"STATIC_CONFIGURATION_NOT_RUNTIME_PROOF")
            self.assertTrue((Path(tmp)/"za_spawner_encounter_edges.csv").exists())

if __name__=="__main__":
    unittest.main()
