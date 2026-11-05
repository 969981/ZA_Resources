"""Synthetic register-flow tests; all sources are made-up opcode tuples."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "za_lua_register_flow", ROOT / "scripts/Trace-ZA-Lua-RegisterFlow.py")
flow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(flow)
TOKEN = b"S0123456789ABCDEF"
PROTO = {"id": 9, "parent": 0, "code_offset": 0x100}

def i(name, a=0, b=0, c=0, k=0, bx=0, ax=0):
    return (name, a, b, c, k, bx, ax)

class TestStraightLineFlow(unittest.TestCase):
    def trace(self, code, constants=(TOKEN,), window=16):
        return flow.trace_proto(code, constants, {TOKEN}, "main", PROTO, window)

    def test_adjacent_field_call_is_preserved(self):
        calls, keys = self.trace([i("GETFIELD", 3, 2, 0), i("CALL", 3), i("RETURN0")])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][5], 0)
        self.assertEqual(calls[0][9], 1)
        self.assertEqual(keys, [])

    def test_move_and_unrelated_constant_allow_nonadjacent_call(self):
        calls, _ = self.trace([i("GETTABUP", 3, 0, 0), i("MOVE", 5, 3),
                               i("LOADK", 7, bx=1), i("TAILCALL", 5)], (TOKEN, b"unrelated"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][12], 5)
        self.assertEqual(calls[0][13], 1)

    def test_move_overwrite_and_unknown_barrier_reject(self):
        calls, _ = self.trace([i("GETFIELD", 3, 2, 0), i("MOVE", 3, 9), i("CALL", 3)])
        self.assertFalse(calls)
        calls, _ = self.trace([i("GETFIELD", 3, 2, 0), i("TEST", 2), i("CALL", 3)])
        self.assertFalse(calls)
        calls, _ = self.trace([i("GETFIELD", 3, 2, 0), i("JMP"), i("CALL", 3)])
        self.assertFalse(calls)

    def test_loadk_gettable_and_method_call(self):
        calls, keyed = self.trace([i("LOADK", 7, bx=0), i("GETTABLE", 3, 2, 7),
                                   i("CALL", 3)])
        self.assertEqual(len(keyed), 1)
        self.assertEqual(keyed[0][7], "GETTABLE")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][4], 0)
        self.assertEqual(calls[0][7], "GETTABLE")

    def test_register_key_write_does_not_create_call(self):
        calls, keyed = self.trace([i("LOADK", 7, bx=0), i("SETTABLE", 3, 7, 2),
                                   i("CALL", 3)])
        self.assertEqual(calls, [])
        self.assertEqual(len(keyed), 1)
        self.assertEqual(keyed[0][7], "SETTABLE")

    def test_self_register_key_and_second_register_clobber(self):
        calls, keys = self.trace([i("LOADK", 8, bx=0), i("SELF", 3, 2, 8, k=0),
                                  i("CALL", 3)])
        self.assertEqual(len(keys), 1)
        self.assertEqual(len(calls), 1)
        calls, keys = self.trace([i("GETFIELD", 4, 2, 0), i("SELF", 3, 2, 0, k=1),
                                  i("CALL", 4)])
        self.assertFalse(calls)

    def test_loadkx_extraarg(self):
        calls, keyed = self.trace([i("LOADKX", 7), i("EXTRAARG", ax=0),
                                   i("GETTABLE", 3, 2, 7), i("CALL", 3)])
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(keyed), 1)

    def test_window_limit(self):
        calls, _ = self.trace([i("GETFIELD", 3, 2, 0), i("MOVE", 6, 3),
                               i("MOVE", 5, 6), i("CALL", 5)], window=2)
        self.assertEqual(calls, [])

    def test_incoming_jump_target_cuts_register_proof(self):
        jump_ax = ((1 << 25) - 1) // 2 + 2
        calls, _ = self.trace([i("JMP", ax=jump_ax), i("GETFIELD", 3, 2, 0),
                               i("MOVE", 5, 3), i("CALL", 5)])
        self.assertEqual(calls, [])

    def test_not_target_constant(self):
        calls, keyed = self.trace([i("LOADK", 7, bx=1), i("GETTABLE", 3, 2, 7),
                                   i("CALL", 3)], (TOKEN, b"not a target"))
        self.assertEqual(calls, [])
        self.assertEqual(keyed, [])

if __name__ == "__main__":
    unittest.main()
