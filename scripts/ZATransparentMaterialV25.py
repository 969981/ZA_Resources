"""Single-pass reference transparency adapter; never fake view-dependent GPU behavior."""
import numpy as np
def candidate(m,base,v2):
    sh=m["shaders"][0]["name"]
    if len(m["shaders"])!=1 or sh not in ("Transparent","IkCharacterTransparent"):raise ValueError("unsupported transparent multipass")
    fp=m["float_parameters"];opts=m["shaders"][0]["values"]
    rgba=np.array(m["rgba"].get("BaseColor",[1,1,1,1]) if sh=="IkCharacterTransparent" else [1,1,1,1])
    result=np.asarray(base,dtype=float).copy();result*=rgba
    alpha=result[:,:,3];rgb=v2.linear_to_srgb(result[:,:,:3]);im=v2.rgba_image(np.concatenate([rgb,alpha[:,:,None]],axis=2))
    mode="MASK" if opts.get("EnableAlphaTest")=="True" else "BLEND";cutoff=fp.get("DiscardValue",.5)
    if not 0<=cutoff<=1:raise ValueError("alpha cutoff")
    return im,dict(shader=sh,alphaMode=mode,alphaCutoff=cutoff if mode=="MASK" else None,alpha_min=float(alpha.min()),alpha_max=float(alpha.max()),alpha_nonopaque=int(np.count_nonzero(alpha<.999)),status="REFERENCE_SINGLE_PASS_CANDIDATE",native_shader_parity=False,unresolved=["view dependent Fresnel","multipass depth and blending","native lighting","LayerMask behavior"])
def self_test(v2):
    m=dict(shaders=[dict(name="IkCharacterTransparent",values={"EnableAlphaTest":"True"})],float_parameters={"DiscardValue":.5},rgba={"BaseColor":[1,1,1,.5]})
    im,r=candidate(m,np.array([[[.25,.5,1.,.5],[1.,1.,1.,1.]]]),v2)
    assert im.getpixel((0,0))==(137,188,255,64) and r["alphaMode"]=="MASK"
