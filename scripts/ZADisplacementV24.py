"""V2.4 source-backed reference displacement, static bind-pose only."""
import copy, math, hashlib
import numpy as np
def sample_repeat_red(image,uv):
    # OpenGL normalized coordinates, center of texel at (i+.5)/size.
    a=np.asarray(image,dtype=np.float64)[:,:,0]/255.0;h,w=a.shape
    x=uv[:,0]*w-.5;y=uv[:,1]*h-.5
    ix=np.floor(x).astype(np.int64);iy=np.floor(y).astype(np.int64)
    fx=x-ix;fy=y-iy
    return ((1-fx)*(1-fy)*a[iy%h,ix%w]+fx*(1-fy)*a[iy%h,(ix+1)%w]+(1-fx)*fy*a[(iy+1)%h,ix%w]+fx*fy*a[(iy+1)%h,(ix+1)%w])
def bake_shapes(shapes,materials,material_path,paths,cache,report,v2,visual):
    """Only single-material shapes; no silent deformation for unsupported shaders.
    Both variants must still pass byte-identical geometry gate in caller.
    """
    out=copy.deepcopy(shapes);raw=v2.audit.checked(material_path,paths);slots=visual.slots(raw);samplers=v2.source_samplers(raw)
    mats={m["name"]:m for m in materials};results=[]
    for sh in out:
        names={name for name,_ in sh["parts"]};active=[]
        for name in sorted(names):
            m=mats[name];opts=m["shaders"][0]["values"]
            if opts.get("EnableDisplacementMap")=="True":
                height=m["float_parameters"].get("DisplacementHeight")
                if height is None or not math.isfinite(height):raise ValueError("missing/nonfinite displacement height")
                if height!=0:active.append((m,height))
        if not active:continue
        if len(names)!=1 or len(active)!=1:raise ValueError("mixed displacement mesh; split required")
        m,height=active[0];name=m["name"];opts=m["shaders"][0]["values"]
        if len(m["shaders"])!=1 or m["shaders"][0]["name"]!="Unlit":raise ValueError("unsupported displacement shader")
        sl=slots[name].get("DisplacementMap")
        if sl is None or samplers[name][sl]!={"u":1,"v":1}:raise ValueError("unsupported displacement sampler")
        path=v2.v1.resolve(material_path,m["textures"]["DisplacementMap"],paths)
        im,r=v2.read_texture(path,paths,cache,report)
        if int(r["format_code"],16)&255!=1:raise ValueError("nonlinear displacement map")
        raw_idx=m["int_parameters"].get("UVIndexLayer3",-1)
        required_uv=opts.get("NumRequiredUV")
        # Reference Unlit chooses UV0 unconditionally for a one-UV shader.
        # Preserve -1 raw sentinel instead of interpreting it as an actual index.
        if required_uv=="1":idx=0
        elif required_uv=="2" and raw_idx in (0,1):idx=raw_idx
        else:raise ValueError("unsupported displacement UV index "+str((required_uv,raw_idx)))
        extra=sh["extra_attributes"]
        uv=np.asarray(sh["uv"] if idx==0 else extra["TEXCOORD_1"],dtype=float)
        color=extra.get("_ZA_COLOR_0",extra.get("COLOR_0"))
        if color is None:raise ValueError("displacement requires explicit native vertex color")
        red=np.asarray(color,dtype=float)[:,0]
        scale=np.asarray(m["rgba"].get("UVScaleOffset3",[1,1,0,0]),dtype=float)
        if scale.shape!=(4,) or not np.isfinite(scale).all():raise ValueError("invalid displacement UV transform")
        uv=(uv-scale[2:])*scale[:2];uv[:,1]=1-uv[:,1]
        h=sample_repeat_red(im,uv);amount=np.sin(h)*red*height
        p=np.asarray(sh["positions"],dtype=float);n=np.asarray(sh["normals"],dtype=float);delta=n*amount[:,None]
        if not np.isfinite(delta).all() or np.max(np.abs(amount))>abs(height)*max(1,float(np.max(np.abs(red))))+1e-9:raise ValueError("displacement bounds")
        extra["_ZA_POSITION_BASE"]=p.tolist()
        sh["positions"]=(p+delta).tolist()
        m["_za_displacement_baked"]=True
        results.append(dict(shape=sh["name"],material=name,source=path,source_blob=paths[path],uv_set=idx,uv_index_raw=raw_idx,num_required_uv_raw=required_uv,uv_transform=scale.tolist(),height=height,red_min=float(red.min()),red_max=float(red.max()),sample_min=float(h.min()),sample_max=float(h.max()),vertices=len(p),nonzero_vertices=int(np.count_nonzero(np.abs(amount)>1e-9)),signed_delta_min=float(amount.min()),signed_delta_max=float(amount.max()),max_distance=float(np.max(np.linalg.norm(delta,axis=1))),delta_sha256=hashlib.sha256(delta.astype("<f4").tobytes()).hexdigest(),status="REFERENCE_STATIC_BIND_POSE_CANDIDATE",native_shader_parity=False))
    return out,results
def self_test():
    from PIL import Image
    im=Image.fromarray(np.array([[[0,0,0,255],[255,0,0,255]]],dtype=np.uint8))
    a=sample_repeat_red(im,np.array([[.25,.5],[.75,.5],[0,.5],[1,.5],[-.25,.5]]))
    assert np.allclose(a,[0,1,.5,.5,1])
    assert np.isclose(np.sin(1)*(-.125)*.08,-.008414709848078965)
