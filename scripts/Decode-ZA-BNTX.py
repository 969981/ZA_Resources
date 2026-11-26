#!/usr/bin/env python3
"""ZA BNTX pointer inventory and conservative BC7 2D single-mip decoder.
Only metadata/hashes by default. Optional local PNG and DDS exports.
Layout reference: https://nintendo-formats.com/libs/nw/bntx.html
Block-linear reference: https://github.com/aboood40091/BNTX-Extractor
"""
import argparse, hashlib, io, json, re, struct, sys
from pathlib import Path
from collections import Counter

ROOT = Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual")
FMT = {0x2001:"BC7_UNORM",0x2006:"BC7_SRGB",0x1a01:"BC1_UNORM",0x1a06:"BC1_SRGB",0x1b01:"BC2_UNORM",0x1c01:"BC3_UNORM",0x1d01:"BC4_UNORM",0x1e01:"BC5_UNORM"}
for i,dim in enumerate(("4x4","5x4","5x5","6x5","6x6","8x5","8x6","8x8","10x5","10x6","10x8","10x10","12x10","12x12"),45):
    FMT[i*256+1]="ASTC_"+dim+"_UNORM"
    FMT[i*256+6]="ASTC_"+dim+"_SRGB"
def sha(b): return hashlib.sha256(b).hexdigest()
def parse(b):
    def unpack(f,o): return struct.unpack_from("<"+f,b,o)[0]
    def check(o,n):
        if o<0 or n<0 or o+n>len(b): raise ValueError("out-of-range pointer")
    if len(b)<88 or b[:8]!=b"BNTX\0\0\0\0" or b[12:14]!=b"\xff\xfe" or b[32:36]!=b"NX  ": raise ValueError("unsupported BNTX header")
    if unpack("I",28)!=len(b): raise ValueError("declared file size mismatch")
    count,table=unpack("I",36),unpack("Q",40)
    check(table,8*count)
    if not count or count>100000: raise ValueError("invalid count")
    rows=[]
    for i in range(count):
        o=unpack("Q",table+8*i); check(o,120)
        if b[o:o+4]!=b"BRTI": raise ValueError("invalid BRTI pointer")
        def u(f,k): return unpack(f,o+k)
        nameptr=u("Q",96); check(nameptr,2); n=unpack("H",nameptr); check(nameptr+2,n)
        name=b[nameptr+2:nameptr+2+n].decode("utf-8")
        mipcount=u("H",22); miptable=u("Q",112)
        if not 1<=mipcount<=32: raise ValueError("invalid mip count")
        check(miptable,8*mipcount)
        offsets=[unpack("Q",miptable+8*j) for j in range(mipcount)]
        size=u("I",80); check(offsets[0],size)
        if any(not offsets[0]<=p<offsets[0]+size for p in offsets): raise ValueError("mip outside texture storage")
        width,height,depth,array=[u("I",k) for k in (36,40,44,48)]
        if min(width,height,depth,array)<=0: raise ValueError("invalid dimensions")
        fmt=u("I",28)
        rows.append(dict(index=i,name=name,brti_offset=o,format_code=f"0x{fmt:04X}",format_name=FMT.get(fmt,"UNKNOWN"),width=width,height=height,depth=depth,array_count=array,mip_count=mipcount,storage_dim=b[o+17],image_dim=b[o+92],tile_mode=u("H",18),swizzle=u("H",20),layout_low=u("I",52),layout_high=u("I",56),block_height_log2=u("I",52)&7,image_size=size,alignment=u("I",84),channels=list(b[o+88:o+92]),mip_offsets=offsets,storage_sha256=sha(b[offsets[0]:offsets[0]+size])))
    return rows
def gob_offset(x,y,pitch,bh):
    return ((y//(8*bh))*512*bh*(pitch//64)+(x//64)*512*bh+((y%(8*bh))//8)*512+((x%64)//32)*256+((y%8)//2)*64+((x%32)//16)*32+(y%2)*16+x%16)
def linear_bc7(b,r):
    if r["format_code"] not in ("0x2001","0x2006") or r["depth"]!=1 or r["array_count"]!=1 or r["mip_count"]!=1 or r["storage_dim"]!=2 or r["image_dim"]!=1 or r["channels"]!=[2,3,4,5] or r["swizzle"]!=0 or r["tile_mode"]!=0 or r["block_height_log2"]>5:
        raise NotImplementedError("only swizzled BC7 identity RGBA single 2D mip supported")
    w,h=(r["width"]+3)//4,(r["height"]+3)//4
    if w*h>16777216: raise ValueError("texture too large")
    pitch=((w*16+63)//64)*64; bh=1<<r["block_height_log2"]
    raw=b[r["mip_offsets"][0]:r["mip_offsets"][0]+r["image_size"]]
    out=bytearray(w*h*16)
    for y in range(h):
        for x in range(w):
            p=gob_offset(x*16,y,pitch,bh)
            if p+16>len(raw): raise ValueError("swizzle address exceeds payload")
            q=(y*w+x)*16; out[q:q+16]=raw[p:p+16]
    return bytes(out)
def dds(r,blocks):
    # DDS_HEADER with DX10 extension; compressed bytes unchanged after deswizzle.
    hdr=[124,0x81007,r["height"],r["width"],len(blocks),0,1]+[0]*11
    hdr += [32,4,int.from_bytes(b"DX10","little"),0,0,0,0,0,0x1000,0,0,0,0]
    return b"DDS "+struct.pack("<31I",*hdr)+struct.pack("<5I",99 if r["format_code"]=="0x2006" else 98,3,0,1,0)+blocks
PAT=re.compile(r"^pm(\d{4})_(\d+)_(\d+)_(\d+)_(\d+)$")
def mapping(rel,r):
    m=PAT.fullmatch(r["name"])
    if not m or "/icon/" not in rel: return None
    a=list(map(int,m.groups()))
    return dict(path=rel,texture=r["name"],name_tokens=a,species_candidate=a[0],species=None,form=None,gender=None,shiny=None,status="FILENAME_CANDIDATE",directory_consistent=rel.startswith(f"ik_pokemon/data/pm{a[0]:04d}/"))
def self_test():
    assert gob_offset(0,0,64,1)==0 and gob_offset(16,0,64,1)==32 and gob_offset(0,1,64,1)==16
    assert len({gob_offset(x*16,y,64,1) for x in range(4) for y in range(8)})==32
    b=bytearray(4096+512); b[:8]=b"BNTX\0\0\0\0"; b[12:14]=b"\xff\xfe"; b[32:36]=b"NX  "
    def put(f,o,v): struct.pack_into("<"+f,b,o,v)
    put("I",28,len(b)); put("I",36,1); put("Q",40,128); put("Q",128,256); b[256:260]=b"BRTI"
    for k,v in [(28,0x2001),(36,4),(40,4),(44,1),(48,1),(80,512),(84,512)]: put("I",256+k,v)
    b[273]=2; b[348]=1; b[344:348]=bytes([2,3,4,5]); put("H",278,1); put("Q",352,512); put("Q",368,640); put("Q",640,4096)
    put("H",512,4); b[514:518]=b"test"; b[4096:4112]=bytes(range(16))
    r=parse(b)[0]; assert r["name"]=="test" and r["width"]==4 and linear_bc7(b,r)==bytes(range(16))
    assert len(dds(r,bytes(range(16))))==164
    try: parse(b[:100]); raise AssertionError("truncation accepted")
    except ValueError: pass
    print("synthetic BNTX pointer/deswizzle tests passed")
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--self-test",action="store_true"); p.add_argument("--inventory",type=Path); p.add_argument("--out",type=Path,default=Path(".za-work/bntx")); p.add_argument("--export",type=Path,help="optional local DDS/PNG output; do not publish game assets")
    a=p.parse_args()
    if a.self_test: self_test(); return
    if not a.inventory: p.error("--inventory required")
    from PIL import Image
    a.out.mkdir(parents=True,exist_ok=True)
    rows=[]; maps=[]; failures=[]; counts=Counter()
    for line in a.inventory.read_text(encoding="utf-8").splitlines():
        src=json.loads(line)
        if src["layer"]!="virtual" or src["extension"]!=".bntx" or src["category"] not in {"pokemon_icon","ui/tex/icon_item","ui/tex/icon_donut"}: continue
        rel=src["path"]; counts["candidate_paths"]+=1
        if src["representation"]!="RAW":
            failures.append(dict(path=rel,stage="representation",error=src["representation"])); continue
        try:
            b=(ROOT/rel).read_bytes(); parsed=parse(b); counts["parsed_paths"]+=1
        except Exception as e:
            failures.append(dict(path=rel,stage="parse",error=str(e))); continue
        for r in parsed:
            r.update(path=rel,source_blob=src["git_blob_sha"],source_sha256=sha(b),decode_status="NOT_DECODED")
            m=mapping(rel,r)
            if m: maps.append(m)
            try:
                blocks=linear_bc7(b,r); payload=dds(r,blocks)
                with Image.open(io.BytesIO(payload)) as im: im.load(); im=im.convert("RGBA")
                if im.size!=(r["width"],r["height"]): raise ValueError("decoded dimensions mismatch")
                hist=im.getchannel("A").histogram()
                r.update(decode_status="DECODED",linear_blocks_sha256=sha(blocks),rgba_sha256=sha(im.tobytes()),alpha_min=next(i for i,v in enumerate(hist) if v),alpha_max=max(i for i,v in enumerate(hist) if v),alpha_zero=hist[0],alpha_partial=sum(hist[1:255]),alpha_opaque=hist[255])
                if a.export:
                    dest=a.export/rel; dest=dest.parent/(dest.name+f".{r['index']}")
                    dest.parent.mkdir(parents=True,exist_ok=True); Path(str(dest)+".dds").write_bytes(payload); im.save(str(dest)+".png")
            except Exception as e:
                r.update(decode_status="UNSUPPORTED" if isinstance(e,NotImplementedError) else "FAILED",decode_error=str(e))
            rows.append(r)
    for name,data in [("textures.jsonl",rows),("pokemon-candidates.jsonl",maps),("failures.jsonl",failures)]:
        (a.out/name).write_text("".join(json.dumps(r,ensure_ascii=True)+"\n" for r in data),encoding="utf-8")
    report=dict(counts,brti_count=len(rows),pokemon_candidates=len(maps),format_counts=dict(Counter(r["format_name"] for r in rows)),decode_counts=dict(Counter(r["decode_status"] for r in rows)),by_category=dict(Counter("pokemon" if "/icon/" in r["path"] else r["path"].split("/")[2] for r in rows)),failures=len(failures),catalog_mapping_confirmed=False,parity_confirmed=False)
    (a.out/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2))
    if counts["candidate_paths"]==0 or counts["parsed_paths"]==0: sys.exit("no native BNTX parsed")
if __name__=="__main__": main()
