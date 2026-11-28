"""Read-only native tangent and multi-UV evidence, independent of material export."""
import numpy as np
def audit_mesh(geo,m,b):
    f=geo.FB(m);g=geo.FB(b);rows=[]
    for t,u in zip(f.tables(f.u("I",0),1),g.tables(g.u("I",0),1)):
        name=f.txt(t,0);ds=f.tables(t,3);vs=g.tables(u,1)
        if len(ds)!=1 or len(vs)!=1:rows.append(dict(name=name,status="UNSUPPORTED_STREAM_COUNT"));continue
        d=ds[0];ss=[f.scalar(x,0,"I") for x in f.tables(d,1)]
        attrs=[(f.scalar(x,1,"I"),f.scalar(x,2,"I"),f.scalar(x,3,"I"),f.scalar(x,4,"I")) for x in f.tables(d,0)]
        raw=g.bytes_vector(vs[0],0)
        if len(ss)!=1 or not ss[0] or len(raw)%ss[0]:rows.append(dict(name=name,status="UNSUPPORTED_STRIDE"));continue
        stride=ss[0];n=len(raw)//stride
        def read(usage,layer):
            aa=[a for a in attrs if a[:2]==(usage,layer)]
            if len(aa)!=1:return None
            _,_,ty,off=aa[0]
            if ty not in geo.FMT or off+geo.FMT[ty][1]>stride:return None
            return np.array([geo.unpack(raw,i*stride+off,ty) for i in range(n)])
        pos=read(1,0);normal=read(2,0);results=[]
        if pos is None or normal is None or not n:continue
        normal=normal[:,:3];nn=np.linalg.norm(normal,axis=1)
        for layer in sorted({a[1] for a in attrs if a[0]==3}):
            tan=read(3,layer);uv=read(6,layer)
            if tan is None or uv is None:results.append(dict(layer=layer,status="UNSUPPORTED"));continue
            xyz=tan[:,:3];tn=np.linalg.norm(xyz,axis=1);dot=np.sum(normal*xyz,axis=1)/np.maximum(nn*tn,1e-12)
            handed=tan[:,3] if tan.shape[1]==4 else np.zeros(n)
            typ=f.scalar(t,2,"I");ixs=g.tables(u,0);agree=[];sign=[]
            if typ in (0,1,2) and len(ixs)==1:
                ix=np.frombuffer(g.bytes_vector(ixs[0],0),dtype={0:"u1",1:"<u2",2:"<u4"}[typ])
                if len(ix)%3==0 and len(ix) and int(ix.max())<n:
                    tri=ix.reshape(-1,3);p=pos[tri];q=uv[tri,:2];e1=p[:,1]-p[:,0];e2=p[:,2]-p[:,0];u1=q[:,1]-q[:,0];u2=q[:,2]-q[:,0];det=u1[:,0]*u2[:,1]-u1[:,1]*u2[:,0]
                    valid=np.abs(det)>1e-10
                    tr=tri[valid];dv=det[valid]
                    tt=(e1[valid]*u2[valid,1,None]-e2[valid]*u1[valid,1,None])/dv[:,None]
                    bt=(e2[valid]*u1[valid,0,None]-e1[valid]*u2[valid,0,None])/dv[:,None]
                    if len(tr):
                        t0=xyz[tr[:,0]];n0=normal[tr[:,0]]
                        agree=(np.sum(tt*t0,axis=1)/np.maximum(np.linalg.norm(tt,axis=1)*np.linalg.norm(t0,axis=1),1e-12)).tolist()
                        sign=(np.sign(np.sum(np.cross(n0,t0)*bt,axis=1))*np.sign(handed[tr[:,0]])).tolist()
            results.append(dict(layer=layer,vertices=n,normal_length_min=float(nn.min()),normal_length_max=float(nn.max()),tangent_length_min=float(tn.min()),tangent_length_max=float(tn.max()),max_abs_normal_tangent_dot=float(np.max(np.abs(dot))),handedness_values=sorted(set(map(float,handed))),triangle_samples=len(agree),mean_tangent_alignment=float(np.mean(agree)) if agree else None,handedness_agreement=float(np.mean(np.array(sign)>0)) if sign else None,status="CANDIDATE_NUMERIC"))
        rows.append(dict(name=name,stride=stride,vertex_streams=len(vs),attribute_layers=[list(a) for a in attrs],tangents=results,status="AUDITED"))
    return rows
