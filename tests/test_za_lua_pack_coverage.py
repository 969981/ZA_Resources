"""Synthetic validation of ZA complete Trinity Lua pack/unknown-constant audit."""
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("za_lua_scope",
                                            ROOT/"scripts/Audit-ZA-Lua-PackCoverage.py")
scope=importlib.util.module_from_spec(spec)
spec.loader.exec_module(scope)

class ScopeTests(unittest.TestCase):
    def test_blua_only_with_complete_pack_suffix(self):
        packs=[
            {"pack_index":"12145","pack_name":"arc/scriptluabinreleasedll_util.blua.trpak"},
            {"pack_index":"12149","pack_name":"arc/unrelatedluaasset.trpak"},
            {"pack_index":"10","pack_name":"arc/main.blua.tmp.trpak"},
            {"pack_index":"12146","pack_name":"arc/scriptluabinreleaseevent_ik.blua.trpak"},
        ]
        unresolved=[
            {"kind":"s","hash":"0x1111111111111111","original_line":"23"},
            {"kind":"f","hash":"0x2222222222222222","original_line":"24"}
        ]
        constants=[{"hash_token":"F2222222222222222"}]
        found,target,present,missing=scope.coverage(packs,unresolved,constants)
        self.assertEqual(len(found),2)
        self.assertEqual(missing,["S1111111111111111"])
        self.assertEqual(len(target),2)

    def test_out_of_corpus_native_token_is_rejected(self):
        with self.assertRaises(ValueError):
            scope.coverage([],
                [{"kind":"s","hash":"0x1111111111111111"}],
                [{"hash_token":"SFFFFFFFFFFFFFFFF"}])

if __name__=="__main__":
    unittest.main()
