#!/usr/bin/env python3
"""Index native SV 4.0.0 C->F method definitions directly in whole Lua 5.4 .blua.

READ ONLY: never split, modify, decompile, or copy the large input files.
Produces small, inspectable TSV/JSON reports. A constant reference is NOT a
method definition; only specific Lua register + OP_CLOSURE + SETTABLE patterns
count as confirmed native method assignments.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HASHES = ROOT / 'tools/PokeDocs/SV/Hashlists/Lua'
DEFAULT_PRIOR = ROOT / 'tools/PokeDocs-Supplement/SV/Hashlists/Lua/recovered.tsv'
DEFAULT_OUTPUT = ROOT / 'tools/PokeDocs-Supplement/SV/Hashlists/Lua/native-4.0.0'
SOURCE_SHA = {
    'main': 'c1a4f4e2625912cf0b739a642a79ba3357df0557a544b92da22a6cb139de2815',
    'main_dynamic': 'ae4a7d0168751f53af11746ac5ae7771cb1a5bfa580bcc0f79e2b9ee85acb572',
}
HASH_ROW = re.compile(r'^0x([0-9a-fA-F]{16})[ \t]*(\S+)?[ \t]*$')
HEX_C = re.compile(rb'C[0-9A-F]{16}\Z')
HEX_F = re.compile(rb'F[0-9A-F]{16}\Z')
OPNAMES = '''MOVE LOADI LOADF LOADK LOADKX LOADFALSE LFALSESKIP LOADTRUE LOADNIL GETUPVAL SETUPVAL GETTABUP GETTABLE GETI GETFIELD SETTABUP SETTABLE SETI SETFIELD NEWTABLE SELF ADDI ADDK SUBK MULK MODK POWK DIVK IDIVK BANDK BORK BXORK SHRI SHLI ADD SUB MUL MOD POW DIV IDIV BAND BOR BXOR SHL SHR MMBIN MMBINI MMBINK UNM BNOT NOT LEN CONCAT CLOSE TBC JMP EQ LT LE EQK EQI LTI LEI GTI GEI TEST TESTSET CALL TAILCALL RETURN RETURN0 RETURN1 FORLOOP FORPREP TFORPREP TFORCALL TFORLOOP SETLIST CLOSURE VARARG VARARGPREP EXTRAARG'''.split()
assert OPNAMES[79] == 'CLOSURE'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FormatError(ValueError):
    pass


class Bin:
    def __init__(self, data: bytes):
        self.data = data
        self.off = 0

    def take(self, n):
        if n < 0 or n > len(self.data) - self.off:
            raise FormatError(f'Truncated Lua at {self.off}, take {n}')
        start = self.off
        self.off += n
        return self.data[start:self.off]

    def u8(self):
        return self.take(1)[0]

    def vint(self):
        value = 0
        for _ in range(12):
            b = self.u8()
            value = (value << 7) | (b & 127)
            if b & 128:
                return value
        raise FormatError('Oversized Lua 5.4 unsigned varint')

    def string(self):
        size = self.vint()
        return self.take(size - 1) if size else None


class Lua54:
    def __init__(self, raw: bytes):
        self.raw = raw
        self.reader = Bin(raw)
        self.protos = []

    def parse(self):
        r = self.reader
        if r.take(12) != b'\x1bLua\x54\x00\x19\x93\r\n\x1a\n':
            raise FormatError('Not standard Lua 5.4 bytecode')
        if (r.u8(),r.u8(),r.u8()) != (4,8,8):
            raise FormatError('Unsupported Lua 5.4 instruction/int/number ABI')
        if int.from_bytes(r.take(8), 'little') != 0x5678 or struct.unpack('<d',r.take(8))[0] != 370.5:
            raise FormatError('Unexpected endian or Lua floating number format')
        main_upvalues = r.u8()
        self._proto(-1,0)
        if r.off != len(r.data):
            raise FormatError(f'Lua trailing bytes: {len(r.data) - r.off}')
        return main_upvalues

    def _proto(self, parent, depth):
        if depth > 150:
            raise FormatError('Suspiciously deep Lua prototype tree')
        r=self.reader
        pid=len(self.protos)
        p={'id':pid,'parent':parent,'depth':depth,'children':[]}
        self.protos.append(p)
        r.string()  # source name, often omitted in shipped bytecode
        r.vint();r.vint() # defined line/last line
        r.take(3) # numparams, flag, maxstack
        n=r.vint()
        if n>15_000_000:
            raise FormatError('Code size beyond supported bound')
        p['code_offset']=r.off
        p['code_count']=n
        r.take(n*4)
        nk=r.vint()
        if nk>1_000_000:
            raise FormatError('Constant count beyond supported bound')
        const=[]
        for _ in range(nk):
            tag=r.u8()
            if tag in (0,1,17):const.append(None)
            elif tag in (3,19):r.take(8);const.append(None)
            elif tag in (4,20):const.append(r.string())
            else:raise FormatError(f'Unknown Lua constant tag {tag} at {r.off}')
        p['constants']=const
        nup=r.vint();r.take(3*nup)
        nch=r.vint()
        if nch>200_000:raise FormatError('Child prototype count beyond bound')
        for _ in range(nch):p['children'].append(self._proto(pid,depth+1))
        nli=r.vint();r.take(nli)
        for _ in range(r.vint()):r.vint();r.vint()
        for _ in range(r.vint()):r.string();r.vint();r.vint()
        for _ in range(r.vint()):r.string()
        return pid


def decode(word):
    opcode=word&127
    if opcode>=len(OPNAMES):raise FormatError('Lua opcode out of range')
    return (OPNAMES[opcode],(word>>7)&255,(word>>16)&255,(word>>24)&255,
            (word>>15)&1,(word>>15)&131071,(word>>7)&33554431)


def instructions(blob, proto):
    start=proto['code_offset']
    return [decode(w[0]) for w in struct.iter_unpack('<I',memoryview(blob)[start:start+4*proto['code_count']])]


def get_maps(folder):
    result={}
    for kind in ('c','f'):
        known={}; unknown=set()
        src=folder/f'lua_{kind}_hashes.txt'
        for line in src.read_text('utf-8-sig').splitlines():
            m=HASH_ROW.fullmatch(line)
            if not m:
                if not line.strip():continue
                raise ValueError(f'Bad source Lua Hashlist row: {line!r}')
            key=m.group(1).upper()
            if m.group(2):known[key]=m.group(2)
            else:unknown.add(key)
        result[kind]={'known':known,'unknown':unknown,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
    return result


def read_candidates(path):
    found={'c':{},'f':{}}
    if path.is_file():
        with path.open(encoding='utf-8',newline='') as stream:
            for row in csv.DictReader(stream,delimiter='\t'):
                k=row['kind'].lower()
                if k in found:found[k][row['hash'][2:].upper()]=row['candidate_name']
    return found


def direct_methods(lua, source_id):
    """Match exact root _ENV[C].prototype[F] = OP_CLOSURE assignment pattern."""
    root=lua.protos[0]
    constants=root['constants']
    ins=instructions(lua.raw,root)
    out=[]
    counts=Counter()
    pattern=('GETUPVAL','LOADK','GETTABLE','LOADK','GETTABLE','LOADK','CLOSURE','SETTABLE')
    for pc in range(len(ins)-7):
        seg=ins[pc:pc+8]
        if tuple(s[0] for s in seg) != pattern:continue
        a=seg[0][1]
        if any(not 0<=s[5]<len(constants) for s in [seg[1],seg[3],seg[5]]):continue
        c=constants[seg[1][5]]
        f=constants[seg[5][5]]
        if not (c and HEX_C.fullmatch(c) and f and HEX_F.fullmatch(f) and constants[seg[3][5]]==b'prototype'):continue
        if (seg[1][1]!=a+1 or seg[2][1:4]!=(a,a,a+1) or seg[3][1]!=a+1
            or seg[4][1:4]!=(a,a,a+1) or seg[5][1]!=a+1 or seg[6][1]!=a+2
            or seg[7][1:4]!=(a,a+1,a+2) or seg[0][2]!=0):
            counts['unverified_register_sequence']+=1
            continue
        child_index=seg[6][5]
        if child_index>=len(root['children']):
            raise FormatError(f'OP_CLOSURE index out of bounds at pc={pc}')
        pid=root['children'][child_index]
        out.append({'source':source_id,'class_hash':c.decode(),'function_hash':f.decode(),
                    'root_pc':pc,'assignment_pc':pc+7,'child_proto_id':pid,
                    'child_proto_index':child_index,'body_instructions':lua.protos[pid]['code_count'],
                    'evidence':'NATIVE_LUA54_CLOSURE_SETTABLE'})
    return out,counts


def usages(lua, wanted, caller_by_pid, source):
    """Usage of unknown F *within caller function code*, not proof of F ownership."""
    occurrences=[]
    for p in lua.protos:
        if not p['constants'] or not wanted:continue
        byconst={i:v[1:].decode() for i,v in enumerate(p['constants']) if v and HEX_F.fullmatch(v) and v[1:].decode() in wanted}
        if not byconst:continue
        ins=instructions(lua.raw,p)
        seen=Counter()
        for pc,(name,a,b,c,k,bx,ax) in enumerate(ins):
            idx=None
            if name=='LOADK':idx=bx
            elif name=='LOADKX' and pc+1<len(ins) and ins[pc+1][0]=='EXTRAARG':idx=ins[pc+1][6]
            elif name in ('GETFIELD','GETTABUP'):idx=c
            elif name in ('SETFIELD','SETTABUP','EQK'):idx=b
            elif name=='SELF' and k==1:idx=c
            if idx not in byconst:continue
            method=byconst[idx];seen[method]+=1
            parents=caller_by_pid.get(p['id'],[])
            if parents:
                for parent in parents:
                    occurrences.append({'source':source,'unknown_f_hash':'F'+method,
                        'usage_op':name,'usage_pc':pc,'caller_class_hash':parent['class_hash'],
                        'caller_function_hash':parent['function_hash'],
                        'caller_definition_root_pc':parent['root_pc'],
                        'caller_proto_id':p['id'],'evidence':'NATIVE_CALLER_REFERENCE_ONLY'})
            else:
                occurrences.append({'source':source,'unknown_f_hash':'F'+method,
                                    'usage_op':name,'usage_pc':pc,'caller_class_hash':'',
                                    'caller_function_hash':'','caller_definition_root_pc':'',
                                    'caller_proto_id':p['id'],'evidence':'NATIVE_UNOWNED_PROTOTYPE_REFERENCE'})
        # A constant that exists but was not referenced by supported opcode is not a usage.
    return occurrences


def emit_tsv(rows, columns):
    out=io.StringIO()
    writer=csv.DictWriter(out,columns,delimiter='\t',lineterminator='\n',extrasaction='ignore')
    writer.writeheader()
    for item in rows:writer.writerow(item)
    return out.getvalue().encode()


def analyze(main_path,dynamic_path,maps,candidates,allow_other_shas=False):
    blobs={'main':main_path,'main_dynamic':dynamic_path}
    files={}; all_method=[]; all_usages=[]; all_protos={}
    for key,path in blobs.items():
        raw=path.read_bytes();hashsum=sha256(raw)
        if not allow_other_shas and hashsum!=SOURCE_SHA[key]:
            raise ValueError(f'{key}: unexpected SHA-256 {hashsum}, expected pinned SV 4.0.0')
        lua=Lua54(raw);lua.parse()
        methods,drops=direct_methods(lua,key)
        index=defaultdict(list)
        for method in methods:index[method['child_proto_id']].append(method)
        usages_table=usages(lua,maps['f']['unknown'],index,key)
        all_method+=methods;all_usages+=usages_table
        files[key]={'file_name':path.name,'sha256':hashsum,'bytes':len(raw),
                    'prototype_count':len(lua.protos),'top_level_proto_count':len(lua.protos[0]['children']),
                    'direct_method_edges':len(methods),'direct_c_count':len({r['class_hash'] for r in methods}),
                    'method_pattern_rejected':dict(drops),'referenced_unknown_f_occurrences':len(usages_table)}
        all_protos[key]=lua
    byclass=defaultdict(list)
    for x in all_method:byclass[x['class_hash'][1:]].append(x)
    byf=defaultdict(list)
    for x in all_method:byf[x['function_hash'][1:]].append(x)
    callbyf=defaultdict(list)
    for x in all_usages:callbyf[x['unknown_f_hash'][1:]].append(x)
    crows=[]
    for hashvalue in sorted(maps['c']['unknown']):
        related=byclass.get(hashvalue,[])
        names={x['source'] for x in related}
        crows.append({'class_hash':'C'+hashvalue,
                      'previous_hash_exact_candidate':candidates['c'].get(hashvalue,''),
                      'native_direct_methods':len(related),
                      'native_distinct_functions':len({x['function_hash'] for x in related}),
                      'present_in_main':int('main' in names),
                      'present_in_main_dynamic':int('main_dynamic' in names),
                      'first_root_pc':min((x['root_pc'] for x in related),default=''),
                      'sample_method_hashes':';'.join(sorted({x['function_hash'] for x in related})[:6]),
                      'status':'NATIVE_4_0_0_METHOD_OWNER' if related else 'NOT_DIRECTLY_DEFINED'})
    frows=[]
    for hashvalue in sorted(maps['f']['unknown']):
        usageset=callbyf.get(hashvalue,[])
        defs=byf.get(hashvalue,[])
        callers=sorted({u['caller_class_hash']+'.'+u['caller_function_hash'] for u in usageset if u['caller_class_hash']})
        frows.append({'function_hash':'F'+hashvalue,
                      'previous_hash_exact_candidate':candidates['f'].get(hashvalue,''),
                      'native_direct_definitions':len(defs),
                      'native_caller_reference_ops':len(usageset),
                      'distinct_caller_methods':len(callers),
                      'caller_examples':';'.join(callers[:12]),
                      'reference_opcode_types':';'.join(sorted({u['usage_op'] for u in usageset})),
                      'status':'NATIVE_4_0_0_DEFINITION' if defs else 'NATIVE_4_0_0_CALLER_REFERENCE' if usageset else 'NOT_REFERENCED_BY_SUPPORTED_OPS'})
    summary={
       'scope':'Whole main.blua / main_dynamic.blua; NEVER split or alter inputs',
       'evidence':'NATIVE_4_0_0_DIRECT_METHOD_REGISTER_ASSIGNMENT',
       'caution':'F references inside a method body describe callers, not callee owner',
       'files':files,
       'total_direct_cf_edges':len(all_method),
       'unique_cf_edges':len({(x['source'],x['class_hash'],x['function_hash']) for x in all_method}),
       'unknown_class_count_original':len(maps['c']['unknown']),
       'unknown_class_with_native_methods':sum(bool(byclass.get(x)) for x in maps['c']['unknown']),
       'unknown_function_count_original':len(maps['f']['unknown']),
       'unknown_function_with_native_direct_definition':sum(bool(byf.get(x)) for x in maps['f']['unknown']),
       'unknown_function_with_caller_references':sum(bool(callbyf.get(x)) for x in maps['f']['unknown']),
       'unknown_f_caller_reference_rows':len(all_usages),
       'pokedocs_original_sha256':{k:v['source_sha256'] for k,v in maps.items()},
       'big_files_split':False,
       'originals_modified':False
    }
    outputs={
       'native-summary.json':(json.dumps(summary,indent=2,ensure_ascii=False,sort_keys=True)+'\n').encode(),
       'native-class-method-edges.tsv':emit_tsv(all_method,[
           'source','class_hash','function_hash','root_pc','assignment_pc','child_proto_id',
           'child_proto_index','body_instructions','evidence']),
       'native-unknown-c.tsv':emit_tsv(crows,[
           'class_hash','previous_hash_exact_candidate','native_direct_methods','native_distinct_functions',
           'present_in_main','present_in_main_dynamic','first_root_pc','sample_method_hashes','status']),
       'native-unknown-f.tsv':emit_tsv(frows,[
           'function_hash','previous_hash_exact_candidate','native_direct_definitions',
           'native_caller_reference_ops','distinct_caller_methods','caller_examples',
           'reference_opcode_types','status']),
       'native-unknown-f-calls.tsv':emit_tsv(all_usages,[
           'source','unknown_f_hash','usage_op','usage_pc','caller_class_hash',
           'caller_function_hash','caller_definition_root_pc','caller_proto_id','evidence'])
    }
    return outputs,summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main',required=True,type=Path)
    parser.add_argument('--dynamic',required=True,type=Path)
    parser.add_argument('--hashlists',type=Path,default=DEFAULT_HASHES)
    parser.add_argument('--prior',type=Path,default=DEFAULT_PRIOR)
    parser.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--allow-other-shas',action='store_true')
    args=parser.parse_args()
    outputs, summary=analyze(args.main,args.dynamic,get_maps(args.hashlists),
                             read_candidates(args.prior),args.allow_other_shas)
    if args.verify_only:
        for name,data in outputs.items():
            path=args.output/name
            if not path.is_file() or path.read_bytes()!=data:raise SystemExit(f'Non-reproducible {path}')
    else:
        args.output.mkdir(parents=True,exist_ok=True)
        for name,data in outputs.items():
            dest=args.output/name
            if not dest.is_file() or dest.read_bytes()!=data:dest.write_bytes(data)
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=='__main__':main()