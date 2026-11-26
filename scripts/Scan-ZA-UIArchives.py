#!/usr/bin/env python3
"""Read-only UI SARC member and component audit. Deduplicate by Git blob, retain aliases."""
import argparse, collections, hashlib, json, re, struct, subprocess
from pathlib import Path
ROOT=Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/ui/data")
TERMS=re.compile(rb"(?i)UikitPokeIcon|L_pokeicon_[0-9%]+|P_poke_icon_[0-9]+|P_icon_00|switch_icon|grptxt_icon_type_[A-Za-z0-9_^]+|icon_item|__Combined\.bntx")
def sarc(b):
    if b[:4]!=b"SARC" or len(b)<20:raise ValueError("not SARC")
    bo=b[6:8]; e="<" if bo==b"\xff\xfe" else ">" if bo==b"\xfe\xff" else None
    if not e:raise ValueError("BOM")
    def u(f,o):return struct.unpack_from(e+f,b,o)[0]
    sh=u("H",4);size=u("I",8);data=u("I",12)
    if size!=len(b) or not sh+12<=data<=size or b[sh:sh+4]!=b"SFAT":raise ValueError("header")
    ah=u("H",sh+4); count=u("H",sh+6); nodes=sh+ah; sfnt=nodes+16*count
    if sfnt+8>data or b[sfnt:sfnt+4]!=b"SFNT":raise ValueError("SFNT")
    names=sfnt+u("H",sfnt+4)
    for i in range(count):
        o=nodes+16*i; hv,attr,start,end=struct.unpack_from(e+"4I",b,o)
        if not 0<=start<=end<=size-data:raise ValueError("member bounds")
        name=f"hash_{hv:08x}"
        if attr>>24:
            n=names+4*(attr&0xffffff); z=b.find(b"\0",n,data)
            if not names<=n<data or z<0:raise ValueError("name bounds")
            name=b[n:z].decode("utf8","replace")
        yield name,b[data+start:data+end]
def layout_sections(b):
    if b[:4] not in (b"FLYT",b"FLAN"):return []
    e="<" if b[4:6]==b"\xff\xfe" else ">" if b[4:6]==b"\xfe\xff" else None
    if not e:return []
    head=struct.unpack_from(e+"H",b,6)[0]; count=struct.unpack_from(e+"H",b,16)[0]
    pos=head;rows=[]
    for i in range(count):
        if pos+8>len(b):raise ValueError("layout section header")
        tag=b[pos:pos+4].decode("ascii","replace");n=struct.unpack_from(e+"I",b,pos+4)[0]
        if n<8 or pos+n>len(b):raise ValueError("layout section bounds")
        rows.append((tag,pos,n));pos+=n
    return rows
def write(out,name,rows):
    (out/name).write_text("".join(json.dumps(r,ensure_ascii=True)+"\n" for r in rows))
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=Path(".za-work/ui-archive"));a=p.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=True)
    aliases=collections.defaultdict(list)
    for row in subprocess.check_output(["git","ls-tree","-rz","HEAD","--",str(ROOT)]).split(b"\0"):
        if not row:continue
        meta,path=row.split(b"\t",1);mode,kind,sha=meta.decode().split();path=path.decode()
        if kind=="blob" and path.endswith(".arc"):aliases[sha].append(path)
    members=[];hits=[];archives=[];errors=[]; sections=collections.Counter()
    for sha,paths in sorted(aliases.items()):
        file=next((Path(x) for x in paths if Path(x).is_file()),None)
        if file is None:errors.append(dict(sha=sha,stage="missing",paths=paths));continue
        b=file.read_bytes()
        try:
            if hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()!=sha:raise ValueError("git blob mismatch")
            entries=list(sarc(b))
        except Exception as ex:errors.append(dict(sha=sha,stage="sarc",error=str(ex),magic=b[:16].hex(),paths=paths));continue
        archives.append(dict(sha=sha,paths=paths,bytes=len(b),members=len(entries)))
        for name,d in entries:
            ext=Path(name).suffix.lower();magic=d[:4].decode("ascii","replace");ls=[]
            try:ls=layout_sections(d)
            except Exception as ex:errors.append(dict(sha=sha,member=name,stage="layout",error=str(ex)))
            sections.update(x[0] for x in ls)
            members.append(dict(sha=sha,member=name,bytes=len(d),magic=magic,extension=ext,sections=[x[0] for x in ls]))
            for match in TERMS.finditer(d):
                pos=match.start(); sec=next((x[0] for x in ls if x[1]<=pos<x[1]+x[2]),None)
                hits.append(dict(sha=sha,member=name,offset=pos,section=sec,token=match.group().decode("ascii"),paths=paths))
    write(out,"archives.jsonl",archives);write(out,"members.jsonl",members);write(out,"hits.jsonl",hits);write(out,"errors.jsonl",errors)
    summary=dict(tracked_paths=sum(map(len,aliases.values())),unique_blobs=len(aliases),parsed_paths=sum(len(x["paths"]) for x in archives),parsed_blobs=len(archives),members=len(members),extensions=dict(collections.Counter(x["extension"] for x in members)),sections=dict(sections),hit_counts=dict(collections.Counter(x["token"].lower() for x in hits)),uikit_hits=sum(x["token"].lower()=="uikitpokeicon" for x in hits),errors=len(errors))
    (out/"summary.json").write_text(json.dumps(summary,indent=2));print("SUMMARY",json.dumps(summary))
    for row in hits:
        if row["token"].lower()=="uikitpokeicon":print("UIKIT",json.dumps(row))
    for row in errors[:20]:print("ERROR",json.dumps(row))
    if len(archives)!=len(aliases):raise SystemExit("archive coverage incomplete")
if __name__=="__main__":main()
