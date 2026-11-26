#!/usr/bin/env python3
"""Decode embedded font BNTX sheets; glyph cell and text composition are candidates."""
import argparse, collections, hashlib, importlib.util, json, struct
from pathlib import Path
from PIL import Image
def load(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
font=load("font","Audit-ZA-FontShader.py");pack=load("pack","Build-ZAImageResources.py")
def sheet(b):
    e,h,v,n=font.header(b,b"FFNT");u=lambda f,o:struct.unpack_from(e+f,b,o)[0]
    for i in range(n):
        tag=b[h:h+4];size=u("I",h+4)
        if size<8 or h+size>len(b):raise ValueError("section bounds")
        if tag==b"TGLP":
            if size<32:raise ValueError("TGLP header")
            cellw,cellh,sheets,maxw=b[h+8:h+12]
            length=u("I",h+12);base=u("I",h+28)
            if not h+32<=base<base+length<=h+size:raise ValueError("sheet bounds")
            declared=u("I",base+28)
            if not 88<=declared<=length:raise ValueError(f"embedded BNTX bounds: declared={declared} TGLP={length}")
            payload=b[base:base+declared];tail=b[base+declared:base+length];rs=pack.bntx.parse(payload)
            if sheets!=1 or len(rs)!=1:raise NotImplementedError("multiple sheets")
            r=rs[0];w,height=u("H",h+24),u("H",h+26)
            if (r["width"],r["height"])!=(w,height):raise ValueError("sheet dimensions")
            if r["format_code"]!="0x1D01" or r["channels"]!=[1,1,1,2] or r["image_dim"]!=5:raise NotImplementedError("unexpected font texture")
            # NX 2D-array view with exactly one layer: use same block linear storage as 2D.
            if r["array_count"]!=1 or r["depth"]!=1:raise NotImplementedError("font array")
            im,blocks=pack.decode(payload,dict(r,image_dim=1))
            return im,dict(tglp_offset=h,embedded_bntx_offset=base,embedded_bntx_sha256=pack.sha(payload),tglp_length=length,bntx_declared_length=declared,tail_length=len(tail),tail_sha256=pack.sha(tail),tail_nonzero=sum(x!=0 for x in tail),linear_blocks_sha256=pack.sha(blocks),texture=r,cell_width=cellw,cell_height=cellh,sheet_count=sheets,max_width_raw=maxw,field_0x10=u("H",h+16),format_raw=u("H",h+18),columns=u("H",h+20),rows=u("H",h+22))
        h+=size
    raise ValueError("missing TGLP")
def crop(im,info,glyph):
    cols,rows=info["columns"],info["rows"];w,h=info["cell_width"],info["cell_height"]
    if cols<=0 or rows<=0 or not 0<=glyph<cols*rows:raise ValueError("glyph capacity")
    # one-pixel border and gap candidate: no native sampling reference yet.
    x=1+(glyph%cols)*(w+1);y=1+(glyph//cols)*(h+1)
    if x+w>im.width or y+h>im.height:raise ValueError("glyph bounds")
    return im.crop((x,y,x+w,y+h)),[x,y,x+w,y+h]
def candidate_box(im,info,glyph,mode,gap,border):
    cols,rows=info["columns"],info["rows"];w,h=info["cell_width"],info["cell_height"]
    if mode=="row":col,row=glyph%cols,glyph//cols
    elif mode=="column":col,row=glyph//rows,glyph%rows
    elif mode=="row_flip":col,row=glyph%cols,rows-1-glyph//cols
    else:col,row=glyph//rows,rows-1-glyph%rows
    x=border+col*(w+gap);y=border+row*(h+gap)
    if not (0<=x<x+w<=im.width and 0<=y<y+h<=im.height):return None
    return im.getchannel("A").crop((x,y,x+w,y+h)).getbbox()
def audit(out,export=False):
    out.mkdir(parents=True,exist_ok=True);counts=collections.Counter();records=[];glyphs=[]
    for p in sorted((font.ROOT/"ui/font/bin").glob("*.bffnt")):
        try:
            b=p.read_bytes();m=font.ffnt(b);im,info=sheet(b);widths={x["glyph"]:x for x in m["widths"]};maps=collections.defaultdict(list)
            for x in m["mappings"]:maps[x["codepoint"]].append(x["glyph"])
            scores={}
            for mode in ("row","column","row_flip","column_flip"):
                for gap,border in ((0,0),(1,0),(1,1),(2,1)):
                    hits=0
                    for cp in range(48,58):
                        gs=maps.get(cp,[])
                        if len(set(gs))==1 and candidate_box(im,info,gs[0],mode,gap,border):hits+=1
                    scores[f"{mode}:gap{gap}:border{border}"]=hits
            row=dict(digit_candidate_nonempty=scores,path=p.name,source_sha256=pack.sha(b),sheet_rgba_sha256=pack.sha(im.tobytes()),sheet_alpha_extrema=im.getchannel("A").getextrema(),**info,layout_candidate_verified=False);records.append(row);counts["decoded_sheets"]+=1
            if export:
                d=out/"png"/p.stem;d.mkdir(parents=True,exist_ok=True);im.save(d/"sheet.png")
            for cp,gs in sorted(maps.items()):
                counts["codepoint_groups"]+=1
                if len(set(gs))!=1:counts["ambiguous_codepoints"]+=1;continue
                gi=gs[0]
                if gi not in widths:counts["missing_width"]+=1;continue
                try:
                    g,box=crop(im,info,gi);alpha=g.getchannel("A");bbox=alpha.getbbox();counts["glyph_crops"]+=1
                    if bbox:counts["nonempty_glyphs"]+=1
                    glyphs.append(dict(font=p.name,codepoint=cp,glyph=gi,metrics=widths[gi],box=box,alpha_bbox=bbox,rgba_sha256=pack.sha(g.tobytes()),status="CELL_CROP_CANDIDATE"))
                    if 48<=cp<=57:
                        counts["digit_crops"]+=1
                        if bbox:counts["nonempty_digits"]+=1
                        if export:g.save(d/f"U+{cp:04X}.png")
                except Exception as ex:counts["crop_errors"]+=1;glyphs.append(dict(font=p.name,codepoint=cp,glyph=gi,error=str(ex)))
        except Exception as ex:counts["sheet_errors"]+=1;records.append(dict(path=p.name,error=str(ex)))
    (out/"sheets.json").write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8");(out/"glyphs.jsonl").write_text("".join(json.dumps(g)+"\n" for g in glyphs),encoding="utf-8")
    summary=dict(counts=dict(counts),errors=[r for r in records if "error" in r],sheets=[dict(path=r["path"],width=r["texture"]["width"],height=r["texture"]["height"],cell=[r["cell_width"],r["cell_height"]],grid=[r["columns"],r["rows"]],alpha=r["sheet_alpha_extrema"],tail_length=r["tail_length"],tail_nonzero=r["tail_nonzero"],digit_candidate_nonempty=r["digit_candidate_nonempty"]) for r in records if "texture" in r],native_glyph_sampling_verified=False,png_export=export)
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8");print(json.dumps(summary,indent=2))
    if counts["decoded_sheets"]!=8:raise SystemExit("expected eight native bitmap sheets")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--out",type=Path,default=Path(".za-work/font-glyphs"));p.add_argument("--export",action="store_true");a=p.parse_args()
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("local output only")
    audit(a.out,a.export)
if __name__=="__main__":main()
