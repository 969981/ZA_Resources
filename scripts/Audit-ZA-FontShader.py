#!/usr/bin/env python3
"""Read-only native font container and shader path inventory; never exports fonts."""
import argparse, collections, hashlib, json, re, struct, subprocess
from pathlib import Path
ROOT=Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual")
def sha(b):return hashlib.sha256(b).hexdigest()
def header(b,magic):
    if len(b)<20 or b[:4]!=magic:raise ValueError("magic")
    e={b"\xff\xfe":"<",b"\xfe\xff":">"}.get(b[4:6])
    if not e:raise ValueError("BOM")
    h,ver,size,n,_=struct.unpack_from(e+"HIIHH",b,6)
    if size!=len(b) or not 20<=h<=size:raise ValueError("header bounds")
    return e,h,ver,n
def names(b):
    return [dict(offset=m.start(),name=m.group().decode("ascii")) for m in re.finditer(rb"[A-Za-z0-9_.-]+\.(?:bffnt|bfttf|bfotf|otf|ttf|fcpx)",b)]
def fcpx(b):
    e,h,ver,n=header(b,b"FCPX")
    if ver!=0x09030000 or h!=20:raise ValueError("unsupported FCPX version")
    u=lambda o:struct.unpack_from(e+"I",b,o)[0]
    mode=u(24); refs=names(b); out=dict(version=f"{ver:08x}",mode_raw=mode,section_count_raw=n,names=refs,body_sha256=sha(b[h:]),status="RAW_REFERENCE_SCAN")
    # Native samples show offsets relative to +0x18 for both modes.
    if mode==0:
        if u(28)+24>=len(b):raise ValueError("bitmap name offset")
        offsets=[28,36]
    elif mode==1:
        count=u(36)
        if count>1024 or 56+40*count>len(b):raise ValueError("font record bounds")
        out["point_size_candidate"]=struct.unpack_from(e+"f",b,28)[0]
        out["font_count_candidate"]=count
        offsets=[o for i in range(count) for o in (68+40*i,92+40*i)]
    else:return out
    byoff={x["offset"]:x["name"] for x in refs}
    out["offset_references"]=[dict(field=o,relative=u(o),absolute=u(o)+24,name=byoff.get(u(o)+24)) for o in offsets if o+4<=len(b)]
    out["status"]="REFERENCE_OFFSETS_MATCH" if out["offset_references"] and all(x["name"] for x in out["offset_references"]) else "PARTIAL_REFERENCE_OFFSETS"
    return out
def ffnt(b):
    e,h,ver,n=header(b,b"FFNT");out=[];widths=[];mapping=[];seen=set()
    u=lambda f,o:struct.unpack_from(e+f,b,o)
    for _ in range(n):
        if h+8>len(b):raise ValueError("section header")
        tag=b[h:h+4].decode("ascii");sz=u("I",h+4)[0]
        if sz<8 or h+sz>len(b):raise ValueError("section bounds")
        s=b[h:h+sz];d=dict(tag=tag,offset=h,size=sz,sha256=sha(s))
        if tag=="CWDH":
            if sz<16:raise ValueError("CWDH header")
            a,z,nxt=u("HHI",h+8)
            if z<a or 16+3*(z-a+1)>sz:raise ValueError("CWDH bounds")
            d.update(first=a,last=z,next_offset=nxt)
            for i in range(z-a+1):
                l,w,adv=struct.unpack_from("bBb",s,16+3*i);widths.append(dict(glyph=a+i,left=l,width=w,advance=adv))
        elif tag=="CMAP":
            if sz<20:raise ValueError("CMAP header")
            a,z,method,res,nxt=u("IIHHI",h+8);d.update(first=a,last=z,method=method,next_offset=nxt)
            if z<a or z>0x10ffff:raise ValueError("CMAP range")
            if method==0:
                if sz<26:raise ValueError("direct CMAP bounds")
                start=u("H",h+24)[0]
                if z-a>65535:raise ValueError("direct range")
                for cp in range(a,z+1):mapping.append(dict(codepoint=cp,glyph=start+cp-a,method=0))
            elif method==1:
                if 24+2*(z-a+1)>sz:raise ValueError("table CMAP bounds")
                for i in range(z-a+1):
                    g=u("H",h+24+2*i)[0]
                    if g!=65535:mapping.append(dict(codepoint=a+i,glyph=g,method=1))
            elif method==2:
                if sz<28:raise ValueError("scan CMAP bounds")
                count=u("H",h+24)[0]
                # FFNT v4 sparse entries use u32 codepoint and u16 glyph with two padding bytes.
                if 28+8*count>sz:raise ValueError("scan CMAP bounds")
                for i in range(count):
                    cp,g,pad=u("IHH",h+28+8*i);mapping.append(dict(codepoint=cp,glyph=g,method=2,padding=pad))
            else:d["unsupported_method"]=True
        out.append(d);h+=sz
    if h!=len(b):raise ValueError("trailing bytes")
    return dict(version=f"{ver:08x}",sections=out,widths=widths,mappings=mapping,duplicate_codepoints=len(mapping)-len({x["codepoint"] for x in mapping}),glyph_texture_verified=False)
def audit(out,ref):
    out.mkdir(parents=True,exist_ok=True);counts=collections.Counter();fonts=[];shader=[]
    paths=subprocess.check_output(["git","ls-tree","-rz","--name-only",ref],text=False).decode("utf-8").split("\0")
    pfx=ROOT.as_posix()+"/";fontpaths=[p for p in paths if p.startswith(pfx+"ui/font/bin/")];available={Path(p).name for p in fontpaths}
    for p in fontpaths:
        path=Path(p);counts["font:"+path.suffix]+=1
        try:
            b=path.read_bytes();row=dict(path=p,size=len(b),sha256=sha(b),magic=b[:4].hex())
            if path.suffix==".bfcpx":
                row.update(fcpx(b));counts[row["status"]]+=1
                for x in row["names"]:
                    n=x["name"]; candidates=[n]
                    if n.endswith(".otf"):candidates.append(n[:-4]+".bfotf")
                    x["local_filename_candidates"]=[v for v in candidates if v in available]
                    if not x["local_filename_candidates"]:counts["external_font_reference"]+=1
            elif path.suffix==".bffnt":
                row.update(ffnt(b));counts["ffnt_parsed"]+=1;counts["glyph_width_records"]+=len(row["widths"]);counts["codepoint_records"]+=len(row["mappings"])
            else:row["names"]=names(b) if path.name=="font_settings.bin" else []
            fonts.append(row)
        except Exception as ex:counts["font_errors"]+=1;fonts.append(dict(path=p,error=str(ex)))
    for p in paths:
        if not p:continue
        n=Path(p).name.lower()
        if re.search(r"shader|bfsha|bfs[c-h]|sharc|shbin|\.spv$|\.glsl$",n) or "/shader/" in p.lower():
            shader.append(p);counts["shader_path_candidate"]+=1
    result=dict(source_commit=ref,counts=dict(counts),font_files=fonts,shader_path_candidates=shader,shader_ui_binding_verified=False,font_glyph_render_verified=False)
    (out/"inventory.json").write_text(json.dumps(result,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
    print(json.dumps(dict(counts=dict(counts),font_errors=[x for x in fonts if "error" in x],shader_sample=shader[:30],external_names=sorted({n["name"] for x in fonts for n in x.get("names",[]) if "local_filename_candidates" in n and not n["local_filename_candidates"]})),indent=2))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--ref",default="HEAD");p.add_argument("--out",type=Path,default=Path(".za-work/ui-font-shader"));a=p.parse_args()
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("local output only")
    ref=subprocess.check_output(["git","rev-parse",a.ref+"^{commit}"],text=True).strip();audit(a.out,ref)
if __name__=="__main__":main()
