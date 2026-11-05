"""Synthetic-only receiver-register provenance tests (no native game data)."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/Trace-ZA-Lua-ReceiverOrigin.py"
SPEC = importlib.util.spec_from_file_location("za_receiver_test", SCRIPT)
assert SPEC and SPEC.loader
TRACE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRACE)


def inst(op, a=0, b=0, c=0, k=0, bx=0, ax=0):
    return (op, a, b, c, k, bx, ax)


class ReceiverOriginTest(unittest.TestCase):
    def test_move_from_upvalue(self):
        code = [inst("GETUPVAL", 1, 0), inst("MOVE", 2, 1),
                inst("GETFIELD", 3, 2, 0)]
        self.assertEqual(TRACE.receiver_origin(code, [b"F" + b"A" * 16], 2),
                         (2, "UPVALUE_PATH", "UPVALUE[0]", 0))

    def test_nested_field_source_is_lexical_only(self):
        code = [inst("GETTABUP", 1, 0, 0),
                inst("GETFIELD", 2, 1, 1),
                inst("GETFIELD", 3, 2, 1)]
        reg, kind, path, pc = TRACE.receiver_origin(code, [b"_G", b"foo"], 2)
        self.assertEqual((reg, kind, path, pc),
                         (2, "UPVALUE_PATH", "UPVALUE[0]._G.foo", 1))

    def test_local_new_table_source(self):
        code = [inst("NEWTABLE", 2), inst("EXTRAARG"),
                inst("GETFIELD", 1, 2, 0)]
        self.assertEqual(TRACE.receiver_origin(code, [b"bar"], 2),
                         (2, "LOCAL_TABLE_PATH", "NEW_TABLE@0", 0))

    def test_self_passes_receiver_as_a_plus_one(self):
        code = [inst("GETUPVAL", 2, 1), inst("SELF", 4, 2, 0, 1),
                inst("GETFIELD", 6, 5, 0)]
        reg, kind, path, pc = TRACE.receiver_origin(code, [b"foo"], 2)
        self.assertEqual((reg, kind, path), (5, "UPVALUE_PATH", "UPVALUE[1]"))

    def test_unknown_side_effect_clears(self):
        code = [inst("GETUPVAL", 2, 1), inst("CALL", 0, 1, 1),
                inst("GETFIELD", 3, 2, 0)]
        self.assertEqual(TRACE.receiver_origin(code, [b"foo"], 2)[1],
                         "UNRESOLVED_REGISTER")

    def test_branch_target_clears(self):
        code = [inst("GETUPVAL", 2, 1), inst("MOVE", 3, 2),
                inst("MOVE", 4, 3), inst("GETFIELD", 5, 4, 0)]
        self.assertEqual(TRACE.receiver_origin(code, [b"x"], 3,
                                                leaders={0, 2})[1],
                         "UNRESOLVED_REGISTER")

    def test_direct_gettabup_receiver_is_upvalue_not_class(self):
        code = [inst("GETTABUP", 2, 3, 0)]
        self.assertEqual(TRACE.receiver_origin(code, [b"x"], 0),
                         (3, "UPVALUE_DIRECT", "UPVALUE[3]", 0))

    def test_unbounded_window_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid window"):
            TRACE.receiver_origin([inst("GETFIELD", 1, 2)], [], 0, 257)


if __name__ == "__main__":
    unittest.main()
