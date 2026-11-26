#!/usr/bin/env python3
"""Read-only ZA UI SARC/BNTX inventory and local image pack."""
import argparse, collections, hashlib, importlib.util, io, json, re, sqlite3, struct, subprocess
from pathlib import Path
ROOT=Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual")
CATS="pokemon items balls types moves badges ribbons donuts characters maps ui atlases manifests database docs".split()
spec=importlib.util.spec_from_file_location("bntx",Path(__file__).with_name("Decode-ZA-BNTX.py"))
bntx=importlib.util.module_from_spec(spec); spec.loader.exec_module(bntx)
def sha(b): return hashlib.sha256(b).hexdigest()

def sarc(b):
    if len(b)<32 or b[:4]!=b"SARC": raise ValueError("not SARC")
    e={b"\xff\xfe":"<",b"\xfe\xff":">"}.get(bytes(b[6:8]))
    if not e: raise ValueError("BOM")
    def u(f,o): return struct.unpack_from(e+f,b,o)[0]
    h=u("H",4); data=u("I",12)
    if h<20 or u("I",8)!=len(b) or not h+12<=data<=len(b) or b[h:h+4]!=b"SFAT": raise ValueError("header")
    size=u("H",h+4); count=u("H",h+6); mul=u("I",h+8)
    start=h+size; nt=start+16*count
    if size<12 or nt+8>data or b[nt:nt+4]!=b"SFNT": raise ValueError("SFAT/SFNT")
    ns=nt+u("H",nt+4)
    if not nt+8<=ns<=data: raise ValueError("SFNT header")
    for i in range(count):
        p=start+i*16; nh=u("I",p); flags=u("I",p+4); lo=data+u("I",p+8); hi=data+u("I",p+12)
        if not data<=lo<=hi<=len(b): raise ValueError("member bounds")
        name=None; ok=None
        if flags>>24:
            off=ns+(flags&0xffffff)*4
            if not ns<=off<data: raise ValueError("name offset")
            end=b.find(b"\0",off,data)
            if end<0: raise ValueError("unterminated name")
            raw=b[off:end]; name=raw.decode("utf-8"); computed=0
            for ch in raw: computed=(computed*mul+ch)&0xffffffff
            ok=computed==nh
        yield dict(index=i,name=name,name_hash=f"{nh:08x}",name_hash_matches=ok,offset=lo,size=hi-lo),b[lo:hi]

BC={0x1a:(8,b"DXT1"),0x1b:(16,b"DXT3"),0x1c:(16,b"DXT5"),0x1d:(8,b"BC4U"),0x1e:(16,b"BC5U"),0x20:(16,b"DX10")}
def decode(b,r):
    from PIL import Image
    fmt=int(r["format_code"],16); kind=fmt>>8
    if kind not in BC or fmt&255 not in (1,6) or (fmt&255==6 and kind not in (0x1a,0x1b,0x1c,0x20)): raise NotImplementedError("format")
    if (r["depth"],r["array_count"],r["mip_count"],r["storage_dim"],r["image_dim"],r["tile_mode"],r["swizzle"])!=(1,1,1,2,1,0,0) or r["block_height_log2"]>5: raise NotImplementedError("layout")
    w,h=r["width"],r["height"]
    if w*h>16777216: raise ValueError("oversized")
    if any(c not in range(6) for c in r["channels"]): raise NotImplementedError("channel selector")
    if kind in (0x1d,0x1e) and any(c in ([3,4,5] if kind==0x1d else [4,5]) for c in r["channels"]): raise NotImplementedError("absent channel")
    bs,cc=BC[kind]; bw,bh=(w+3)//4,(h+3)//4; pitch=((bw*bs+63)//64)*64
    raw=b[r["mip_offsets"][0]:r["mip_offsets"][0]+r["image_size"]]; blocks=bytearray()
    for y in range(bh):
        for x in range(bw):
            p=bntx.gob_offset(x*bs,y,pitch,1<<r["block_height_log2"])
            if p+bs>len(raw): raise ValueError("GOB bounds")
            blocks.extend(raw[p:p+bs])
    hdr=[124,0x81007,h,w,len(blocks),0,1]+[0]*11+[32,4,int.from_bytes(cc,"little"),0,0,0,0,0,0x1000,0,0,0,0]
    dds=b"DDS "+struct.pack("<31I",*hdr)
    if kind==0x20: dds+=struct.pack("<5I",99 if fmt&255==6 else 98,3,0,1,0)
    dds+=blocks
    with Image.open(io.BytesIO(dds)) as im:
        im.load()
        if im.size!=(w,h): raise ValueError("pixel dimensions")
        bands=im.split() if kind in (0x1d,0x1e) else im.convert("RGBA").split()
        channels=[Image.new("L",im.size,0),Image.new("L",im.size,255),*bands]
        rgba=Image.merge("RGBA",[channels[c] for c in r["channels"]])
    return rgba,bytes(blocks)

def classify(path,name):
    if path.startswith("ik_pokemon/"): return "pokemon"
    for prefix,cat in [("icon_item","items"),("icon_donut","donuts"),("chara","characters"),("ryl_npc","characters"),("map_pic","maps")]:
        if path.startswith("ui/tex/"+prefix+"/"): return cat
    for pat,cat in [(r"(?:^|_)icon_type(?:_|$)","types"),(r"(?:^|_)(?:ribbon|mark_icon|icon_mark)(?:_|$)","ribbons"),(r"(?:^|_)(?:badge|medal|achievement)(?:_|$)","badges"),(r"(?:^|_)icon_ball(?:_|$)","balls"),(r"(?:^|_)(?:waza_category|move_category|icon_waza)(?:_|$)","moves")]:
        if re.search(pat,name.lower()): return cat
    return "ui"

def tracked(ref):
    root=ROOT.as_posix()+"/"
    for line in subprocess.check_output(["git","ls-tree","-rz",ref,"--",ROOT.as_posix()]).split(b"\0"):
        if not line: continue
        meta,path=line.split(b"\t",1); mode,kind,oid=meta.decode().split()
        if kind!="blob": continue
        path=path.decode("utf-8")[len(root):]; logical=re.sub(r"\.7z\.\d+$","",path)
        if (logical.startswith("ui/data/") and logical.endswith(".arc")) or (logical.startswith("ui/tex/") and logical.endswith(".bntx")) or (logical.startswith("ik_pokemon/data/") and "/icon/" in logical and logical.endswith(".bntx")): yield logical,path,oid

def run(out,ref,export=False):
    if out.exists() and any(out.iterdir()): raise ValueError("output directory must be empty")
    for c in CATS: (out/c).mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(out/"database"/"images.sqlite")
    db.executescript("""CREATE TABLE source(path TEXT PRIMARY KEY,blob TEXT,representation TEXT,status TEXT,sha256 TEXT,detail TEXT);
    CREATE TABLE member(blob TEXT,member_index INTEGER,name TEXT,sha256 TEXT,metadata TEXT,PRIMARY KEY(blob,member_index));
    CREATE TABLE texture(blob TEXT,member_index INTEGER,texture_index INTEGER,name TEXT,category TEXT,width INTEGER,height INTEGER,format TEXT,rgba_sha256 TEXT,png_path TEXT,status TEXT,metadata TEXT,PRIMARY KEY(blob,member_index,texture_index));
    CREATE TABLE mapping(blob TEXT,member_index INTEGER,texture_index INTEGER,domain TEXT,game_id INTEGER,form INTEGER,gender INTEGER,shiny INTEGER,evidence TEXT);
    CREATE VIEW image_sources AS SELECT s.path,t.* FROM source s JOIN texture t USING(blob) WHERE s.status='PARSED';""")
    counts=collections.Counter(); groups=collections.defaultdict(list); cache={}
    for logical,path,oid in tracked(ref): groups[logical].append((path,oid))
    for logical,entries in sorted(groups.items()):
        counts["logical_paths"]+=1; counts["path:"+Path(logical).suffix]+=1
        if len(entries)!=1 or entries[0][0]!=logical:
            db.execute("INSERT INTO source VALUES(?,?,?,?,?,?)",(logical,None,"SPLIT_OR_MIXED","UNRESTORED",None,json.dumps(entries))); counts["unrestored"]+=1; continue
        path,oid=entries[0]
        if oid in cache:
            status,digest,detail=cache[oid]; db.execute("INSERT INTO source VALUES(?,?,?,?,?,?)",(logical,oid,"RAW",status,digest,detail)); counts["alias_paths"]+=1; continue
        digest=None; detail=None
        try:
            raw=(ROOT/path).read_bytes()
            if hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()!=oid: raise ValueError("working tree mismatch")
            digest=sha(raw); counts["unique_raw_blobs"]+=1; counts["blob:"+Path(path).suffix]+=1
            members=list(sarc(raw)) if path.endswith(".arc") else [(dict(index=-1,name=None,offset=0,size=len(raw)),raw)]
            status="PARSED"; counts["parsed_unique_blobs"]+=1
            for m,b in members:
                m.update(magic=b[:4].hex()); mi=m["index"]; counts["members"]+=1
                db.execute("INSERT INTO member VALUES(?,?,?,?,?)",(oid,mi,m["name"],sha(b),json.dumps(m)))
                if b[:4]!=b"BNTX":
                    if path.endswith(".bntx") or (m["name"] or "").lower().endswith(".bntx"): counts["bntx_magic_mismatch"]+=1
                    continue
                try: textures=bntx.parse(b)
                except Exception as e:
                    m["bntx_error"]=str(e); db.execute("UPDATE member SET metadata=? WHERE blob=? AND member_index=?",(json.dumps(m),oid,mi)); counts["bntx_parse_failures"]+=1; continue
                for t in textures:
                    cat=classify(path,t["name"]); counts["texture:"+cat]+=1; counts["format:"+t["format_code"]]+=1
                    pix=None; png=None; state="UNSUPPORTED"
                    try:
                        im,blocks=decode(b,t); pix=sha(im.tobytes()); t["linear_blocks_sha256"]=sha(blocks); t["alpha_histogram"]=im.getchannel("A").histogram()
                        if export:
                            key=sha((oid+":"+str(mi)+":"+str(t["index"])).encode()); png=f"{cat}/{key}.png"; im.save(out/png)
                        state="DECODED_CANDIDATE"
                    except NotImplementedError as e: t["decode_error"]=str(e)
                    except Exception as e: state="FAILED"; t["decode_error"]=str(e)
                    counts[state]+=1
                    db.execute("INSERT INTO texture VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(oid,mi,t["index"],t["name"],cat,t["width"],t["height"],t["format_code"],pix,png,state,json.dumps(t)))
        except Exception as e:
            status="FAILED"; detail=str(e); counts["source_failures"]+=1
        cache[oid]=(status,digest,detail); db.execute("INSERT INTO source VALUES(?,?,?,?,?,?)",(logical,oid,"RAW",status,digest,detail)); db.commit()
    report=dict(source_commit=ref,counts=dict(counts),png_export=export,classification="NAME_PATH_CANDIDATE",native_id_mapping_complete=False,decoder_parity_confirmed=False,atlas_uv_confirmed=False)
    for table in ("source","member","texture","mapping"):
        cur=db.execute("SELECT * FROM "+table+" ORDER BY "+("path" if table=="source" else "blob,member_index"+(",texture_index" if table in ("texture","mapping") else "")))
        cols=[d[0] for d in cur.description]
        with (out/"manifests"/(table+".jsonl")).open("w",encoding="utf-8") as f:
            for row in cur: f.write(json.dumps(dict(zip(cols,row)),ensure_ascii=True)+"\n")
    db.commit(); db.close(); (out/"manifests"/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2))
    if not counts["parsed_unique_blobs"]: raise SystemExit("No sources parsed")

def self_test():
    b=bytearray(84); b[:4]=b"SARC"; struct.pack_into("<HHIII",b,4,20,0xfeff,len(b),80,0x100)
    b[20:24]=b"SFAT"; struct.pack_into("<HHI",b,24,12,1,101); struct.pack_into("<IIII",b,32,120,0x1000000,0,4)
    b[48:52]=b"SFNT"; struct.pack_into("<HH",b,52,8,0); b[56:58]=b"x\0"; b[80:84]=b"test"
    m,p=next(sarc(b)); assert m["name"]=="x" and m["name_hash_matches"] and p==b"test"
    bad=bytearray(b); struct.pack_into("<I",bad,44,5)
    try: list(sarc(bad)); raise AssertionError("bounds accepted")
    except ValueError: pass
    for fmt,channels,block,expected in [("0x1D01",[1,1,1,2],bytes([128,128])+bytes(6),(255,255,255,128)),("0x1E01",[2,2,2,3],bytes([64,64])+bytes(6)+bytes([192,192])+bytes(6),(64,64,64,192))]:
        r=dict(format_code=fmt,depth=1,array_count=1,mip_count=1,storage_dim=2,image_dim=1,tile_mode=0,swizzle=0,block_height_log2=0,width=4,height=4,channels=channels,mip_offsets=[0],image_size=512)
        im,blocks=decode(block+bytes(512-len(block)),r); assert blocks==block and im.getpixel((0,0))==expected,(fmt,im.getpixel((0,0)))
    assert classify("ui/data/dummy/dummy_icon_type.arc","grptxt_icon_type_00_normal_00^s")=="types"
    print("SARC bounds, BC4/BC5 channel fixtures and category tests passed")
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--self-test",action="store_true"); p.add_argument("--ref",default="HEAD"); p.add_argument("--out",type=Path,default=Path(".za-work/ZAImageResources")); p.add_argument("--export",action="store_true",help="local PNG only; verify rights before use")
    a=p.parse_args()
    if a.self_test: self_test(); return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()): p.error("output must be inside .za-work")
    ref=subprocess.check_output(["git","rev-parse",a.ref+"^{commit}"],text=True).strip(); run(a.out,ref,a.export)
if __name__=="__main__": main()
