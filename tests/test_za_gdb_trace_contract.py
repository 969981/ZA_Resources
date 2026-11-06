"""Static contract for GDB-only code; no debugger or Nintendo ROM needed in CI."""
import ast
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/gdb/za_ex_rare_trace.py"

class ReadOnlyGDBContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code=SCRIPT.read_text(encoding="utf-8")
        cls.tree=ast.parse(cls.code)
    def test_syntax(self):
        compile(self.code,str(SCRIPT),"exec")
    def test_read_only_runtime(self):
        self.assertIn("read_memory(",self.code)
        self.assertNotIn("write_memory(",self.code)
        self.assertNotIn("gdb.execute(",self.code)
        self.assertIn("return False",self.code)
        self.assertIn("self.enabled=False",self.code)
    def test_version_fingerprints_and_labels(self):
        for literal in ("0xE5D20C","0x657168","0x656298","0xE3EB64",
                        '"EX1"','"EX2"','"CONTROL"',"Mismatch VA","elf_sha256"):
            self.assertIn(literal,self.code)
    def test_no_unattended_bypass(self):
        self.assertIn("for va,expected in PROBES.items()",self.code)
        self.assertIn("STATE.breakpoints.append(TracePoint(",self.code)
        self.assertLess(self.code.index("for va,expected in PROBES.items()"),
                        self.code.index("STATE.breakpoints.append(TracePoint("))

if __name__=="__main__":unittest.main()
