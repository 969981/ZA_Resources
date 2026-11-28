#!/usr/bin/env python3
"""Textured Bulbasaur GLB V2: mip-aware BNTX and reference-shader base-color bake.
No original shader/visual parity claim. All generated game assets stay local.
"""
import argparse, hashlib, importlib.util, io, json, math, struct, subprocess
from pathlib import Path
import numpy as np
from PIL import Image

def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v1=load("ZANativeModelExporter")
audit=v1.audit
geo=v1.geo
bntx=load("Decode-ZA-BNTX")
BC={0x1a:(8,b"DXT1"),0x1b:(16,b"DXT3"),0x1c:(16,b"DXT5"),0x1d:(8,b"BC4U"),0x1e:(16,b"BC5U"),0x20:(16,b"DX10")}
def sha(b):return hashlib.sha256(b).hexdigest()
def srgb_to_linear(a):return np.where(a<=0.04045,a/12.92,((a+0.055)/1.055)**2.4)
def linear_to_srgb(a):
    a=np.clip(a,0,1)
    return np.where(a<=0.0031308,a*12.92,1.055*a**(1/2.4)-0.055)
def mip_layout(r,level):
    if not 0<=level<r["mip_count"]:raise ValueError("mip index")
    if (r["depth"],r["array_count"],r["storage_dim"],r["image_dim"],r["tile_mode"],r["swizzle"])!=(1,1,2,1,0,0):raise NotImplementedError("non-2D block linear layout")
    fmt=int(r["format_code"],16);kind=fmt>>8
    if kind not in BC or (fmt&255) not in (1,6) or ((fmt&255)==6 and kind not in (0x1a,0x1b,0x1c,0x20)):raise NotImplementedError("format "+r["format_code"])
    if not 0<=r["block_height_log2"]<=5:raise ValueError("block height")
    w=max(1,r["width"]>>level);h=max(1,r["height"]>>level)
    if w*h>16777216:raise ValueError("oversized texture")
    bw,bh=(w+3)//4,(h+3)//4;bs=BC[kind][0];block_height=1<<r["block_height_log2"]
    # Standard Tegra GOB height reduction candidate; validate full mip span.
    while block_height>1 and bh<=8*(block_height//2):block_height//=2
    pitch=((bw*bs+63)//64)*64
    offsets=r["mip_offsets"]
    if sorted(set(offsets))!=offsets:raise ValueError("mip offsets not strictly increasing")
    start=offsets[level];end=offsets[level+1] if level+1<len(offsets) else offsets[0]+r["image_size"]
    padded=pitch*((bh+8*block_height-1)//(8*block_height))*8*block_height
    if end-start<padded:raise ValueError("mip GOB span too short")
    return dict(level=level,width=w,height=h,block_width=bw,block_rows=bh,block_bytes=bs,pitch=pitch,block_height=block_height,start=start,end=end,padded_bytes=padded,kind=kind,format=fmt)
def decode_mip(raw,r,level):
    m=mip_layout(r,level);w,h=m["width"],m["height"];bs=m["block_bytes"];kind=m["kind"]
    if m["end"]>len(raw):raise ValueError("mip span outside source")
    blocks=bytearray()
    for y in range(m["block_rows"]):
        for x in range(m["block_width"]):
            o=m["start"]+bntx.gob_offset(x*bs,y,m["pitch"],m["block_height"])
            if o+bs>m["end"]:raise ValueError("GOB outside mip")
            blocks.extend(raw[o:o+bs])
    cc=BC[kind][1]
    hdr=[124,0x81007,h,w,len(blocks),0,1]+[0]*11+[32,4,int.from_bytes(cc,"little"),0,0,0,0,0,0x1000,0,0,0,0]
    dds=b"DDS "+struct.pack("<31I",*hdr)
    if kind==0x20:dds+=struct.pack("<5I",99 if m["format"]&255==6 else 98,3,0,1,0)
    with Image.open(io.BytesIO(dds+blocks)) as im:
        im.load()
        if im.size!=(w,h):raise ValueError("pixel dimensions")
        # BC4/5 physically encode one/two channels. Missing GPU channels are
        # represented as zero and one, not treated as extra compressed channels.
        if kind==0x1d:
            red=im.convert("RGB").getchannel("R");bands=[red,Image.new("L",im.size,0),Image.new("L",im.size,0),Image.new("L",im.size,255)]
        elif kind==0x1e:
            rgb=im.convert("RGB");bands=[rgb.getchannel("R"),rgb.getchannel("G"),Image.new("L",im.size,0),Image.new("L",im.size,255)]
        else:bands=list(im.convert("RGBA").split())
        channels=[Image.new("L",im.size,0),Image.new("L",im.size,255),*bands]
        if any(c not in range(6) for c in r["channels"]):raise NotImplementedError("channel selector")
        rgba=Image.merge("RGBA",[channels[c] for c in r["channels"]])
    m.update(linear_blocks_sha256=sha(blocks),rgba_sha256=sha(rgba.tobytes()),color_space="SRGB" if m["format"]&255==6 else "UNORM",status="DECODED_CANDIDATE")
    return rgba,m
def read_texture(path,paths,cache,report):
    if path in cache:return cache[path]
    raw=audit.checked(path,paths);rs=bntx.parse(raw)
    if len(rs)!=1:raise ValueError("sample expects single BRTI")
    r=rs[0];mips=[];top=None
    for i in range(r["mip_count"]):
        im,m=decode_mip(raw,r,i);mips.append(m)
        if i==0:top=im
    row=dict(path=path,git_blob=paths[path],source_sha256=sha(raw),brti=r,mips=mips)
    report.append(row);cache[path]=(top,r);return cache[path]
def resize_float(a,size):
    if a.shape[:2]==(size[1],size[0]):return a
    return np.stack([np.asarray(Image.fromarray(a[:,:,i].astype(np.float32)).resize(size,Image.Resampling.BILINEAR),dtype=np.float64) for i in range(a.shape[2])],axis=2)
def pixels(im,r,color=False):
    a=np.asarray(im,dtype=np.float64)/255
    if color and int(r["format_code"],16)&255==6:a[:,:,:3]=srgb_to_linear(a[:,:,:3])
    return a
def rgba_image(a):return Image.fromarray(np.rint(np.clip(a,0,1)*255).astype(np.uint8))
def bake(base,mask,mat):
    opts=mat["shaders"][0]["values"];fp=mat["float_parameters"];p=mat["rgba"]
    count=int(opts["NumMaterialLayer"])
    if not 1<=count<=5:raise ValueError("layer count")
    multiply=opts.get("BaseColorMultiply","False")=="True"
    w=np.clip(mask*np.array([fp.get("LayerMaskScale"+str(i),1.0) for i in range(1,5)]),0,1)
    for i in range(count-1,4):w[:,:,i]=0
    result=base[:,:,:3]*np.array(p.get("BaseColor",[1,1,1,1])[:3])*np.maximum(1-w.sum(axis=2,keepdims=True),0)
    for i in range(4):
        tint=np.asarray(p.get("BaseColorLayer"+str(i+1),[1,1,1,1])[:3])
        if multiply:tint=tint*base[:,:,:3]
        result=result*(1-w[:,:,i:i+1])+tint*w[:,:,i:i+1]
    lum=result@np.array([.2126,.7152,.0722])
    sat=fp.get("SaturationPower",1.0);dark=fp.get("BaseColorDarkness",0.0)
    result=(lum[:,:,None]*(1-sat)+result*sat)*(1-dark)
    rgb=linear_to_srgb(result);alpha=base[:,:,3:4]*p.get("BaseColor",[1,1,1,1])[3]
    return rgba_image(np.concatenate([rgb,alpha],axis=2))
def normal_image(im,r):
    if int(r["format_code"],16)!=0x1e01 or r["channels"]!=[2,3,4,5]:raise NotImplementedError("normal format")
    a=np.asarray(im,dtype=np.float64)/255;xy=a[:,:,:2]*2-1
    z=np.sqrt(np.maximum(0,1-np.sum(xy*xy,axis=2,keepdims=True)))
    xyz=np.concatenate([xy,z],axis=2);norm=np.linalg.norm(xyz,axis=2,keepdims=True)
    xyz=xyz/np.maximum(norm,1e-9)
    return rgba_image(np.concatenate([xyz*.5+.5,np.ones_like(z)],axis=2))
def source_samplers(raw):
    f=geo.FB(raw);o=f.u("I",0);out={}
    for t in f.tables(o,1):
        out[f.txt(t,0)]=[dict(u=f.scalar(x,9,"I"),v=f.scalar(x,10,"I")) for x in f.tables(t,3)]
    return out
def texture_transform(m,normal=False):
    p=m["rgba"];opts=m["shaders"][0]["values"]
    separate=normal and opts.get("EnableUVScaleOffsetNormal","False")=="True"
    scale=p.get("UVScaleOffsetNormal" if separate else "UVScaleOffset",[1,1,0,0])
    center=[0,0] if separate else p.get("UVCenter0",[0,0,0,0])[:2]
    # Candidate centered affine transform. V1 native UV orientation retained.
    off=[scale[i+2]+center[i]*(1-scale[i]) for i in range(2)]
    return dict(scale=scale[:2],offset=off)
def add_image(g,im,name,sampler):
    # gftool Sampling.glsl mode 1 repeat, 6 mirror; mode 7 approximated clamp.
    wrap={1:10497,6:33648,7:33071}
    if sampler["u"] not in wrap or sampler["v"] not in wrap:raise ValueError("unsupported sampler")
    d=g.doc;bio=io.BytesIO();im.save(bio,format="PNG");raw=bio.getvalue()
    while len(g.data)%4:g.data.append(0)
    vi=len(d["bufferViews"]);d["bufferViews"].append(dict(buffer=0,byteOffset=len(g.data),byteLength=len(raw)));g.data.extend(raw)
    images=d.setdefault("images",[]);ii=len(images);images.append(dict(name=name,bufferView=vi,mimeType="image/png"))
    samplers=d.setdefault("samplers",[]);s=dict(wrapS=wrap[sampler["u"]],wrapT=wrap[sampler["v"]],magFilter=9729,minFilter=9987)
    if s not in samplers:samplers.append(s)
    textures=d.setdefault("textures",[]);ti=len(textures);textures.append(dict(name=name,source=ii,sampler=samplers.index(s)))
    return ti,dict(name=name,width=im.width,height=im.height,png_sha256=sha(raw),rgba_sha256=sha(im.tobytes()),sampler=s)
def attach_info(ti,transform):
    info=dict(index=ti)
    if any(abs(a-b)>1e-7 for a,b in zip(transform["scale"]+transform["offset"],[1,1,0,0])):
        info["extensions"]={"KHR_texture_transform":transform}
    return info
def parse_glb(path):
    b=path.read_bytes();magic,version,size=struct.unpack_from("<4sII",b)
    if (magic,version,size)!=(b"glTF",2,len(b)):raise ValueError("GLB header")
    n,tag=struct.unpack_from("<I4s",b,12);off=20+n
    if tag!=b"JSON":raise ValueError("JSON chunk")
    doc=json.loads(b[20:off]);bn,bt=struct.unpack_from("<I4s",b,off)
    if bt!=b"BIN\0" or off+8+bn!=len(b):raise ValueError("BIN chunk")
    g=v1.GLB();g.doc=doc;g.data=bytearray(b[off+8:off+8+doc["buffers"][0]["byteLength"]]);return g
def textured(flat_path,dest,material_path,variant,paths,cache,report):
    g=parse_glb(flat_path);d=g.doc;raw=audit.checked(material_path,paths)
    mats={m["name"]:m for m in geo.material(raw)};samplers=source_samplers(raw);outputs=[]
    def get(m,name):
        path=v1.resolve(material_path,m["textures"][name],paths)
        return read_texture(path,paths,cache,report)
    for mat in d["materials"]:
        name=mat["name"];m=mats[name];s=samplers[name];opts=m["shaders"][0]["values"]
        if m["shaders"][0]["name"]!="IkCharacter" or opts.get("EnableBaseColorMap")!="True":raise ValueError("unsupported shader")
        if s[0]!=s[8]:raise ValueError("base/mask sampler differs; needs UV-domain bake")
        b,br=get(m,"BaseColorMap");mask,mr=get(m,"LayerMaskMap")
        if int(mr["format_code"],16)&255!=1:raise ValueError("mask must be linear")
        size=(max(b.width,mask.width),max(b.height,mask.height))
        baked=bake(resize_float(pixels(b,br,True),size),resize_float(pixels(mask,mr),size),m)
        ti,meta=add_image(g,baked,name+"_baseColor",s[0]);outputs.append(meta)
        p=mat["pbrMetallicRoughness"];p["baseColorFactor"]=[1,1,1,1];p["baseColorTexture"]=attach_info(ti,texture_transform(m))
        if opts.get("EnableNormalMap")=="True":
            im,r=get(m,"NormalMap");ni,nmeta=add_image(g,normal_image(im,r),name+"_normal",s[1]);outputs.append(nmeta)
            mat["normalTexture"]=attach_info(ni,texture_transform(m,True))
        if opts.get("EnableAOMap")=="True":
            im,r=get(m,"OcclusionMap");ai,ameta=add_image(g,im,name+"_occlusion",s[2]);outputs.append(ameta)
            mat["occlusionTexture"]=attach_info(ai,texture_transform(m))
        mat["extras"].update(appearance_status="REFERENCE_BAKED_TEXTURE_CANDIDATE",uv_transform_candidate=texture_transform(m),native_sampler_states=s,
            unimplemented=["native shader lighting","eye parallax/refraction","eyelid","emission","specular/rim/shadow","native normal handedness","mode 7 exact address semantics"])
    d["asset"]["generator"]="ZANativeModelExporter V2 Textured candidate"
    if any("extensions" in info for mat in d["materials"] for info in [mat["pbrMetallicRoughness"]["baseColorTexture"],mat.get("normalTexture",{}),mat.get("occlusionTexture",{})]):d["extensionsUsed"]=["KHR_texture_transform"]
    d["extras"].update(material_status="reference baseColor bake; candidate normal/AO",native_shader_parity=False,uv_visual_parity=False)
    digest=g.save(dest);validation=v1.validate(dest)
    # Re-open each embedded PNG and ensure the material graph references it.
    verify=parse_glb(dest)
    for i in verify.doc["images"]:
        view=verify.doc["bufferViews"][i["bufferView"]];raw=bytes(verify.data[view["byteOffset"]:view["byteOffset"]+view["byteLength"]])
        with Image.open(io.BytesIO(raw)) as im:im.verify()
    return dict(file=dest.name,variant=variant,sha256=digest,bytes=dest.stat().st_size,images=len(outputs),materials=len(d["materials"]),textures=outputs,**validation)
def self_test():
    r=dict(depth=1,array_count=1,storage_dim=2,image_dim=1,tile_mode=0,swizzle=0,format_code="0x1d01",width=8,height=8,block_height_log2=1,mip_count=2,mip_offsets=[0,512],image_size=1024,channels=[2,2,2,1])
    raw=bytearray(1024)
    # Four BC4 constant blocks at mip0 and one at mip1; use actual GOB offsets.
    for y in range(2):
        for x in range(2):
            p=bntx.gob_offset(x*8,y,64,1);raw[p:p+8]=bytes([128,128])+bytes(6)
    raw[512:520]=bytes([64,64])+bytes(6)
    a,_=decode_mip(raw,r,0);b,_=decode_mip(raw,r,1)
    assert a.size==(8,8) and a.getpixel((0,0))==(128,128,128,255)
    assert b.size==(4,4) and b.getpixel((0,0))==(64,64,64,255)
    # independent BC5 constant-channel fixture
    q=dict(r,format_code="0x1e01",width=4,height=4,mip_count=1,mip_offsets=[0],image_size=512,channels=[2,3,4,5])
    raw=bytes([128,128])+bytes(6)+bytes([64,64])+bytes(6)+bytes(496)
    im,_=decode_mip(raw,q,0);assert im.getpixel((0,0))==(128,64,0,255)
    assert normal_image(im,q).getpixel((0,0))[2]>230
    m=dict(shaders=[dict(values={"NumMaterialLayer":"5","BaseColorMultiply":"True"})],float_parameters={},rgba={"BaseColorLayer1":[.25,.5,1,1]})
    a=np.ones((1,1,4));w=np.array([[[1.,0.,0.,0.]]]);out=bake(a,w,m)
    assert out.getpixel((0,0))==(137,188,255,255)
    print("Mip span, BC4/BC5, color-space and LayerMask fixtures passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--out",type=Path,default=Path(".za-work/ZANativeModelExporterV2"));a=p.parse_args()
    if a.self_test:self_test();return
    if not a.out.resolve().is_relative_to(Path(".za-work").resolve()) or a.out.resolve()==Path(".za-work").resolve():p.error("local output only")
    if a.out.exists() and any(a.out.iterdir()):p.error("empty output required")
    a.out.mkdir(parents=True,exist_ok=True);paths=audit.tree();model=v1.SAMPLE
    def get(p):return audit.checked(p,paths)
    mdl=audit.parse(get(model),".trmdl");sp=v1.resolve(model,mdl["skeleton"],paths);sk=geo.skeleton(get(sp));local,joints,ib,bind=v1.bind_pose(sk)
    if bind["max_identity_error"]>v1.EPS:raise ValueError("bind failure")
    mp=v1.resolve(model,mdl["meshes"][0],paths);mb=get(mp);f=geo.FB(mb);bp=v1.resolve(mp,f.txt(f.u("I",0),2),paths);shapes=v1.read_mesh(mb,get(bp),sk)
    mmp=model.removesuffix(".trmdl")+".trmmt";variants=audit.parse(get(mmp),".trmmt")["variants"]
    cache={};report=[];exports=[]
    for variant in ("normal","rare"):
        match=[x for x in variants if x["name"]==variant]
        if len(match)!=1 or len(match[0]["material_files"])!=1:raise ValueError("variant")
        matpath=v1.resolve(mmp,match[0]["material_files"][0],paths);flat=a.out/(variant+".flat.glb");dest=a.out/(Path(model).stem+"_"+variant+".glb")
        v1.export(flat,shapes,sk,local,joints,ib,geo.material(get(matpath)),variant)
        exports.append(textured(flat,dest,matpath,variant,paths,cache,report));flat.unlink()
    # Prove geometry/accessor bytes are unchanged across variant GLBs.
    gs=[parse_glb(a.out/e["file"]) for e in exports]
    ends=[min(g.doc["bufferViews"][i["bufferView"]]["byteOffset"] for i in g.doc["images"]) for g in gs]
    if gs[0].data[:ends[0]]!=gs[1].data[:ends[1]]:raise ValueError("variant geometry changed")
    if not any(a["rgba_sha256"]!=b["rgba_sha256"] for a,b in zip(exports[0]["textures"],exports[1]["textures"]) if a["name"].endswith("_baseColor")):raise ValueError("variant textures identical")
    audit.write(a.out,"source-mips",report)
    s=dict(source_commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),model=model,bind_pose=bind,unique_source_textures=len(report),decoded_mips=sum(len(r["mips"]) for r in report),geometry_identical=True,exports=exports,native_shader_parity=False,visual_parity=False,notes="Reference bake in source texture domain, candidate centered UV transform, mode 7 clamp approximation, normal Y convention unverified")
    (a.out/"summary.json").write_text(json.dumps(s,indent=2)+"\n");print(json.dumps(s,indent=2))
if __name__=="__main__":main()
