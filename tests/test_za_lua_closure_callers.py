"""Synthetic tests of ZA Lua closure/call ownership and receiver provenance."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "za_closure_callers", ROOT / "scripts/Join-ZA-Lua-Closure-Callers.py")
owner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(owner)


def ins(op, a=0, b=0, c=0, k=0, bx=0, ax=0):
    return (op, a, b, c, k, bx, ax)


class TestClosureOwner(unittest.TestCase):
    def setUp(self):
        self.protos = [
            {"id":0, "parent":-1, "code_offset":0x80},
            {"id":1, "parent":0, "code_offset":0x100},
            {"id":2, "parent":1, "code_offset":0x200},
            {"id":3, "parent":0, "code_offset":0x300},
        ]
        self.f = [{"source":"main","class_hash":"C0123456789ABCDEF",
                   "function_hash":"F0123456789ABCDEF","root_pc":"12",
                   "child_proto_id":"1"}]
        self.s = [{"source":"main","class_hash":"C0123456789ABCDEF",
                   "s_hash":"S0123456789ABCDEF","root_pc":"19",
                   "closure_proto_id":"3"}]

    def test_direct_f_owner(self):
        lookup=owner.build_closures(self.f, self.s)
        found, grade, steps=owner.nearest_owner("main",1,self.protos,lookup)
        self.assertEqual((found["kind"],grade,steps),
                         ("F","NATIVE_DIRECT_CLOSURE_BODY",0))

    def test_direct_s_owner(self):
        lookup=owner.build_closures(self.f, self.s)
        found,grade,steps=owner.nearest_owner("main",3,self.protos,lookup)
        self.assertEqual((found["kind"],grade,steps),
                         ("S","NATIVE_DIRECT_CLOSURE_BODY",0))

    def test_lexical_child_does_not_claim_runtime_receiver(self):
        lookup=owner.build_closures(self.f, self.s)
        found,grade,steps=owner.nearest_owner("main",2,self.protos,lookup)
        self.assertEqual((found["class"],grade,steps),
                         ("C0123456789ABCDEF","NATIVE_LEXICAL_CHILD_OF_CLOSURE",1))

    def test_no_owner_for_root_or_other_source(self):
        lookup=owner.build_closures(self.f,self.s)
        self.assertEqual(owner.nearest_owner("main",0,self.protos,lookup)[1],
                         "NO_VERIFIED_CLOSURE_OWNER")
        self.assertEqual(owner.nearest_owner("event_ik",1,self.protos,lookup)[1],
                         "NO_VERIFIED_CLOSURE_OWNER")

    def test_ambiguous_closure_binding_rejected(self):
        lookup=owner.build_closures(self.f+self.f,self.s)
        self.assertEqual(owner.nearest_owner("main",1,self.protos,lookup)[1],
                         "AMBIGUOUS_CLOSURE_ASSIGNMENTS")


class TestReceiverRegister(unittest.TestCase):
    def locate(self, instructions, field, reg, consts=()):
        return owner.receiver_origin(instructions,consts,field,reg,{0},16)

    def test_self_receiver_from_upvalue(self):
        status,chain,key=self.locate(
            [ins("GETUPVAL",a=4,b=2), ins("SELF",a=2,b=4,c=0,k=1)],
            1,4,(b"F0123456789ABCDEF",))
        self.assertEqual(status,"DIRECT_UPVALUE_SLOT")
        self.assertEqual(key,"")
        self.assertIn("GETUPVAL",chain)

    def test_literal_class_hash_key_does_not_prove_class(self):
        status,chain,key=self.locate(
            [ins("GETTABUP",a=6,b=0,c=0),
             ins("SELF",a=2,b=6,c=1,k=1)],
             1,6,(b"C0123456789ABCDEF",b"F0123456789ABCDEF"))
        self.assertEqual(status,"UPVALUE_KEY_LOOKUP")
        self.assertEqual(key,"C0123456789ABCDEF")

    def test_move_chain_resolves_upvalue_slot(self):
        status,chain,key=self.locate(
            [ins("GETUPVAL",a=5,b=1),ins("MOVE",a=8,b=5),
             ins("SELF",a=2,b=8,c=0,k=1)],2,8,(b"F0123456789ABCDEF",))
        self.assertTrue(status.startswith("MOVE_FROM_DIRECT_UPVALUE_SLOT"))
        self.assertIn("MOVE",chain)

    def test_unknown_side_effect_blocks_source(self):
        status,chain,key=self.locate(
            [ins("GETUPVAL",a=5,b=1), ins("CALL",a=2),
             ins("SELF",a=2,b=5,c=0,k=1)],2,5,
            (b"F0123456789ABCDEF",))
        self.assertEqual(status,"UNKNOWN_OPCODE_BARRIER")

    def test_missing_producer_does_not_guess_receiver(self):
        status,_,key=self.locate([ins("SELF",a=2,b=5,c=0,k=1)],0,5,
                                  (b"F0123456789ABCDEF",))
        self.assertEqual(status,"SOURCE_OUTSIDE_WINDOW")
        self.assertEqual(key,"")

    def test_self_second_register_copy(self):
        status,chain,key=self.locate(
            [ins("GETUPVAL",a=5,b=1),ins("SELF",a=2,b=5,c=0,k=1),
             ins("SELF",a=4,b=3,c=0,k=1)],2,3,
            (b"F0123456789ABCDEF",))
        self.assertTrue(status.startswith("SELF_RECEIVER_COPY_OF_DIRECT_UPVALUE_SLOT"))

    def test_branch_boundary_blocks_receiver_trace(self):
        instructions=[ins("GETUPVAL",a=5,b=1),ins("MOVE",a=8,b=5),
                      ins("SELF",a=2,b=8,c=0,k=1)]
        result=owner.receiver_origin(instructions,(b"F0123456789ABCDEF",),
                                      2,8,{0,1},16)
        self.assertEqual(result[0],"CONTROL_FLOW_BOUNDARY")


if __name__=="__main__":
    unittest.main()
