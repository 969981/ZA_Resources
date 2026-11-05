"""Synthetic checks for ZA Lua 5.4 native-reference evidence; no ROM inputs."""
from __future__ import annotations
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def import_script(filename, name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/filename)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

native=import_script("Analyze-ZA-Lua-Native.py","za_native")
locator=import_script("Locate-ZA-Lua-Packs.py","za_locator")

def vint(n):
    values=[n & 127]
    n >>= 7
    while n:
        values.append(n & 127)
        n >>= 7
    values.reverse()
    values[-1] |= 128
    return bytes(values)

def make_chunk(token):
    core=native.core_module()
    header=b"\x1bLua\x54\x00\x19\x93\r\n\x1a\n"+bytes([4,8,8])
    header+=(0x5678).to_bytes(8,"little")+struct.pack("<d",370.5)+b"\x00"
    code=[core.OPNAMES.index("LOADK"),core.OPNAMES.index("RETURN0")]
    proto=vint(0)+vint(0)+vint(0)+bytes([0,0,2])
    proto+=vint(len(code))+b"".join(struct.pack("<I",w) for w in code)
    proto+=vint(1)+b"\x04"+vint(len(token)+1)+token
    proto+=vint(0)*6
    return header+proto

class ZANativeTests(unittest.TestCase):
    def test_true_opcode_constant_reference(self):
        core=native.core_module()
        token=b"S007A70B0AFF2E6D0"
        lua,refs,consts,methods,statics,drops=native.analyze(make_chunk(token),"event_ik",{token},core)
        self.assertEqual(len(lua.protos),1)
        self.assertEqual(len(refs),1)
        self.assertEqual(refs[0][1],"S007A70B0AFF2E6D0")
        self.assertEqual(refs[0][6],"LOADK")
        self.assertEqual(refs[0][-1],"NATIVE_LUA54_OPCODE_CONSTANT_REFERENCE")
        self.assertEqual(len(consts),1)
        self.assertFalse(methods)
        self.assertFalse(statics)

    def test_constant_does_not_imply_op_reference(self):
        core=native.core_module()
        token=b"S007A70B0AFF2E6D0"
        _,refs,consts,*_=native.analyze(make_chunk(token),"event_ik",{b"S1111111111111111"},core)
        self.assertEqual(refs,[])
        self.assertEqual(consts,[])

    def test_bad_bytecode_refused(self):
        core=native.core_module()
        with self.assertRaises(core.FormatError):
            native.analyze(b"not a game script","main",{b"S007A70B0AFF2E6D0"},core)

    def test_target_names_and_pinning(self):
        self.assertEqual(set(locator.TARGETS),{"dll_util","event_ik","main","main_dynamic"})
        self.assertIn("event_ik/event_ik.blua",locator.TARGETS["event_ik"])
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                locator.build(Path(tmp))

if __name__=="__main__":
    unittest.main()
