"""Synthetic native Lua 5.4 adjacent opcode call-edge tests (no ROM files)."""
from __future__ import annotations

import importlib.util
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def imp(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

direct = imp("za_native_direct", "Analyze-ZA-Lua-DirectCalls.py")
core = direct.load_core()

def vint(v):
    seq = [v & 127]
    v >>= 7
    while v:
        seq.append(v & 127)
        v >>= 7
    seq.reverse()
    seq[-1] |= 128
    return bytes(seq)

def make_bytecode(ops, token=b"S007A70B0AFF2E6D0"):
    header = b"\x1bLua\x54\x00\x19\x93\r\n\x1a\n" + bytes([4, 8, 8])
    header += (0x5678).to_bytes(8, "little") + struct.pack("<d", 370.5) + b"\x00"
    proto = vint(0) + vint(0) + vint(0) + bytes([0, 0, 8])
    proto += vint(len(ops)) + b"".join(struct.pack("<I", w) for w in ops)
    proto += vint(1) + b"\x04" + vint(len(token) + 1) + token
    proto += vint(0) * 6
    return header + proto

def opcode(name, a=0, b=0, c=0, k=0):
    return core.OPNAMES.index(name) | (a << 7) | (k << 15) | (b << 16) | (c << 24)

class ZALuaDirectCallTest(unittest.TestCase):
    TARGET = {b"S007A70B0AFF2E6D0"}

    def test_adjacent_getfield_call_identifies_proven_native_opcode_pair(self):
        raw = make_bytecode([opcode("GETFIELD", a=3, b=2, c=0),
                             opcode("CALL", a=3),
                             opcode("RETURN0")])
        protos, found = direct.edges(raw, "main", self.TARGET, core)
        self.assertEqual(protos, 1)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][1], "S007A70B0AFF2E6D0")
        self.assertEqual(found[0][6], "GETFIELD")
        self.assertEqual(found[0][10], "CALL")
        self.assertEqual(found[0][-1], direct.GRADE)

    def test_wrong_register_is_not_a_direct_call_edge(self):
        raw = make_bytecode([opcode("GETTABUP", a=3, b=0, c=0),
                             opcode("CALL", a=4),
                             opcode("RETURN0")])
        self.assertEqual(direct.edges(raw, "event_ik", self.TARGET, core)[1], [])

    def test_register_field_get_self_must_use_constant_k(self):
        raw_no = make_bytecode([opcode("SELF", a=3, b=2, c=0, k=0),
                                opcode("CALL", a=3), opcode("RETURN0")])
        raw_yes = make_bytecode([opcode("SELF", a=3, b=2, c=0, k=1),
                                 opcode("TAILCALL", a=3), opcode("RETURN0")])
        self.assertEqual(direct.edges(raw_no, "main", self.TARGET, core)[1], [])
        self.assertEqual(len(direct.edges(raw_yes, "main", self.TARGET, core)[1]), 1)

    def test_constant_does_not_imply_direct_call(self):
        raw = make_bytecode([opcode("LOADK", a=3, b=0, c=0),
                             opcode("CALL", a=3), opcode("RETURN0")])
        self.assertEqual(direct.edges(raw, "main", self.TARGET, core)[1], [])

if __name__ == "__main__":
    unittest.main()
