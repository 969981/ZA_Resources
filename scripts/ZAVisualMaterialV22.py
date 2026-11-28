"""V2.2 reference material adapters; no native Shader parity claim."""
import numpy as np
from PIL import Image
import io
v2=None
def uv_transform(m,normal=False,period=(1,1)):
    p=m["rgba"];opts=m["shaders"][0]["values"]
    separate=normal and opts.get("EnableUVScaleOffsetNormal")=="True"
    s=p.get("UVScaleOffsetNormal" if separate else "UVScaleOffset",[1,1,0,0])
    c=[0,0] if separate or m["shaders"][0]["name"]=="Unlit" else p.get("UVCenter0",[0,0,0,0])[:2]
    # gftool reference: (uv-center-offset)*scale+center; final y flip.
    x=c[0]-(c[0]+s[2])*s[0];y=c[1]-(c[1]+s[3])*s[1]
    return dict(scale=[s[0]/period[0],-s[1]/period[1]],offset=[x/period[0],(1-y)/period[1]])
def domain(base,mask,bs,ms):
    size=(max(base.shape[1],mask.shape[1]),max(base.shape[0],mask.shape[0]))
    base=v2.resize_float(base,size);mask=v2.resize_float(mask,size)
    period=[1,1];out={}
    # Exact periodicity for repeat+mirror: a two-tile supertexture.
    # Nonperiodic mismatch is supported only if the counterpart is constant.
    for i,k in enumerate(("u","v")):
        a,b=bs[k],ms[k]
        if a==b:out[k]=a;continue
        if np.max(np.abs(base-base[0,0]))<1e-12:out[k]=b;continue
        if np.max(np.abs(mask-mask[0,0]))<1e-12:out[k]=a;continue
        if {a,b}!={1,6}:raise ValueError("nonperiodic nonconstant sampler mismatch "+str((a,b)))
        period[i]=2;out[k]=1;axis=1-i
        base=np.concatenate([base,np.flip(base,axis=axis) if a==6 else base],axis=axis)
        mask=np.concatenate([mask,np.flip(mask,axis=axis) if b==6 else mask],axis=axis)
    if base.shape[0]*base.shape[1]>16777216:raise ValueError("bake too large")
    return base,mask,out,period
def unlit(base,mask,m):
    p=m["rgba"];fp=m["float_parameters"];opts=m["shaders"][0]["values"]
    count=int(opts["NumMaterialLayer"])
    if not 1<=count<=5:raise ValueError("unlit layer count")
    if opts.get("EnableDisplacementMap")=="True" and fp.get("DisplacementHeight")!=0 and not m.get("_za_displacement_baked"):raise ValueError("Unlit nonzero displacement requires reference bake")
    w=np.clip(mask*np.array([fp.get("LayerMaskScale"+str(i),1) for i in range(1,5)]),0,1)
    w[:,:,count-1:]=0
    total=np.maximum(1-w.sum(axis=2,keepdims=True),0);bc=np.array(p.get("BaseColor",[1,1,1,1]))
    tint=bc[:3]*total
    for i in range(4):
        weight=w[:,:,i:i+1];layer=np.array(p.get("BaseColorLayer"+str(i+1),[1,1,1,1]))[:3]
        tint=tint*(1-weight)+layer*bc[:3]*weight
        total=total*(1-weight)+weight
    rgb=base[:,:,:3]*tint/np.maximum(total,.00001)*fp.get("EmissionIntensity",1)
    return v2.rgba_image(np.concatenate([v2.linear_to_srgb(rgb),base[:,:,3:4]*bc[3]],axis=2))
def slots(raw):
    f=v2.geo.FB(raw);o=f.u("I",0)
    return {f.txt(t,0):{f.txt(x,0):f.scalar(x,2,"I") for x in f.tables(t,2)} for t in f.tables(o,1)}
def textured(flat_path,dest,material_path,variant,paths,cache,report,displacement_rows=()):
    g=v2.parse_glb(flat_path);d=g.doc;raw=v2.audit.checked(material_path,paths)
    mats={m["name"]:m for m in v2.geo.material(raw)};samplers=v2.source_samplers(raw);slotmap=slots(raw);outputs=[]
    def get(m,name):
        return v2.read_texture(v2.v1.resolve(material_path,m["textures"][name],paths),paths,cache,report)
    extensions=set()
    for mat in d["materials"]:
        name=mat["name"];m=mats[name];s=samplers[name];sl=slotmap[name];opts=m["shaders"][0]["values"];shader=m["shaders"][0]["name"]
        if len(m["shaders"])!=1 or shader not in ("IkCharacter","Unlit") or opts.get("EnableBaseColorMap")!="True":raise ValueError("unsupported shader "+str(shader))
        if opts.get("EnableLayerMaskUVTransform")=="True" or m["int_parameters"].get("UVIndexLayerMask",-1)==1:raise ValueError("independent LayerMask UV not supported")
        if not 1<=int(opts["NumMaterialLayer"])<=5:raise ValueError("unsupported layer count")
        b,br=get(m,"BaseColorMap");mask,mr=get(m,"LayerMaskMap")
        if int(mr["format_code"],16)&255!=1:raise ValueError("mask must be linear")
        base,weights,sampler,period=domain(v2.pixels(b,br,True),v2.pixels(mask,mr),s[sl["BaseColorMap"]],s[sl["LayerMaskMap"]])
        if any(r["material"]==name for r in displacement_rows):m["_za_displacement_baked"]=True
        baked=unlit(base,weights,m) if shader=="Unlit" else v2.bake(base,weights,m)
        ti,meta=v2.add_image(g,baked,name+"_baseColor",sampler);meta.update(period=period,shader=shader);outputs.append(meta)
        p=mat["pbrMetallicRoughness"];p["baseColorFactor"]=[1,1,1,1];p["baseColorTexture"]=v2.attach_info(ti,uv_transform(m,period=period))
        if shader=="Unlit":mat.setdefault("extensions",{})["KHR_materials_unlit"]={};extensions.add("KHR_materials_unlit")
        else:
            if opts.get("EnableNormalMap")=="True":
                im,r=get(m,"NormalMap");ni,nmeta=v2.add_image(g,v2.normal_image(im,r),name+"_normal",s[sl["NormalMap"]]);outputs.append(nmeta)
                mat["normalTexture"]=v2.attach_info(ni,uv_transform(m,True))
            if opts.get("EnableAOMap")=="True":
                im,r=get(m,"OcclusionMap");ai,ameta=v2.add_image(g,im,name+"_occlusion",s[sl["OcclusionMap"]]);outputs.append(ameta)
                mat["occlusionTexture"]=v2.attach_info(ai,uv_transform(m))
        if opts.get("EnableAlphaTest")=="True":
            mat["alphaMode"]="MASK";mat["alphaCutoff"]=m["float_parameters"].get("DiscardValue",.5)
        mat["extras"].update(appearance_status="REFERENCE_V22_CANDIDATE",native_sampler_states=s,native_slots=sl,period=period,
            displacement_height=m["float_parameters"].get("DisplacementHeight"),displacement_bake=[r for r in displacement_rows if r["material"]==name],unresolved=["original shader","normal handedness","eye parallax","lighting","emission parity","mode7 boundary","filtering"])
    if any("extensions" in info for mat in d["materials"] for info in [mat["pbrMetallicRoughness"]["baseColorTexture"],mat.get("normalTexture",{}),mat.get("occlusionTexture",{})]):extensions.add("KHR_texture_transform")
    d["extensionsUsed"]=sorted(extensions)
    d["asset"]["generator"]="ZANativeModelExporter V2.4 reference candidate"
    d["extras"].update(material_status="reference V2.2 UV-domain bake",native_shader_parity=False,uv_visual_parity=False)
    digest=g.save(dest);validation=v2.v1.validate(dest)
    verify=v2.parse_glb(dest)
    for i in verify.doc["images"]:
        view=verify.doc["bufferViews"][i["bufferView"]]
        with Image.open(io.BytesIO(bytes(verify.data[view["byteOffset"]:view["byteOffset"]+view["byteLength"]]))) as im:im.verify()
    return dict(file=dest.name,variant=variant,sha256=digest,bytes=dest.stat().st_size,images=len(outputs),materials=len(d["materials"]),textures=outputs,**validation)
def self_test():
    a=np.array([[[.1,.2,.3,1],[.8,.7,.6,1]]]);b=a.copy()
    x,y,s,p=domain(a,b,dict(u=6,v=1),dict(u=1,v=1))
    assert p==[2,1] and s==dict(u=1,v=1)
    assert np.array_equal(x,np.concatenate([a,a[:,::-1]],axis=1))
    assert np.array_equal(y,np.concatenate([b,b],axis=1))
    x,y,s,p=domain(np.ones_like(a),b,dict(u=1,v=1),dict(u=7,v=7))
    assert p==[1,1] and s==dict(u=7,v=7)
    m=dict(shaders=[dict(name="IkCharacter",values={})],rgba={"UVScaleOffset":[2,1,.25,.1]})
    assert uv_transform(m)==dict(scale=[2,-1],offset=[-.5,1.1])
