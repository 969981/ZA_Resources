#!/usr/bin/env python3
"""Restricted isolated-pane color reconstruction hypotheses, NOT a native renderer."""
import argparse, collections, importlib.util, json, struct, hashlib
from pathlib import Path
from PIL import Image, ImageChops
spec=importlib.util.spec_from_file_location("material",Path(__file__).with_name("Audit-ZA-NativeMaterials.py"))
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
layout=native.layout;pack=native.pack
SAMPLES=["dummy/dummy_icon_type.arc","hud_ball/hud_ball_00.arc","btl_app/btl_app_trainer_ball_00.arc","btl_app/btl_app_waza_last_01.arc","btl_app/btl_app_hit_marker_00.arc","quest_info/resident_ui.arc"]
def mul(a,b):return (a*b+127)//255
def render(im,colors,vertex=(255,255,255,255),alpha=255,model="endpoint"):
    """Explicit hypothesis: per-channel interpolation or simple modulation in stored-byte space."""
    lo,hi=colors
    if model not in ("endpoint","multiply"):raise ValueError("model")
    bands=[]
    for i,band in enumerate(im.convert("RGBA").split()):
        lut=[]
        for x in range(256):
            y=mul(x,hi[i]) if model=="multiply" else (lo[i]*(255-x)+hi[i]*x+127)//255
            y=mul(y,vertex[i])
            if i==3:y=mul(y,alpha)
            lut.append(y)
        bands.append(band.point(lut))
    return Image.merge("RGBA",bands)
def material_rows(b):
    out=[]
    for tag,off,s,e in layout.sections(b):
        if tag!="mat1":continue
        u=layout.reader(s,e);n=u("H",8);layout.need(s,12,4*n)
        offsets=[u("I",12+4*i) for i in range(n)]+[len(s)]
        for a,z in zip(offsets,offsets[1:]):
            if a<12+4*n or z<a or z>len(s):raise ValueError("material bounds")
            out.append(native.material(s[a:z],e))
    return out
def eligibility(m,p,pane):
    if m["status"]!="BOUNDARY_FIT_CANDIDATE":return "PARTIAL_MATERIAL"
    if m["flags"]!=0x15:return "UNSUPPORTED_FLAGS"
    if len(m.get("maps",[]))!=1 or len(p["texture_names"])!=1:return "NOT_SINGLE_TEXTURE"
    if p["uv_kind"]!="FULL":return "NON_FULL_UV"
    s=m.get("srt",[])
    if len(s)!=1 or s[0]["translation"]!=[0,0] or s[0]["rotation"]!=0 or s[0]["scale"]!=[1,1]:return "NON_IDENTITY_SRT"
    v=bytes.fromhex(p["vertex_colors"])
    if len(v)!=16 or any(v[:4]!=v[i:i+4] for i in (4,8,12)):return "NON_UNIFORM_VERTEX"
    if m.get("coord_raw")!=["00000000000000000000000000000000"]:return "UNVERIFIED_COORD"
    if m["maps"][0]["u_options"]!=4 or m["maps"][0]["v_options"]!=4:return "UNVERIFIED_SAMPLER"
    return "ISOLATED_COLOR_CANDIDATE"
def audit(out,export=False,all_arcs=False):
    out.mkdir(parents=True,exist_ok=True);counts=collections.Counter();groups=collections.defaultdict(set); examples=[]
    paths=sorted((pack.ROOT/"ui/data").rglob("*.arc")) if all_arcs else [pack.ROOT/"ui/data"/x for x in SAMPLES];seen=set()
    with (out/"recipes.jsonl").open("w",encoding="utf-8") as f:
        def emit(r):f.write(json.dumps(r,ensure_ascii=True,allow_nan=False)+"\n")
        for path in paths:
            counts["arc_paths"]+=1
            try:
                b=path.read_bytes();digest=pack.sha(b)
                if digest in seen:counts["arc_aliases"]+=1;continue
                seen.add(digest);members=list(pack.sarc(b));textures=collections.defaultdict(list);decoded={}
                for m,t in members:
                    if t[:4]==b"BNTX":
                        for tr in pack.bntx.parse(t):textures[tr["name"]].append((m,t,tr))
                for m,raw in members:
                    if raw[:4]!=b"FLYT":continue
                    try:
                        d=layout.flyt(raw);mats=material_rows(raw)
                        for p in d["pictures"]:
                            counts["pictures"]+=1;mi=p["material_index"];pane=d["panes"][p["pane_index"]]
                            if mi>=len(mats):counts["MATERIAL_MISSING"]+=1;continue
                            mat=mats[mi];status=eligibility(mat,p,pane);counts[status]+=1
                            if status!="ISOLATED_COLOR_CANDIDATE":continue
                            name=p["texture_names"][0];xs=textures.get(name,[])
                            if len(xs)!=1:counts["TEXTURE_NOT_UNIQUE"]+=1;continue
                            mem,t,tr=xs[0];k=(mem["index"],tr["index"])
                            if k not in decoded:decoded[k]=pack.decode(t,tr)[0]
                            im=decoded[k];v=tuple(bytes.fromhex(p["vertex_colors"])[:4]);a=pane["alpha"]
                            colors=mat["colors"];row=dict(path=path.relative_to(pack.ROOT).as_posix(),arc_sha256=digest,layout=m["name"],pane=p["name"],material=mat["name"],material_sha256=mat["record_sha256"],texture=name,texture_member=mem["name"],texture_index=tr["index"],texture_storage_sha256=tr["storage_sha256"],width=im.width,height=im.height,source_rgba_sha256=pack.sha(im.tobytes()),colors=colors,vertex=v,pane_alpha=a,models={},status="ISOLATED_COLOR_HYPOTHESIS",native_render_verified=False)
                            for model in ("multiply","endpoint"):
                                image=render(im,colors,v,a,model);h=pack.sha(image.tobytes());groups[model].add((image.width,image.height,h))
                                row["models"][model]=h
                                if h!=row["source_rgba_sha256"]:counts["changed:"+model]+=1
                                if export:
                                    dest=out/"png"/model/(f"{image.width}x{image.height}-{h}.png");dest.parent.mkdir(parents=True,exist_ok=True)
                                    if not dest.exists():image.save(dest)
                            if row["models"]["multiply"]!=row["models"]["endpoint"]:counts["models_disagree"]+=1
                            counts["rendered_recipes"]+=1
                            if len(examples)<10 and row["models"]["endpoint"]!=row["source_rgba_sha256"]:examples.append({k:row[k] for k in ("path","pane","texture","colors","vertex","pane_alpha","models")})
                            emit(row)
                    except Exception as ex:counts["layout_errors"]+=1;emit(dict(path=str(path),member=m["name"],error=str(ex)))
            except Exception as ex:counts["arc_errors"]+=1;emit(dict(path=str(path),error=str(ex)))
    for m,g in groups.items():counts["unique:"+m]=len(g)
    result=dict(scope="all raw checkout ARC" if all_arcs else "six sample ARC",counts=dict(counts),png_export=export,examples=examples,native_render_verified=False,limitations=["no GPU shader or framebuffer comparison","no parent alpha, panel geometry, texture filtering, SRT, multi-layer, blend or font rendering","texture-size isolated candidates, not final screen pixels","stored-byte space; no sRGB conversion"])
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,indent=2))
    if not counts["rendered_recipes"]:raise SystemExit("no eligible candidate recipes")
def self_test():
    im=Image.new("RGBA",(1,1),(255,255,255,128))
    assert render(im,[[0,0,0,0],[255,0,0,255]],alpha=128).getpixel((0,0))==(255,0,0,64)
    assert render(im,[[0,0,0,0],[255,255,255,255]]).tobytes()==im.tobytes()
    assert render(Image.new("RGBA",(1,1),(0,0,0,255)),[[20,30,40,0],[255,255,255,255]],model="endpoint").getpixel((0,0))==(20,30,40,255)
    print("isolated modulation and endpoint interpolation fixtures passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--out",type=Path,default=Path(".za-work/ui-render"));p.add_argument("--export",action="store_true");p.add_argument("--all-arcs",action="store_true");a=p.parse_args()
    if a.self_test:self_test();return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()):p.error("local output only")
    audit(a.out,a.export,a.all_arcs)
if __name__=="__main__":main()
