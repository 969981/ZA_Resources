"""Synthetic regression for orphan-scene/spawner triage; source data not included."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "encounters"))
from za_gap_triage import classify, scene_category, spawner_category, candidate_battle_id


class GapTriageTest(unittest.TestCase):
    def test_family_classification_is_not_spawn_proof(self):
        self.assertEqual(scene_category("spn_a0601_w01_v02_001"), "wild_zone_scene_object")
        self.assertEqual(scene_category("spn_boss_0359_01_object"), "boss_scene_object")
        self.assertEqual(scene_category("test_pokemon_spawner_blue_object_01"), "test_object")
        self.assertEqual(spawner_category("id_zdm_random_t00_r01_016"),
                         "dimension_pool_not_selected")
        self.assertEqual(spawner_category("btl_spn_boss_0359_01"),
                         "battle_named_spawner")

    def test_candidate_remains_candidate(self):
        self.assertEqual(candidate_battle_id("spn_boss_0359_01_object"),
                         "btl_spn_boss_0359_01")
        self.assertEqual(candidate_battle_id("spn_a0601_w01_v01_001"), "")
        scene=[dict(name="spn_boss_0359_01_object",scene="t1",x="1",y="2",z="3",
                    locations="",nearest_distance="")]
        sp=[dict(id="btl_spn_boss_0359_01",object_names="btl_spn_boss_0359_01",
                 scene_placements="0",hyperspace_refs="0",transform_name_matches="0",
                 spawner_conditions="1",maxcount_enabled="1")]
        edges=[dict(spawner_id=sp[0]["id"],encounter_id="ect_boss_0359_01",
                    official_template="static")]
        scene_gaps,sp_gaps=classify(scene,sp,edges,raw=None)
        self.assertEqual(len(scene_gaps),1)
        self.assertEqual(scene_gaps[0]["candidate_spawner_id"],sp[0]["id"])
        self.assertEqual(scene_gaps[0]["evidence"],"CANDIDATE")
        self.assertEqual(len(sp_gaps),1)
        self.assertEqual(sp_gaps[0]["official_template"],"static")
        self.assertEqual(sp_gaps[0]["evidence"],"CONFIRMED_STATIC_PKHEX_TEMPLATE")
        self.assertIn("NOT disproven",sp_gaps[0]["explanation"])

    def test_battle_actor_exact_join(self):
        sp=[dict(id="id_sub119_01",object_names="id_sub119_01",
                 scene_placements="0",hyperspace_refs="0",transform_name_matches="0",
                 spawner_conditions="1",maxcount_enabled="1")]
        battles=[dict(index=1,battle_id="btl_sub_119",actor_id="id_sub119_01",
                      event_id="bae_Ev_sub_119_010",context_id="wild_common_3")]
        _,gaps=classify([],sp,[],battles=battles)
        self.assertEqual(gaps[0]["direct_battle_table_refs"],1)
        self.assertEqual(gaps[0]["direct_battle_ids"],"btl_sub_119")
        self.assertEqual(gaps[0]["direct_battle_event_ids"],"bae_Ev_sub_119_010")
        self.assertEqual(gaps[0]["evidence"],"CONFIRMED_STATIC_BATTLE_TABLE_LINK")

    def test_raw_source_path_preserved(self):
        sp=[dict(id="id_sub119_01",object_names="sub_119_placement",
                 scene_placements="0",hyperspace_refs="0",transform_name_matches="1",
                 spawner_conditions="1",maxcount_enabled="1")]
        raw={"id_sub119_01":[dict(object_name="sub_119_placement",
                                 create_scene_path="world/ik_scene/a.trscn",
                                 battle_area_id="btl_sub_119",dungeon_name="",
                                 tags="")]}
        a,b=classify([],sp,[],raw=raw)
        self.assertEqual(a,[])
        self.assertEqual(b[0]["raw_create_scene_paths"],"world/ik_scene/a.trscn")
        self.assertEqual(b[0]["raw_battle_area_ids"],"btl_sub_119")
        self.assertEqual(b[0]["family"],"quest_named_spawner")


if __name__=="__main__":
    unittest.main()
