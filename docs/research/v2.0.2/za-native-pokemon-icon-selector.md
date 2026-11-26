---
title: ZA 2.0.2 原生宝可梦图标选择器研究
tags: [ZA, PokemonConfigParser, NativePokemonIconSelector, FlatBuffers]
status: static-key-crosswalk-confirmed-selector-unverified
---
# NativePokemonIconSelector
[[za-bntx-pokemon-icon-mapping]] · [[za-image-resource-audit]]

## 原生输入
- Catalog: ik_pokemon/catalog/catalog/poke_resource_table.trpmcatalog, 275948 bytes, Git blob d8facfafebe3de732b5a7fe0071f38e13cd819c5.
- Personal: avalon/data/personal_array.bin, 384260 bytes, Git blob a2d9c3bc7af23b5b5ce148202e68e79a2032c5dd. 1445 rows, 594 present. Layout reference: vendored pkNX/FlatBuffers/ZA/Personal/Schemas/PersonalInfoDetail.fbs and PersonalInfoGender.fbs. Slot 0 inline struct reads u16 at +0/+2/+4; slot 10 inline gender group and ratio; slot 1 present flag. Raw values retained; no assumption that numeric resource names equal national ID.
- main.elf: 66579944 bytes, SHA256 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d, Build ID b1f12fd919eae86ab8a978317677e64bce443d1f000000000000000000000000.
- All paths under Unpack/v2.0.2/romfs/arc/data.trpfs/virtual except ELF.

## 637 catalog keys directly parsed and joined
Root slot 1 vector; each row slot 0 points to another FlatBuffers table. Key slots 0:u16, 1:u8, 2:u8 (observed width/layout, absent treated as default 0 candidate). 637 unique triples, 598 unique first-two-field pairs. Slot 2 histogram 0=596, 1=41. 633/637 exact first-two-key matches to Personal raw species/form; 632 present, 1 absent. 268 matched records have model path numerical prefix different from raw Personal national field. Do not relabel these as confirmed national IDs before independently checking personal schema and name tables.
| Catalog index | Key | Directory |
|---:|---|---|
| 3 | 3,0,0 | pm0003_00_00 |
| 4 | 3,0,1 | pm0003_01_00 |
| 5 | 3,1,0 | pm0003_51_00 |
| 25 | 25,0,0 | pm0025_00_00 |
| 26 | 25,0,1 | pm0025_01_00 |
| 29 | 26,1,0 | pm0026_00_11 |
| 30 | 26,2,0 | pm0026_51_00 |
| 31 | 26,3,0 | pm0026_52_00 |
| 285 | 479,0,0 | pm0479_11_00 |
| 290 | 479,5,0 | pm0479_16_00 |
| 626-628 | 978,3/4/5,0 | pm1071_51_00 |
| 636 | 9999,0,0 | pm9999_00_00 |

Last four rows have no corresponding Personal pair. Slot 2 appearance/gender candidate only, not enum semantics or proof of shiny. Model folder IDs must not be used as game Form IDs. Catalog→directory→icon is a join candidate not a native UI call.

## trpokecfg direct samples
7 raw files read. Root at 56, vtable at 4; 24 vtable slots, object length 52 or 48. Slot 0 is at +7 (one byte in these samples); slots 1-8 when present each four bytes, plausible f32; slot 23 final 12-byte region (raw, not scalar). No field names assumed.
| Resource | Bytes | Slot 0 | Slot 1 | Slot 2 | Slot 7 | Slot 8 |
|---|---:|---:|---:|---:|---:|---:|
| pm0001_00_00 | 108 | 0 | .945 | 1.155 | -20 | 20 |
| pm0003_00_00 | 108 | 2 | .864 | 1.056 | -12 | 12 |
| pm0003_01_00 | 108 | 2 | .864 | 1.056 | -12 | 12 |
| pm0003_51_00 | 104 | 2 | .9 | 1.1 | -20 | absent |
| pm0003_00_00_oybn | 108 | 3 | 1.372 | 1.372 | -12 | 12 |
| pm0003_51_00_oybn | 104 | 3 | 1.43 | 1.43 | -20 | absent |
| pm0003_51_00_bousou | 104 | 2 | 2 | 2 | -20 | absent |

pm0003_00_00 and pm0003_01_00 config blob identical 4aebdf71d89a5d69ff1cf03f70715cfae879440d, but four icons have distinct Git blob hashes c5692448d3f2ff83d71668872461f51ff5b41c6b, a1b9c7830f6be621c1fc9330a2a36a4a31d0039d, eab35173063548f2dad7596d3a0245ab086c1fe5, f56e11833c518ca90d2118971994152e020bbd4d. Thus config alone cannot distinguish these resource identities. Distinct blobs do not prove distinct pixel values. Slot meaning and suffix semantics remain unknown.

## Reproduce
```powershell
python scripts/Probe-ZA-PokemonConfig.py
python -m pip install capstone==5.0.3
python scripts/Probe-ZA-NativePokemonIconSelector.py
```
Separate CI jobs: native config/Personal/catalog/BRTI crosswalk, ELF string/ADR/ADRP+ADD candidate xrefs and Capstone windows. No game assets uploaded; metadata only. The 66 MB ELF could not be read directly through connector, so xrefs are not yet observed; do not invent offsets. Static short windows do not establish function boundaries or runtime selection. Candidate table retains all ambiguous catalog rows, config fields raw, gender and shiny null. Sparse checkout limits direct raw files, excludes archived/split assets; reconcile against full path inventory before calling coverage complete.
## Next acceptance
1. Verify CI outputs, count raw BRTI and config paths against inventory, compare errors.
2. Inspect actual ELF xref windows and recover callers/format arguments, then use same Build ID runtime tests for male/female, no difference, shiny, form and fallback. 
3. Compare both icon suffixes pixel-wise with independently known normal/shiny references. Resolve slot 2 with native inputs, not naming convention.
4. Reconcile 268 mismatches with name table/official ID semantics, and 4 missing Personal keys. Only then materialize confirmed (species, form, gender, shiny) resolver.
