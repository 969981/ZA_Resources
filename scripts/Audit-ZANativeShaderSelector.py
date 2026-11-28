#!/usr/bin/env python3
"""Read-only AArch64 string reference scan; candidate consumer sites, not function identity."""
import hashlib,json,struct,subprocess,collections
from pathlib import Path
import numpy as np
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
ELF=Path("Unpack/v2.0.2/exefs/main/main.elf")
OUT=Path(".za-work/ZANativeShaderCore")
NEEDLES=[b".trsha",b".bnsh",b".trtch",b"technique_list",b"EnableDisplacementMap",b"NumRequiredUV",b"IkCharacterTransparent",b"FresnelEffect",b"InsideEmissionParallax",b"ShaderVariation",b"ShaderProgram",b"ShaderArchive",b"ShaderModel",b"GetShader",b"shader/NX64",b"env_ikkaku"]
def segments(b):
    if b[:6]!=b"\x7fELF\x02\x01" or struct.unpack_from("<H",b,18)[0]!=183:raise ValueError("ELF format")
    po=struct.unpack_from("<Q",b,32)[0];sz,n=struct.unpack_from("<HH",b,54)
    for i in range(n):
        typ,flags,off,va,_,size,_,_=struct.unpack_from("<IIQQQQQQ",b,po+i*sz)
        if typ==1 and size and off+size<=len(b):yield off,va,size,flags
def main():
    b=ELF.read_bytes();oid=subprocess.check_output(["git","rev-parse","HEAD:"+ELF.as_posix()],text=True).strip()
    if hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()!=oid:raise ValueError("ELF blob mismatch")
    seg=list(segments(b));strings=collections.defaultdict(set)
    for off,va,size,flags in seg:
        if flags&1:continue
        data=b[off:off+size]
        for needle in NEEDLES:
            start=0
            while True:
                pos=data.find(needle,start)
                if pos<0:break
                start=pos+len(needle);lo=pos;hi=pos+len(needle)
                while lo>0 and pos-lo<160 and 32<=data[lo-1]<127:lo-=1
                while hi<len(data) and hi-pos<200 and 32<=data[hi]<127:hi+=1
                if hi>=len(data) or data[hi]!=0 or (lo and 32<=data[lo-1]<127):continue
                strings[va+lo].add(data[lo:hi].decode("ascii"))
    refs=[];md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    for off,va,size,flags in seg:
        if not flags&1:continue
        w=np.frombuffer(b,dtype="<u4",count=size//4,offset=off)
        candidates=np.flatnonzero((w&0x9f000000)==0x90000000)
        for k in candidates:
            k=int(k);v=int(w[k]);reg=v&31;imm=((v>>29)&3)|(((v>>5)&0x7ffff)<<2)
            if imm&(1<<20):imm-=1<<21
            pc=va+4*k;page=(pc&~4095)+(imm<<12)
            # Strict adjacent ADD only; do not claim arbitrary dataflow.
            if k+1>=len(w):continue
            a=int(w[k+1])
            if a&0xffc00000!=0x91000000 or (a>>5)&31!=reg:continue
            target=page+((a>>10)&4095)
            if target not in strings:continue
            lo=max(0,k-8);hi=min(len(w),k+24);raw=b[off+lo*4:off+hi*4]
            context=[dict(pc=hex(i.address),op=i.mnemonic,args=i.op_str) for i in md.disasm(raw,va+lo*4)]
            refs.append(dict(pc=hex(pc),target=hex(target),strings=sorted(strings[target]),context=context,status="DIRECT_STRING_REFERENCE_CANDIDATE"))
    rows=[dict(va=hex(k),strings=sorted(v)) for k,v in sorted(strings.items())]
    result=dict(elf_sha256=hashlib.sha256(b).hexdigest(),git_blob=oid,string_locations=len(rows),adjacent_adrp_add_refs=len(refs),native_selector_verified=False)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"elf-shader-strings.json").write_text(json.dumps(rows,indent=2)+"\n")
    (OUT/"elf-shader-xrefs.json").write_text(json.dumps(refs,indent=2)+"\n")
    (OUT/"elf-shader-summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("ELF_SHADER_SUMMARY",json.dumps(result))
    for r in refs[:40]:print("ELF_SHADER_XREF",json.dumps({k:v for k,v in r.items() if k!="context"}))
if __name__=="__main__":main()
