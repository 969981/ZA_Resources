#!/usr/bin/env python3
"""Audit font sheet arrays, independent BC4 pixels, and glyph-grid hypotheses."""
import argparse, collections, importlib.util, json, struct, math
from pathlib import Path
from PIL import Image
def load(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
font=load("font","Audit-ZA-FontShader.py");pack=load("pack","Build-ZAImageResources.py")
def decode_bc4(blocks,w,h):
    im=Image.new("L",(w,h));p=im.load();bw=(w+3)//4
    for y in range((h+3)//4):
        for x in range(bw):
            b=blocks[(y*bw+x)*8:(y*bw+x+1)*8];a,z=b[:2];bits=int.from_bytes(b[2:],"little")
            table=[a,z]+([( (7-i)*a+i*z)//7 for i in range(1,7)] if a>z else [((5-i)*a+i*z)//5 for i in range(1,5)]+[0,255])
            for j in range(16):
                xx=x*4+j%4;yy=y*4+j//4
                if xx<w and yy<h:p[xx,yy]=table[(bits>>(3*j))&7]
    return im
def get_sheets(b):
    e,h,v,n=font.header(b,b"FFNT");u=lambda f,o:struct.unpack_from(e+f,b,o)[0]
    for _ in range(n):
        size=u("I",h+4)
        if size<8 or h+size>len(b):raise ValueError("section bounds")
        if b[h:h+4]!=b"TGLP":h+=size;continue
        cw,ch,count,mw=b[h+8:h+12];length=u("I",h+12);base=u("I",h+28);end=h+size
        if not h+32<=base<=end-88:raise ValueError("TGLP pointer")
        declared=u("I",base+28)
        if not 88<=declared<=end-base:raise ValueError(f"BNTX length {declared} section available {end-base}")
        payload=b[base:base+declared];rs=pack.bntx.parse(payload)
        meta=dict(tglp_offset=h,cell=[cw,ch],count=count,max_width=mw,per_sheet_length_raw=length,container_length=declared,section_available=end-base,tail_length=end-base-declared,grid=[u("H",h+20),u("H",h+22)],size=[u("H",h+24),u("H",h+26)],textures=rs)
        images=[];parity=[]
        for r in rs:
            if r["format_code"]!="0x1D01" or r["channels"]!=[1,1,1,2] or r["image_dim"]!=5 or r["depth"]!=1 or r["mip_count"]!=1 or r["tile_mode"]!=0:raise ValueError("unsupported sheet format")
            w,ht=r["width"],r["height"]
            if [w,ht]!=meta["size"]:raise ValueError("dimension mismatch")
            layers=r["array_count"]
            if layers<=0 or r["image_size"]%layers:raise ValueError("array storage size")
            stride=r["image_size"]//layers;bw,bh=(w+3)//4,(ht+3)//4;pitch=((bw*8+63)//64)*64;gob=1<<r["block_height_log2"];expected=pitch*((bh+8*gob-1)//(8*gob))*8*gob
            if stride!=expected:raise ValueError(f"array stride {stride} != expected {expected}")
            for layer in range(layers):
                start=r["mip_offsets"][0]+stride*layer
                if start+stride>len(payload):raise ValueError("layer bounds")
                rr=dict(r,image_dim=1,array_count=1,image_size=stride,mip_offsets=[start])
                im,blocks=pack.decode(payload,rr);alpha=im.getchannel("A");other=decode_bc4(blocks,w,ht)
                dif=[abs(x-y) for x,y in zip(alpha.tobytes(),other.tobytes())]
                parity.append(dict(texture=r["index"],layer=layer,storage_stride=stride,sha256=pack.sha(alpha.tobytes()),independent_sha256=pack.sha(other.tobytes()),different=sum(x!=0 for x in dif),max_error=max(dif),pixels=len(dif)))
                images.append(alpha)
        if len(images)!=count:raise ValueError(f"sheet count {count} decoded {len(images)}")
        meta["parity"]=parity;return images,meta
    raise ValueError("no TGLP")
def crop(sheets,meta,gi,mode,gap,border):
    cols,rows=meta["grid"];w,h=meta["cell"];layer,idx=divmod(gi,cols*rows)
    if layer>=len(sheets):return None
    if mode.startswith("row"):col,row=idx%cols,idx//cols
    else:col,row=idx//rows,idx%rows
    if "flip" in mode:row=rows-1-row
    x=border+col*(w+gap);y=border+row*(h+gap);im=sheets[layer]
    if not (0<=x<x+w<=im.width and 0<=y<y+h<=im.height):return None
    g=im.crop((x,y,x+w,y+h))
    if "flip" in mode:g=g.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return g,[x,y,x+w,y+h],layer
def audit(out):
    out.mkdir(parents=True,exist_ok=True);counts=collections.Counter();result=[]
    for p in sorted((font.ROOT/"ui/font/bin").glob("*.bffnt")):
        try:
            b=p.read_bytes();m=font.ffnt(b);sheets,meta=get_sheets(b);metrics={x["glyph"]:x for x in m["widths"]};maps={x["codepoint"]:x["glyph"] for x in m["mappings"]}
            scores=[];counts["fonts"]+=1;counts["sheets"]+=len(sheets)
            for q in meta["parity"]:counts["bc4_pixels"]+=q["pixels"];counts["bc4_different"]+=q["different"];counts["bc4_max_error"]=max(counts["bc4_max_error"],q["max_error"])
            for mode in ("row","column","row_flip","column_flip"):
                for gap,border in ((0,0),(1,0),(1,1),(2,1)):
                    hits=0;digit_hits=0;spaces=0;width_error=0;edge_hits=0;valid=0;digit_details=[]
                    for cp,gi in maps.items():
                        v=crop(sheets,meta,gi,mode,gap,border)
                        if v is None:continue
                        im,box,layer=v;bb=im.getbbox();valid+=1;w=metrics.get(gi,{}).get("width")
                        if cp==32 and not bb:spaces+=1
                        if bb:
                            hits+=1
                            if w is not None:width_error+=abs((bb[2]-bb[0])-w)
                            if bb[0]==0 or bb[1]==0 or bb[2]==im.width or bb[3]==im.height:edge_hits+=1
                        if 48<=cp<=57:
                            if bb:digit_hits+=1
                            digit_details.append(dict(codepoint=cp,glyph=gi,layer=layer,box=box,bbox=bb,width_metric=w,alpha_sha256=pack.sha(im.tobytes())))
                    scores.append(dict(mode=mode,gap=gap,border=border,valid=valid,nonempty=hits,digits=digit_hits,empty_space=spaces,width_error=width_error,edge_hits=edge_hits,digit_details=digit_details))
            # Rank diagnostics only; no auto promote from occupancy.
            ranks=sorted(scores,key=lambda s:(-s["digits"],-s["empty_space"],-s["valid"],s["width_error"],s["edge_hits"]))
            result.append(dict(path=p.name,sha256=pack.sha(b),**meta,candidates=ranks,native_uv_verified=False))
            print(json.dumps(dict(font=p.name,count=meta["count"],container=meta["container_length"],per_sheet_raw=meta["per_sheet_length_raw"],parity=meta["parity"],top=[{k:v for k,v in s.items() if k!="digit_details"} for s in ranks[:3]])))
        except Exception as ex:counts["errors"]+=1;result.append(dict(path=p.name,error=str(ex)));print(p.name,str(ex))
    (out/"glyph-uv.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(counts=dict(counts),native_uv_verified=False),indent=2))
    if counts["fonts"]!=8:raise SystemExit("font array validation incomplete")
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=Path(".za-work/glyph-uv"));a=p.parse_args()
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("local output only")
    audit(a.out)
if __name__=="__main__":main()
