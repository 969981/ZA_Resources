"""Deterministic Lua 5.4 capture descriptor and closure-site tests (no game bytes)."""
import importlib.util
import struct
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "za_upvalue_captures", ROOT/"scripts/Trace-ZA-Lua-Upvalue-Captures.py")
ua=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ua)
owner=ua.load_owner()
core=owner.load_flow().load_direct().load_core()


def ins(op, a=0,b=0,c=0,k=0,bx=0,ax=0):
    return (op,a,b,c,k,bx,ax)


class FakeLua:
    def __init__(self,protos):
        self.protos=protos


def fake_p(pid,parent,children,upvalues,constants=()):
    return {"id":pid,"parent":parent,"children":children,
            "upvalues":upvalues,"constants":list(constants),"code_offset":0x100+pid*100}


class TestNativeCapture(unittest.TestCase):
    def test_parent_upvalue_to_root_external(self):
        lua=FakeLua([
            fake_p(0,-1,[1],[(1,0,0)]),
            fake_p(1,0,[],[(0,0,0)])])
        inst={0:[ins("CLOSURE",bx=0)],1:[]}
        state,depth,chain,creation,producer=ua.trace_capture(lua,inst,1,0,owner)
        self.assertEqual(state,"ROOT_EXTERNAL_UPVALUE")
        self.assertEqual(depth,1)
        self.assertIn("P1.U0(s=0,i=0,k=0)->P0.U0",chain)
        self.assertIn("P0.CLOSURE[0]@0",creation)

    def test_parent_stack_captured_root_upvalue_register(self):
        lua=FakeLua([
            fake_p(0,-1,[1],[(1,0,0)]),
            fake_p(1,0,[],[(1,4,0)])])
        inst={0:[ins("GETUPVAL",a=4,b=0), ins("CLOSURE",a=0,bx=0)],1:[]}
        state,depth,chain,creation,producer=ua.trace_capture(lua,inst,1,0,owner)
        self.assertEqual(state,"ROOT_EXTERNAL_UPVALUE")
        self.assertEqual(depth,1)
        self.assertIn("P0.R4<-P0.U0",chain)
        self.assertIn("DIRECT_UPVALUE_SLOT",producer)

    def test_multiple_creation_sites_must_remain_ambiguous(self):
        lua=FakeLua([
            fake_p(0,-1,[1],[(1,0,0)]),
            fake_p(1,0,[],[(1,4,0)])])
        inst={0:[ins("GETUPVAL",a=4,b=0), ins("CLOSURE",bx=0),
                 ins("GETUPVAL",a=4,b=0),ins("CLOSURE",bx=0)],1:[]}
        state,*_=ua.trace_capture(lua,inst,1,0,owner)
        self.assertEqual(state,"PARENT_STACK_CAPTURE_MULTIPLE_SITES")

    def test_missing_native_closure_site_is_not_repaired_by_guess(self):
        lua=FakeLua([
            fake_p(0,-1,[1],[(1,0,0)]),
            fake_p(1,0,[],[(0,0,0)])])
        state,*_=ua.trace_capture(lua,{0:[],1:[]},1,0,owner)
        self.assertEqual(state,"NO_NATIVE_CLOSURE_SITE")

    def test_bad_upvalue_reference_rejected(self):
        lua=FakeLua([
            fake_p(0,-1,[1],[(1,0,0)]),
            fake_p(1,0,[],[(0,9,0)])])
        with self.assertRaisesRegex(ValueError,"Invalid parent upvalue"):
            ua.trace_capture(lua,{0:[ins("CLOSURE",bx=0)],1:[]},1,0,owner)

    def test_lookup_native_opcode_and_static_class_key(self):
        C=b"C0C062DE5AED06885"
        lua=FakeLua([fake_p(0,-1,[],[(1,0,0)],[C])])
        # GETTABUP R2 U0 K0, GETFIELD R2 R2 K1, CALL R2
        inst={0:[ins("GETTABUP",2,0,0),ins("GETFIELD",2,2,1),
                 ins("CALL",2)]}
        lua.protos[0]["constants"].append(b"S3D047DB5B440735C")
        row={"source":"main","proto_id":"0","field_pc":"1","call_pc":"2",
             "receiver_origin_kind":"UPVALUE_KEY_LOOKUP",
             "receiver_origin_trace":"0:GETTABUP(R2,R0,R0,k0)",
             "receiver_static_class_key":C.decode(),
             "hash_token":"S3D047DB5B440735C","owner_class_hash":"",
             "owner_member_hash":"","owner_grade":"NO_VERIFIED_CLOSURE_OWNER"}
        traced=ua.trace_static_lookup(row,lua,inst,owner)
        self.assertEqual(traced[5],C.decode())
        self.assertEqual(traced[10],"ROOT_EXTERNAL_UPVALUE")
        self.assertEqual(traced[17],"NO")
        row["receiver_static_class_key"]="CFFFFFFFFFFFFFFFF"
        with self.assertRaisesRegex(ValueError,"original native C lookup"):
            ua.trace_static_lookup(row,lua,inst,owner)

    def test_child_index_must_match_binary_closure_index(self):
        lua=FakeLua([fake_p(0,-1,[1,2],[]),
                     fake_p(1,0,[],[]),fake_p(2,0,[],[])])
        idx,pcs=ua.closure_sites(lua,{0:[ins("CLOSURE",bx=1),ins("CLOSURE",bx=0)],
                                       1:[],2:[]},0,1)
        self.assertEqual((idx,pcs),(0,[1]))


def varint(n):
    if not 0<=n<128: raise ValueError("fixture supports single-byte varints")
    return bytes([0x80|n])


def proto_fixture(children,upvalues,instructions=()):
    b=bytearray()
    b+=varint(0)       # stripped source name
    b+=varint(0)+varint(0) # line / last_line
    b+=bytes([0,0,5]) # numparams/flags/maxstack
    b+=varint(len(instructions))
    for word in instructions:b+=struct.pack("<I",word)
    b+=varint(0) # constants
    b+=varint(len(upvalues))
    for triple in upvalues:b+=bytes(triple)
    b+=varint(len(children))
    for child in children:b+=child
    b+=varint(0)*4 # line info, abslineinfo, local vars, upvalue names
    return bytes(b)


class TestRealLua54BinaryLayout(unittest.TestCase):
    def test_upvalue_descriptor_three_bytes_are_preserved(self):
        inner=proto_fixture([],[(0,0,0)])
        # OP_CLOSURE index=0; opcode 79 in Lua 5.4, A=0, Bx=0
        outer=proto_fixture([inner],[(1,0,0)],(79,))
        chunk=(b"\x1bLua\x54\x00\x19\x93\r\n\x1a\n"+bytes([4,8,8])
               +struct.pack("<Q",0x5678)+struct.pack("<d",370.5)
               +bytes([1])+outer)
        lua=core.Lua54(chunk)
        self.assertEqual(lua.parse(),1)
        self.assertEqual(lua.main_upvalues,1)
        self.assertEqual(lua.protos[0]["upvalues"],[(1,0,0)])
        self.assertEqual(lua.protos[1]["upvalues"],[(0,0,0)])
        instr={p["id"]:core.instructions(chunk,p) for p in lua.protos}
        self.assertEqual(ua.closure_sites(lua,instr,0,1),(0,[0]))
        self.assertEqual(ua.trace_capture(lua,instr,1,0,owner)[0],
                         "ROOT_EXTERNAL_UPVALUE")


if __name__=="__main__":
    unittest.main()
