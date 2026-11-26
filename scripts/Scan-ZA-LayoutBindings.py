#!/usr/bin/env python3
"""Audit layout pic/material/texture-name joins against ARC BRTI names; no pixel rendering."""
import argparse,collections,hashlib,importlib.util,json,re,struct,subprocess
from pathlib import Path
def load(name,path):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(path));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
arc=load("arc","Scan-ZA-UIArchives.py");bntx=load("bntx","Decode-ZA-BNTX.py")
def write(out,name,rows):
    (out/(name+".jsonl")).write_text("".join(json.dumps(x,ensure_ascii=True)+"\n" for x in rows))
def cstr(b,p,end):
    if not 0<=p<end<=len(b):raise ValueError("string offset")
    z=b.find(b"\0",p,end)
    if z<0:raise ValueError("unterminated string")
    return b[p:z].decode("utf8","replace")
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=Path(".za-work/layout-bind"));a=p.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=True)
    aliases=collections.defaultdict(list)
    for row in subprocess.check_output(["git","ls-tree","-rz","HEAD","--",str(arc.ROOT)]).split(b"\0"):
        if not row:continue
        meta,path=row.split(b"\t",1);mode,kind,sha=meta.decode().split();path=path.decode()
        if kind=="blob" and path.endswith(".arc"):aliases[sha].append(path)
    pics=[];mats=[];textures=[];components=[];brtis=[];errors=[];counts=collections.Counter()
    for sha,paths in sorted(aliases.items()):
        f=next((Path(x) for x in paths if Path(x).is_file()),None)
        if not f:errors.append(dict(sha=sha,stage="missing"));continue
        raw=f.read_bytes()
        if hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()!=sha:raise ValueError("blob mismatch")
        entries=list(arc.sarc(raw));counts["archives"]+=1
        index=collections.defaultdict(list)
        for name,b in entries:
            if not name.endswith(".bntx"):continue
            try:
                for r in bntx.parse(b):
                    x=dict(sha=sha,member=name,**r);brtis.append(x);index[r["name"]].append(dict(member=name,index=r["index"],format=r["format_name"],width=r["width"],height=r["height"]))
            except Exception as ex:errors.append(dict(sha=sha,member=name,stage="bntx",error=str(ex)))
        for name,b in entries:
            if not name.endswith(".bflyt"):continue
            counts["layouts"]+=1
            endi="<" if b[4:6]==b"\xff\xfe" else ">"
            def u(fmt,p):return struct.unpack_from(endi+fmt,b,p)[0]
            secs=arc.layout_sections(b);tx=[];ms=[]
            base=dict(sha=sha,member=name)
            try:
                for tag,pos,n in secs:
                    if tag=="txl1":
                        c=u("H",pos+8)
                        if 12+4*c>n:raise ValueError("txl count")
                        for i in range(c):
                            v=u("I",pos+12+4*i);t=cstr(b,pos+12+v,pos+n);tx.append(t)
                            textures.append(dict(**base,index=i,name=t,matches=index.get(t,[])))
                    if tag=="mat1":
                        c=u("H",pos+8)
                        if 12+4*c>n:raise ValueError("mat count")
                        offsets=[u("I",pos+12+4*i) for i in range(c)]+[n]
                        for i,(v,z) in enumerate(zip(offsets,offsets[1:])):
                            if not 12+4*c<=v<z<=n or z-v<40:raise ValueError("mat bounds")
                            start=pos+v;nm=cstr(b,start,start+28)
                            # Raw flags and first candidate texture index. No flag interpretation yet.
                            flags=u("I",start+28)
                            first=u("H",start+40) if z-v>=44 else None
                            row=dict(**base,index=i,name=nm,size=z-v,flags=f"{flags:08x}",first_texture_index_candidate=first,first_texture_candidate=tx[first] if first is not None and first<len(tx) else None,raw_prefix=b[start:start+min(z-v,64)].hex())
                            mats.append(row);ms.append(row)
                for tag,pos,n in secs:
                    if tag=="pic1":
                        if n<104:raise ValueError("short pic1")
                        nm=cstr(b,pos+12,pos+36);i=u("H",pos+100);uv=b[pos+102]
                        r=ms[i] if i<len(ms) else None
                        # pic1 material slot verified by bounds and name agreement; texture candidate remains unproven.
                        pics.append(dict(**base,offset=pos,name=nm,material_index=i,uv_count=uv,material=r["name"] if r else None,material_name_agreement=bool(r and nm==r["name"]),texture_candidate=r["first_texture_candidate"] if r else None))
                    if tag in ("cnt1","prt1","usd1"):
                        for m in re.finditer(rb"[ -~]{4,120}",b[pos+8:pos+n]):
                            st=m.group().decode("ascii")
                            if "[GF]" in st or "uikit" in st.lower() or "pokeicon" in st.lower():
                                components.append(dict(**base,section=tag,offset=pos+8+m.start(),text=st))
            except Exception as ex:errors.append(dict(**base,stage="layout",error=str(ex)))
    for name,rows in [("pictures",pics),("materials",mats),("texture-names",textures),("component-tokens",components),("brti",brtis),("errors",errors)]:write(out,name,rows)
    summary=dict(paths=sum(map(len,aliases.values())),unique_blobs=len(aliases),counts=dict(counts),pictures=len(pics),materials=len(mats),textures=len(textures),brti=len(brtis),picture_material_in_bounds=sum(x["material"] is not None for x in pics),picture_material_name_agreement=sum(x["material_name_agreement"] for x in pics),texture_exact_local_match=sum(bool(x["matches"]) for x in textures),texture_unique_local_match=sum(len(x["matches"])==1 for x in textures),component_tokens=len(components),component_classes=dict(collections.Counter(x["text"] for x in components).most_common(60)),errors=len(errors),material_texture_semantics_verified=False)
    (out/"summary.json").write_text(json.dumps(summary,indent=2));print("SUMMARY",json.dumps(summary))
    for x in errors[:12]:print("ERROR",json.dumps(x))
    for x in pics:
        if x["name"]=="P_icon_00" and "box_box_button_00" in x["member"]:
            print("SAMPLE",json.dumps(x));break
    for x in components:
        if "poke" in x["text"].lower():print("POKE_COMPONENT",json.dumps(x))
if __name__=="__main__":main()
