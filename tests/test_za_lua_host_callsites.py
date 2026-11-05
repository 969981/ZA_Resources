"""Synthetic checks for high-signal main ELF xref context and pointer-site scanner."""
import importlib.util
import struct
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(tag,path):
    spec=importlib.util.spec_from_file_location(tag,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

tracer=load("za_host_callsites",ROOT/"scripts/Trace-ZA-Lua-Host-Callsites.py")
probe=tracer.load_probe()
fixture=load("za_elf_fixture",ROOT/"tests/test_za_lua_host_elf.py")


class HostCallsTests(unittest.TestCase):
    def test_branch_target_hints_not_function_names(self):
        self.assertEqual(tracer.instruction_hint(0x94000003,0x1000,probe),
                         "BL_IMMEDIATE 0x100C")
        self.assertEqual(tracer.instruction_hint(0x14000002,0x2000,probe),
                         "B_IMMEDIATE 0x2008")
        self.assertEqual(tracer.instruction_hint(0xD65F03C0,0x1000,probe),
                         "RET X30")
        self.assertEqual(tracer.instruction_hint(0xD63F0060,0x1000,probe),
                         "BLR_REGISTER X3")

    def test_bounded_xref_context_uses_real_section_va(self):
        elf=probe.ELF64(fixture.fixture_elf())
        ctx=tracer.xref_context(elf,0x1000,"main_dynamic.blua",probe,3)
        self.assertEqual(ctx[0][3],"0x1000")
        self.assertEqual(ctx[0][4],"0x100")
        self.assertIn("ADRP X3",ctx[0][7])
        self.assertEqual(ctx[1][7],"ADD X3,X3,#0")
        self.assertEqual(ctx[0][8],
                         "NATIVE_BOUNDED_INSTRUCTION_CONTEXT_NOT_EXECUTION_PROOF")

    def test_pointer_literals_not_deduced_calls(self):
        payload=b"lua_helper\x00"+struct.pack("<Q",0x3000)+b"\x00"
        elf=probe.ELF64(fixture.fixture_elf(payload))
        entries,types=tracer.pointer_and_relocations(elf,{"lua_helper":0x3000})
        self.assertEqual(types,{})
        self.assertEqual(len(entries),1)
        self.assertEqual(entries[0][4],"ELF_QWORD_RAW_LITERAL")
        self.assertEqual(entries[0][-1],"NATIVE_ELF_POINTER_BYTES_ONLY")

    def test_empty_pointer_and_relocation_never_crash(self):
        elf=probe.ELF64(fixture.fixture_elf())
        pointers,rela=tracer.pointer_and_relocations(elf,{"_ENV":0x31F263F})
        self.assertEqual(pointers,[])
        self.assertEqual(rela,{})

    def test_xref_not_in_code_rejected(self):
        elf=probe.ELF64(fixture.fixture_elf())
        with self.assertRaisesRegex(ValueError,"executable mapping"):
            tracer.xref_context(elf,0x3000,"lua_helper",probe,2)


if __name__=="__main__":
    unittest.main()
