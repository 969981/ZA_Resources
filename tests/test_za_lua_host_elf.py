"""No-ROM synthetic AArch64 ELF tests for ZA Lua host-loader triage."""
import importlib.util
import struct
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "za_elf_probe",ROOT/"scripts/Probe-ZA-Lua-Host-ELF.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def adrp(reg, pc, target):
    diff=((target&~4095)-(pc&~4095))//4096
    unsigned=diff&((1<<21)-1)
    return (0x90000000 | (unsigned&3)<<29 |
            (unsigned>>2)<<5 | reg)


def add_x(reg,src,imm):
    return 0x91000000 | (imm<<10) | (src<<5) | reg


def fixture_elf(needle=b"main_dynamic.blua\x00luaL_loadbufferx\x00"):
    names=b"\x00.text\x00.rodata\x00.shstrtab\x00"
    file=bytearray(0x480)
    elf_header=struct.pack("<16sHHIQQQIHHHHHH",
        b"\x7fELF"+bytes([2,1,1])+b"\x00"*9,
        2,183,1,0x1000,0,0x380,0,64,56,0,64,4,3)
    file[:64]=elf_header
    words=(adrp(3,0x1000,0x3000),add_x(3,3,0),0xD65F03C0,0xD503201F)
    for i,w in enumerate(words):
        struct.pack_into("<I",file,0x100+i*4,w)
    file[0x200:0x200+len(needle)]=needle
    file[0x300:0x300+len(names)]=names
    shs=[
        (0,0,0,0,0,0,0,0,0,0),
        (1,1,6,0x1000,0x100,16,0,0,4,0),
        (7,1,2,0x3000,0x200,len(needle),0,0,1,0),
        (15,3,0,0,0x300,len(names),0,0,1,0),
    ]
    for i,sh in enumerate(shs):
        struct.pack_into("<IIQQQQIIQQ",file,0x380+i*64,*sh)
    return bytes(file)


class SyntheticELFTests(unittest.TestCase):
    def test_elf64_sections_and_locations(self):
        elf=mod.ELF64(fixture_elf())
        self.assertEqual(len(elf.sections),4)
        self.assertEqual(elf.sections[2]["name"],".rodata")
        self.assertEqual(elf.location(0x200),(0x3000,".rodata"))
        self.assertEqual(len(elf.text_regions()),1)

    def test_exact_string_address_xref_and_no_runtime_proof(self):
        elf=mod.ELF64(fixture_elf())
        hits,total,truncated=mod.scan_strings(elf,"main")
        self.assertEqual(total,2)
        self.assertFalse(truncated)
        refs=mod.scan_adr_xrefs(elf,"main",hits)
        self.assertEqual(len(refs),1)
        self.assertEqual(refs[0][1],"0x3000")
        self.assertEqual(refs[0][3],"0x1000")
        self.assertEqual(refs[0][5],"NATIVE_AARCH64_ADRP_ADD_GAP1")

    def test_targeted_hash_byte_probe_is_only_match(self):
        needle=(b"S062729EC443620C2\x00"+
                struct.pack("<Q",int(mod.S_GAPS[0],16)))
        elf=mod.ELF64(fixture_elf(needle))
        matches=mod.scan_hashes(elf,"main")
        self.assertTrue(any(x[1]=="S" and x[3]=="ASCII_PREFIXED" for x in matches))
        self.assertTrue(any(x[1]=="S" and x[3]=="LITTLE_ENDIAN_UINT64" for x in matches))
        self.assertTrue(all("NOT_PROVEN_RUNTIME" in x[-1] for x in matches))

    def test_reject_wrong_abi_and_out_of_bounds_section(self):
        blob=bytearray(fixture_elf())
        blob[18]=0
        with self.assertRaisesRegex(ValueError,"AArch64"):
            mod.ELF64(bytes(blob))
        blob=bytearray(fixture_elf())
        struct.pack_into("<Q",blob,0x380+2*64+32,0xFFFFFFFF)
        with self.assertRaisesRegex(ValueError,"section outside file"):
            mod.ELF64(bytes(blob))

    def test_adr_and_add_decoder_signed_and_shifted(self):
        pc=0x1000
        self.assertEqual(mod.decode_adrp(adrp(7,pc,0x3000),pc),(7,0x3000))
        self.assertEqual(mod.decode_adrp(adrp(7,pc,0x0),pc),(7,0x0))
        self.assertEqual(mod.decode_add_x_imm(add_x(1,1,39)),(1,1,39))
        self.assertIsNone(mod.decode_adrp(0xD65F03C0,pc))


if __name__=="__main__":
    unittest.main()
