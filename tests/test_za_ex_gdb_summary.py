"""Synthetic, not real GDB, tests of EX1/EX2 evidence summarizer."""
import importlib.util, json, tempfile, unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/Analyze-ZA-EX-Rare-GDB.py"
s=importlib.util.spec_from_file_location("za_ex_gdb_analyzer", SCRIPT)
m=importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def emit(path,label,species=719,with_never=True):
    rows=[{"label":label,"event":"trace_started"},
          {"label":label,"event":"rare_raw_load",
           "values":{"descriptor_plus68_u32":"0x1FFFFFFF" if with_never else "0x3FFFFFFF"}},
          {"label":label,"event":"native_mode_dispatch",
           "values":{"state_plus20_u64":"0x1FFFFFFFF" if with_never else "0x3FFFFFFFF"}},
          {"label":label,"event":"field_init_pid_setter_call","regs":{"x0":"0x400000"}},
          {"label":label,"event":"field_init_species_setter_call",
           "values":{"w1_species_candidate":f"0x{species:X}","pokemon_object_pointer":"0x400000"}},
          {"label":label,"event":"native_never_antishiny_call"},
          {"label":label,"event":"trace_stopped"}]
    path.write_text("\n".join(json.dumps(x) for x in rows)+"\n",encoding="utf-8")

class GDBAnalyzerTests(unittest.TestCase):
    def test_ex1_ex2_synthetic(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/"ex1.jsonl",Path(d)/"ex2.jsonl"
            emit(a,"EX1",719);emit(b,"EX2",150)
            out=m.run(a,b)
            self.assertFalse(out["confirmed_original_FlatBuffers_to_descriptor_assignment"])
            for e in out["runtime_sessions"]:
                self.assertTrue(e["pid_and_expected_species_on_same_object_seen"])
                self.assertTrue(e["original_raw_never_observed"])
                self.assertTrue(e["native_never_mode_observed"])
                self.assertEqual(e["native_never_call_hits"],1)
    def test_no_never_is_not_proof(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"ex1.jsonl";emit(a,"EX1",719,False)
            x=m.summarize(a,"EX1")
            self.assertFalse(x["original_raw_never_observed"])
            self.assertFalse(x["native_never_mode_observed"])
    def test_missing_session_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                m.summarize(Path(d)/"no.jsonl","EX1")
    def test_wrong_manual_label_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"wrong.jsonl";emit(a,"EX1",719)
            with self.assertRaisesRegex(ValueError,"expected label EX2"):
                m.summarize(a,"EX2")

if __name__=="__main__":unittest.main()
