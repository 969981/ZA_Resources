#!/usr/bin/env python3
"""Audit native Zygarde material passes independently of blocked skinning."""
import importlib.util,json,collections
from pathlib import Path
import numpy as np
def load(name):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
v2=load("ZANativeModelExporterV2");visual=load("ZAVisualMaterialV22");visual.v2=v2
core=load("ZANativeShaderCore");adapter=load("ZATransparentMaterialV25");adapter.self_test(v2)
paths=core.audit.tree();v2.audit.checked=core.get;out=Path(".za-work/ZANativeShaderCore")
out.mkdir(parents=True,exist_ok=True);rows=[];cache={};report=[]
for path in sorted(paths):
    if not path.startswith("ik_pokemon/data/pm0770/") or not path.endswith(".trmtr"):continue
    raw=core.get(path,paths);f=core.FB(raw);o=f.u("I",0);alpha={f.txt(t,0):f.txt(t,15) for t in f.tables(o,1)}
    slots=visual.slots(raw)
    for m in v2.geo.material(raw):
        names=[s["name"] for s in m["shaders"]]
        if not any("Transparent" in n or n in ("FresnelEffect","SSS","InsideEmissionParallax") for n in names):continue
        row=dict(path=path,material=m["name"],shader_passes=m["shaders"],alpha_type_raw=alpha.get(m["name"]),texture_slots=slots[m["name"]],texture_refs=m["textures"],float_parameters=m["float_parameters"],int_parameters=m["int_parameters"],rgba=m["rgba"],native_shader_parity=False)
        try:
            if len(names)!=1 or names[0] not in ("Transparent","IkCharacterTransparent"):raise ValueError("view-dependent or multipass shader unresolved")
            p=v2.v1.resolve(path,m["textures"]["BaseColorMap"],paths);im,r=v2.read_texture(p,paths,cache,report)
            baked,meta=adapter.candidate(m,v2.pixels(im,r,True),v2)
            row.update(candidate=meta,rgba_sha256=v2.sha(baked.tobytes()),status="REFERENCE_TEXTURE_CANDIDATE")
        except Exception as e:row.update(status="REJECTED",reason=str(e))
        rows.append(row)
core.audit.write(out,"transparent-materials",rows);core.audit.write(out,"transparent-source-mips",report)
summary=dict(materials=len(rows),candidates=sum(r["status"]=="REFERENCE_TEXTURE_CANDIDATE" for r in rows),rejected=sum(r["status"]=="REJECTED" for r in rows),shader_pass_counts=dict(collections.Counter(s["name"] for r in rows for s in r["shader_passes"])),visual_parity=False)
(out/"transparent-summary.json").write_text(json.dumps(summary,indent=2)+"\n");print("TRANSPARENT_SUMMARY",json.dumps(summary))
if not rows or not summary["candidates"]:raise SystemExit("transparent sample missing")
