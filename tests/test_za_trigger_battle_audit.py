"""Synthetic regression tests for Z-A trigger → battle → spawner joins."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "encounters"))
from za_trigger_battle_audit import join_links, read_trigger


class TriggerJoinTest(unittest.TestCase):
    def test_exact_ids_no_prefix_matching(self):
        triggers=[
            dict(source="trigger_sub_0119.bin",trigger_index=5,battle_id="btl_sub_119"),
            dict(source="trigger_sub_0120.bin",trigger_index=3,battle_id="btl_sub_120"),
        ]
        battles=[
            dict(index=42,battle_id="btl_sub_119",actor_id="id_sub119_01",
                 event_id="bae_Ev_sub_119_010",context_id="wild_common_3"),
            dict(index=43,battle_id="btl_sub_120",actor_id="id_sub120_01",
                 event_id="bae_Ev_sub_120_010",context_id="wild_common_3"),
        ]
        edges=[
            dict(spawner_id="id_sub119_01",encounter_id="sub_119_diancie"),
            dict(spawner_id="id_sub119_01",encounter_id="sub_119_melecie_01"),
            dict(spawner_id="id_sub120_01",encounter_id="sub_120_mewtwo"),
        ]
        joined=join_links(triggers,battles,edges)
        self.assertEqual(len(joined),2)
        self.assertEqual(joined[0]["exact_actor_id"],"id_sub119_01")
        self.assertEqual(joined[1]["exact_actor_id"],"id_sub120_01")
        self.assertIn("sub_119_diancie",joined[0]["encounter_ids"])
        self.assertEqual(joined[0]["evidence"],"STATIC_EXACT_BATTLE_ACTOR_ENCOUNTER")

    def test_missing_battle_kept_unknown(self):
        raw=[dict(source="unmatched.bin",battle_id="btl_missing",trigger_index=0)]
        matched=join_links(raw,[dict(battle_id="btl_miss",actor_id="id_x",event_id="")],[])
        self.assertEqual(len(matched),1)
        self.assertEqual(matched[0]["evidence"],"UNKNOWN_BATTLE_ID")
        self.assertEqual(matched[0]["exact_actor_id"],"")

    def test_non_flatbuffer_is_not_silently_parsed(self):
        with self.assertRaises((Exception,)):
            read_trigger(b"invalid", "bad.bin")


if __name__=="__main__":
    unittest.main()
