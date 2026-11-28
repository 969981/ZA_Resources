# ZANativeModelExporter V2.1 — representative batch / visual validation
[总览](README.md) · [V2](NativeModelExporterV2.md)
V2 run 46101741626: 12 unique source BNTX, 107 mips, identical geometry, two GLB Khronos 0 errors/6 warnings each; Blender failed because system Python numpy absent. Fixed by apt python3-numpy and explicit Blender Python import test. No visual parity claim.
## 原生样本
直接按 Personal national_raw 和 Catalog slot1/2 选取，不从 pm prefix 推断 ID。23 catalog keys, 21 distinct TRMDL:
| National raw | models | catalog keys |
|---:|---:|---:|
|1|1|1|
|3|3|3|
|6|3|3|
|25|2|2|
|450|2|2|
|479|6|6|
|718|4|6|
基格尔德资源 pm0770: 11/12/13/51；forms1/2 share11, 0/3 share12. Preserve native appearance raw key; gender/shiny runtime semantic not claimed. 
## 批量门槛
V2.1 extends strict single-stream attributes by type and offset rather than hard-coded 48 bytes, supports uint8/16/32 index inputs only if actual indices fit uint16 output; rejects unresolved direct/local joint mapping, unsupported streams, unsafe weights, bind mismatch, missing LayerMask materials, multi-file variant, unknown shader or sampler. Native exact references and Git blobs verified, sparse checkout fallback git cat-file; no original bytes overwritten. All successful output marked CANDIDATE; rejection isolated per model and partial files removed. A missing rare record remains missing, identical candidate texture remains identical (not forced differentiation). The normal/rare geometry payload must match. No silent fallback to another model. Explicit --all opt-in is experimental, not a guarantee all590 pass.
## 验收
Khronos validates every generated GLB; Blender import checks armatures, texture nodes and renders transparent preview, foreground coverage and RGB variability checks for empty renders. These are sanity checks, not comparison to original game. Source mip and bake algorithms remain V2 reference candidate. Eye/refraction/shadow/lighting/normal-Y/native shader parity unresolved; screenshots with same pose/camera/lighting are required for objective visual parity. CI only uploads metadata, never GLBs/PNG.
```powershell
python -m pip install numpy==2.2.6 Pillow==12.3.0
python scripts/ZANativeModelExporterV21.py --self-test
python scripts/ZANativeModelExporterV21.py
npm install --no-save --ignore-scripts gltf-validator@2.0.0-dev.3.10
node scripts/Validate-ZABatchGltf.cjs .za-work/ZANativeModelExporterV21
blender -b -t 2 --python-exit-code 1 --python scripts/Validate-ZABatchBlender.py -- .za-work/ZANativeModelExporterV21
```
Output .za-work/ZANativeModelExporterV21/summary.json, batch-results.jsonl, models/<resource_dir>/<stem>/GLBs + summary + source-mips, khronos-summary.json, blender-summary.json. CI results pending; no assumption 21 pass.
