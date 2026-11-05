"""Synthetic native + Haxe evidence crosswalk tests (no game source files)."""
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("za_crosswalk",ROOT/"scripts/Crosswalk-ZA-Lua-Native.py")
core=importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

def tsv(path,fields,rows):
    with path.open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,delimiter="\t",lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

class TestCrosswalk(unittest.TestCase):
    def test_hash_join_does_not_confirm_original_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            unknown=[]
            for k,num in [("s",116),("f",43),("e",3)]:
                for i in range(num):
                    unknown.append({"kind":k,"hash":f"0x{i+1:016X}","original_line":str(i+1)})
            tsv(d/"unknown.tsv",["kind","hash","original_line"],unknown)
            sha="c7bc243ac4d28356dff9f06b6723330ea92247d5"
            tsv(d/"haxe.tsv",["kind","hash","role","path","line","commit"],[
                {"kind":"s","hash":"0x0000000000000001","role":"CALL","path":"source/example.hx","line":"7","commit":sha}])
            tsv(d/"opcodes.tsv",["hash_token","source","proto_id","pc","opcode","evidence"],[
                {"hash_token":"S0000000000000001","source":"event_ik","proto_id":"9",
                 "pc":"12","opcode":"GETFIELD","evidence":"NATIVE_LUA54_OPCODE_CONSTANT_REFERENCE"}])
            tsv(d/"static.tsv",["s_hash","class_hash","evidence"],[
                {"s_hash":"S0000000000000001","class_hash":"C1234567890123456",
                 "evidence":"NATIVE_ROOT_CLASS_S_CLOSURE_ASSIGNMENT"}])
            (d/"native.json").write_text(json.dumps({"version":"v2.0.2","native_files_parsed":4}))
            out=d/"out"
            info=core.run(d/"unknown.tsv",d/"haxe.tsv",d/"opcodes.tsv",d/"static.tsv",d/"native.json",out)
            self.assertEqual(info["unique_s_with_native_opcode_and_haxe"],1)
            self.assertEqual(info["native_class_s_static_edges"],1)
            self.assertEqual(info["native_symbol_names_confirmed"],0)
            with (out/"native-haxe-crosswalk.tsv").open() as f:
                rows=list(csv.DictReader(f,delimiter="\t"))
            self.assertEqual(len(rows),162)
            matches=[x for x in rows if x["kind"]=="s" and x["hash"]=="0x0000000000000001"]
            self.assertEqual(len(matches),1)
            self.assertEqual(matches[0]["crosswalk_grade"],"NATIVE_OPCODE_AND_HAXE_REFERENCES_NOT_NAME_CONFIRMED")
            self.assertEqual(matches[0]["original_name_confirmed"],"NO")

if __name__=="__main__":
    unittest.main()
