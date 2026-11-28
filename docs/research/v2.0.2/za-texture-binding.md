---
title: ZA 2.0.2 纹理路径构造与动态字符串键
tags: [ZA, ARM64, BNTX, UikitPokeIcon, TextureBinding]
status: static-trace-pass-selector-unverified
---
# 图标选择器第六阶段
[[za-resource-key-scanner]] · [[za-icon-registration]]
## 验收
[45772226571](https://github.com/969981/ZA_Resources/actions/runs/45772226571) success; [artifact](https://github.com/969981/ZA_Resources/actions/runs/45772226571/artifacts/15094512328). ELF SHA256 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d. 82 neighbor-key observations across four windows (overlap possible), 32 texture-related ASCII candidates, 8 data-pointer candidates, 69 ADR/ADRP candidates including 23 texture-related candidates, 28 disassembly windows. Direct B/BL counts: 0x283F0 97, 0x7DEFC0 238, 0x2CD6CC8 2, 0x2CD73BC/0x2CD7418 1 each.
## Static suffix key
| Record VA | String | Hash |
|---|---|---|
| 0x3E28108 | / | AF67024C8607461E |
| 0x3E28120 | _ | AF66B24C8606BE2E |
| 0x3E28138 | .bntx | AE49EDF5D08552A1 |
All are verified 24-byte keys. 0x2D6AF90 ADRP / 0x2D6AF94 ADD reference record base 0x3E28138; 0x2D6AF9C BL 0x421C copies static record to a view. 0x2D6AF8C BL 0x38B90 obtains dynamic input view. At 0x2D6AFD4 BL 0x629D8C receives two views, empty descriptor seeded with native empty hash, and X3 from [X21+8]. Return subsequently converted with 0x38B90. Exact semantic operation and upstream entity remain unverified.
## Direct extension literal
0x31AD4EC .bntx has six ADRP/ADD pairs at 0x2BCA1D0, 0x2C0477C, 0x2C1655C, 0x2C1689C, 0x2CDFFF0, 0x2D33C84. 0x2BCA1F0 and 0x2D33CA4 call 0x2A02B0 with 5 parts and capacity 0x100. 0x2CE0018 calls 0x31607C0 with destination length 0x50. Need full window and exact literal extraction to determine templates.
Other strings: ui/tex/icon_item/%s/%s.bntx at 0x31CF855; ui/tex/icon_donut/%s/%s.bntx at 0x32EB8AD (xref 0x2D69FE4); ui/tex/icon_donut/%s_big/%s_big.bntx at 0x32B5448 (xref 0x2D6A06C); ui/tex/icon_pokemon_last/icon_ob0009_00/icon_ob0009_00.bntx and two other fixed paths; ik_pokemon/data/ at 0x32D57AB, catalog path at 0x3288619. Existence in ELF does not prove files present or actual consumer.
## 0x283F0
MOV X1,X0; MOV X0,X8; B 0x972470. This is an ABI adapter, not the actual dynamic constructor. Do not include the adjacent function starting 0x283FC in its body. 97 direct references. Next trace 0x972470.
## UikitPokeIcon
Literal 0x3296760, seeded hash 954D3547F9414E35. No validated 24-byte static record, no aligned raw pointer or relative relocation to literal, no matching direct ADR/ADRP ADD/LDR candidate in this scan. No type or vtable attribution confirmed. No runtime trace.
## Reproduce
python -m pip install capstone==5.0.3
python scripts/Probe-ZA-TextureBinding.py
Expanded [run 45772323586](https://github.com/969981/ZA_Resources/actions/runs/45772323586) follows 0x972470, 0x629D8C, larger extension caller windows and exact adjacent ADRP/ADD literals. Hash and indirect pointer candidates remain static, not runtime evidence.

## Second run verified
[45772323586](https://github.com/969981/ZA_Resources/actions/runs/45772323586) success; [artifact](https://github.com/969981/ZA_Resources/actions/runs/45772323586/artifacts/15094662174). 30 windows, 69 xref candidates, 23 texture-related candidates; 0x972470 74 direct branches, 0x629D8C 3, 0x2A02B0 95.
### Dynamic constructor
0x972470 reads pointer/length at input+8/+0x10, hashes exactly length bytes with seed CBF29CE484222645 (ignores supplied Hash for construction), calls 0x164C8; empty path uses global 0x40FE128. Output is one object pointer; release path atomically subtracts 0x400 from packed flags at object+8 when low 2 bits nonzero, calls 0x95A40 on last reference condition. Initial output zero store observed; no claim of arbitrary replacement semantics. 0x283F0 is a three-instruction ABI adapter.
### Extension consumer
0x629D8C uses string view Name/Length, copies input, searches for occurrence of needle with byte search and compare (0x629E78/0x629E8C), calls 0x31611C0 with replacement position, needle length, replacement pointer and length. Repeats search from pos+replacement length. This supports substring replacement, not appending extension or directly selecting Pokemon textures. At 0x2D6AFD4 replacement is empty, thus removes .bntx occurrences from input; exact path source and upper-level caller still unknown.
### Path templates
- 0x2BCA130..0x2BCA204 constructs ui/tex/logo_brand/{arg1}/{arg2}.bntx via five parts.
- 0x2C0477C window: ui/tex/photomode_pose/, /, .bntx.
- 0x2C1655C and 0x2C1689C windows: ui/tex/tips/, /, .bntx.
- 0x2CDFF64..0x2CE003C formats six strings with %s%s%s%s%s%s, prefix [ryl_npc], / separators, .bntx suffix; first/second input view names as components.
- 0x2D33C84 window: ui/tex/icon_item/, /, .bntx; five-part concat at 0x2D33CA4. Input-to-ItemID mapping still not proven.
- 0x2D69FE4 and 0x2D6A06C reference donut normal and _big templates. No actual physical-path resolution or layout binding claimed.
Next run adds bytewise raw hash and bounded MOVZ/MOVK construction search for class name and three punctuation keys. UikitPokeIcon remains unresolved until confirmed binding or registration evidence.

## Third run verified: raw and immediate hash audit
[45772415393](https://github.com/969981/ZA_Resources/actions/runs/45772415393) success; [artifact](https://github.com/969981/ZA_Resources/actions/runs/45772415393/artifacts/15094727363). Exact raw hash hits: .bntx at 0x3E28138; / at 0x3DCD1A0, 0x3E054E8, 0x3E28108; _ at 0x3E28120. Bounded MOVZ/MOVK construction candidates: _ at 0x2973A88..0x2973A98 and 0x2B88BEC..0x2B88C00; / at 0x2D6AEF8..0x2D6AF08. Total 8 hits. UikitPokeIcon seeded hash 954D3547F9414E35 has zero matches under both scan modes. This excludes only these encodings, not indirect lookup, other hash algorithms or archive-side class metadata. No actual binding function assigned.
Next: trace item ID to string arguments of the 0x2D33C84 path builder; 0x2D6AEF8 surrounding string-view producer; inspect UI layout assets for UikitPokeIcon and connect node/class registration to ELF consumers. Preserve unverified shiny/gender/special forms as unknown. No runtime validation.
