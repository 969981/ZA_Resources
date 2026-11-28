"""Batch headless import/render checks. No original-game comparison unless supplied separately."""
import bpy, json, sys, math, hashlib
from pathlib import Path
from mathutils import Vector
root=Path(sys.argv[sys.argv.index("--")+1]).resolve()
# Blender 4.5 importer stores names in a set but arrays in insertion order.
# Apply the upstream ordered-dict fix in this validation process only.
# https://github.com/blender/blender/blob/v4.5.3/scripts/addons_core/io_scene_gltf2/blender/imp/mesh.py
import inspect, textwrap
from io_scene_gltf2.blender.imp import mesh as importer_mesh
def ordered_custom_attributes():
    src=textwrap.dedent(inspect.getsource(importer_mesh.do_primitives))
    before="attributes = set({})";update="attributes.update(set(custom_attrs))"
    if src.count(before)==1 and src.count(update)==1:
        src=src.replace(before,"attributes = {}").replace(update,"attributes.update(dict.fromkeys(custom_attrs))")
        exec(compile(src,"<ZA ordered custom attribute compatibility>","exec"),importer_mesh.__dict__)
        return "UPSTREAM_ORDERED_DICT_COMPAT_PATCH"
    if "attributes = {}" in src and "attributes.update(dict.fromkeys(custom_attrs))" in src:return "UPSTREAM_ORDERED_DICT_PRESENT"
    raise RuntimeError("unrecognized Blender glTF custom attribute implementation")
importer_compat=ordered_custom_attributes()
print("BLENDER_ATTRIBUTE_COMPAT",importer_compat,flush=True)
rows=[]
for path in sorted(root.rglob("*.glb")):
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path))
        import struct
        raw=path.read_bytes();json_size=struct.unpack_from("<I",raw,12)[0]
        doc=json.loads(raw[20:20+json_size])
        expected=[n["name"] for n in doc["nodes"] if "mesh" in n and "skin" in n]
        scene_meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
        rigs=[o for o in bpy.context.scene.objects if o.type=="ARMATURE"]
        diag=[dict(name=o.name,vertices=len(o.data.vertices),modifiers=[dict(type=m.type,target=m.object.name if m.type=="ARMATURE" and m.object else None) for m in o.modifiers],groups=len(o.vertex_groups)) for o in scene_meshes]
        print("MESH_DIAGNOSTICS",json.dumps(dict(file=path.name,expected=expected,objects=diag)),flush=True)
        # Blender may add auxiliary bone display meshes. Validate every actual
        # source mesh node by its exact unique name, not arbitrary scene objects.
        if len(set(expected))!=len(expected):raise ValueError("duplicate source mesh node names")
        meshes=[]
        for name in expected:
            match=[o for o in scene_meshes if o.name==name]
            if len(match)!=1:raise ValueError("source mesh missing or ambiguous "+name)
            o=match[0]
            if not any(m.type=="ARMATURE" and m.object in rigs for m in o.modifiers):raise ValueError("source mesh lacks armature "+name)
            if not o.vertex_groups or not all(any(g.weight>0 for g in v.groups) for v in o.data.vertices):raise ValueError("source mesh lacks vertex weights "+name)
            meshes.append(o)
        extras=[o.name for o in scene_meshes if o not in meshes]
        if not meshes or not rigs:raise ValueError("missing mesh or armature")
        materials={m for o in meshes for m in o.data.materials if m}
        image_nodes=[n for m in materials if m.use_nodes for n in m.node_tree.nodes if n.type=="TEX_IMAGE" and n.image and n.image.size[0]>0]
        if not materials or not image_nodes:raise ValueError("missing material or texture")
        if not all(any(m.type=="ARMATURE" for m in o.modifiers) for o in meshes):raise ValueError("missing armature modifier")
        bpy.context.view_layer.update()
        points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
        lo=Vector(tuple(min(p[i] for p in points) for i in range(3)));hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
        center=(lo+hi)*.5;extent=max(hi-lo)
        if not math.isfinite(extent) or extent<=0:raise ValueError("invalid bounds")
        scene=bpy.context.scene
        bpy.ops.object.camera_add(location=center+Vector((1.6,-2.4,1.25))*extent)
        cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler();cam.data.type="ORTHO";cam.data.ortho_scale=extent*1.5;scene.camera=cam
        for offset,energy,size in [((2,-3,4),450,3),((-3,-1,2),260,3),((1,4,2),350,2)]:
            bpy.ops.object.light_add(type="AREA",location=center+Vector(offset)*extent);light=bpy.context.object;light.data.energy=energy*extent*extent;light.data.shape="DISK";light.data.size=size*extent;light.rotation_euler=(center-light.location).to_track_quat("-Z","Y").to_euler()
        scene.world=bpy.data.worlds.new("ZA Preview");scene.world.use_nodes=True;scene.world.node_tree.nodes["Background"].inputs[0].default_value=(.15,.15,.15,1)
        scene.render.engine="CYCLES";scene.cycles.device="CPU";scene.cycles.samples=8
        scene.render.resolution_x=256;scene.render.resolution_y=256;scene.render.resolution_percentage=100
        scene.render.film_transparent=True;scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA";scene.render.filepath=str(path.with_suffix(".preview.png"))
        bpy.ops.render.render(write_still=True)
        png=Path(scene.render.filepath);im=bpy.data.images.load(str(png),check_existing=False)
        import numpy as np
        pix=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(pix);pix=pix.reshape(-1,4)
        fg=pix[:,3]>.5;coverage=float(fg.mean())
        if not .005<coverage<.95:raise ValueError("empty or excessive foreground")
        rgb=pix[fg,:3];std=float(rgb.std())
        if not math.isfinite(std) or std<.005:raise ValueError("flat or invalid foreground")
        row=dict(file=str(path.relative_to(root)),mesh_objects=len(meshes),auxiliary_meshes=extras,armatures=len(rigs),materials=len(materials),image_nodes=len(image_nodes),bones=sum(len(o.data.bones) for o in rigs),bounds=[list(lo),list(hi)],coverage=coverage,foreground_rgb_std=std,render_sha256=hashlib.sha256(png.read_bytes()).hexdigest(),status="PASS",importer_compat=importer_compat,visual_parity=False)
    except Exception as e:row=dict(file=str(path.relative_to(root)),status="FAIL",error=str(e),visual_parity=False)
    rows.append(row);print("BLENDER_MODEL",json.dumps(row),flush=True)
(root/"blender-summary.json").write_text(json.dumps(dict(blender_version=bpy.app.version_string,models=rows),indent=2)+"\n")
if not rows or any(r["status"]!="PASS" for r in rows):raise RuntimeError("batch Blender failures")
