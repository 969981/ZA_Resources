---
title: ZA 内嵌 BNSH 与原生字形虚表
tags: [ZA, BNSH, ResFontBase, ELF, Obsidian]
status: xref-and-vtable-candidates-confirmed-method-audit-pending
---
# ZA Embedded Shader / Native Font
[[za-native-glyph-uv-rtti]] · [[za-glyph-hermite-shader-locators]] · [[za-dynamic-texture-flts-renderer]]

## 第二轮 RTTI 回归
[45781698633](https://github.com/969981/ZA_Resources/actions/runs/45781698633) PASS. 68 RTTI names, 68 typeinfo candidates, 109 vtable candidates (including possible inheritance-pointer false positives), 3 embedded BNSH ADRP+ADD references. 9 font sheets / 5242880 BC4 Alpha parity pixels unchanged, zero differences (shared GOB deswizzle).

| Container VA | ARM64 reference PC | ADD PC |
|---|---|---|
| 0x3EF8000 | 0x2626190 | 0x2626194 |
| 0x3EF8000 | 0x2626AFC | 0x2626B00 |
| 0x3F00000 | 0x2666AD4 | 0x2666AD8 |

Reference PCs are not function entry points. Need dataflow to determine actual callee/argument and binding.

## Font virtual table candidates
| Type | TypeInfo | Candidate first function slot | Initial scan |
|---|---|---|---|
| ResFont | 0x3C92240 | 0x3C92110 | 24 slots (capped) |
| ResFontBase | 0x3C92398 | 0x3C92268 | 24 slots (capped) |
| ResFontBase | 0x3C92398 | 0x3C92258 | 1 slot, likely other object relation |

New read-only script checks primary candidate table header, offset-to-top, mapped executable pointers and actual bounded instruction prefixes. Ranks arithmetic (UDIV/MSUB/MADD, integer to float, FMUL/FDIV, byte/halfword loads), retains direct BL targets, no automatic naming. First RET does not prove complete function boundary. Short one-slot reference excluded from primary inspection pending object-layout proof.

## Embedded shader audit
BNSH magic/BOM and declared byte length checked against mapped segment; SHA256 and structural tag offsets only; bounded ASCII name inventory. No shader bytes exported. Three reference windows and direct BL targets retained with bounded prefixes. GPU program identity and material formula not established.
Input SHA256 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d.

## Reproduction
[Probe-ZA-EmbeddedShaderFont.py](../../../scripts/Probe-ZA-EmbeddedShaderFont.py) · [CI](../../../.github/workflows/za-embedded-shader-font.yml)
```powershell
python -m pip install capstone==5.0.7
python scripts/Probe-ZA-EmbeddedShaderFont.py
```
Output .za-work/native-font-shader/evidence.json; no original shader/font exports. New CI pending.

## First method audit diagnostic
[45782829027](https://github.com/969981/ZA_Resources/actions/runs/45782829027) failed while reading a bounded direct callee prefix at 0x3163EE0: 256 bytes crossed its mapped executable LOAD end. The two BNSH header/declared-length checks had passed before that exception, but complete output was not written. Fix 329affb197f5bfaeaa56631b41f432a820703ce0 clamps instruction read length to segment remaining bytes, aligned down to 4. [Rerun 45782921774](https://github.com/969981/ZA_Resources/actions/runs/45782921774). No changes to source assets.

## Method audit actual PASS
[45782921774](https://github.com/969981/ZA_Resources/actions/runs/45782921774), commit 329affb197f5bfaeaa56631b41f432a820703ce0. Both declared BNSH ranges validated:
| VA | Size | Internal name | SHA256 |
|---|---:|---|---|
| 0x3EF8000 | 29752 (0x7438) | font_BuildinShader_Nvn_Binary | ba534a7a521a467a3723613e22bace0bb9c8439a6d828dbabf40794f2a17d407 |
| 0x3F00000 | 147936 (0x241E0) | ui2d_BuildinShader_Nvn_Binary | c286bdcfd846993989d0769205f3f88f6a39de1697fe4381133db317a718f586 |
Both grsc at +96 and multiple _DIC magic hits. Font strings: aVertex, gl_VertexID, oColor, ShaderParamBlackWhiteInterpolation, ShaderParam, uTextureSrc. UI2D strings: uTexture0, aVertexIndex, uConstantBufferForVertexShader, uConstantBufferForPixelShader, o_Color, uTexture1. Names strongly establish intended subsystem; no final shader variation/constant-buffer/formula evidence yet.
- 0x2626190 ADRP x0, 0x3EF8000; 0x2626194 ADD x0,x0,0 (pointer-return candidate, need confirm RET).
- 0x2626AFC ADRP x24, font BNSH; 0x2626B08 MOV x0,x24; 0x2626B14 BL 0x3163EE0; 0x2626B20 MOV w23,0x7438; 0x2626B28 MOV x1,x24; 0x2626B2C MOV x2,x23; 0x2626B34 MOV x0,x19; 0x2626B38 BL 0x3161510; 0x2626B40 BL 0x2694A68.
- 0x2666AD4 ADRP x24, UI2D BNSH; 0x2666AE4 MOV x0,x24; 0x2666AFC BL 0x3163EE0; 0x2666B00 MOV w26,0x41E0; 0x2666B10 BL 0x26313E8; 0x2666B14 MOV x1,x24; 0x2666B18 MOV x2,x26; 0x2666B20 BL 0x3161510. Note 0x41E0 differs from declared 0x241E0; inspect full instruction stream before interpreting copy length.
Primary ResFont and ResFontBase tables each have offset-to-top 0 and 39 contiguous executable entries. Shared slot17 0x261B930 and slot18 0x261B9E0 call 0x261B780; 0xffff fallback test, resource pointer [this+0x20], file base candidate [this+0x18], linked ranges with u16 first/last indices, stride 3 for slot17 and stride 6 candidate slot18. These suggest codepoint-to-glyph and metric access, not UV yet. Slot19 0x261BAAC seed. 325ebae22ff0998f2a942d4c34ac1e86b931c73f expands unique method evidence and outgoing branch targets; pending new CI. 

## Glyph method chain actual PASS
[45782999095](https://github.com/969981/ZA_Resources/actions/runs/45782999095) PASS, commit 325ebae22ff0998f2a942d4c34ac1e86b931c73f. ResFontBase slot19 at 0x3C92300 points to 0x261BAAC: at 0x261BAC8 BL 0x261B780 (codepoint lookup), 0x261BACC–0x261BAFC 0xffff missing-index fallback and status, 0x261BB08 BL 0x261BB20 (glyph producer). 0x261B780 follows CMAP chains with u32 codepoint lower/upper bounds and method u16 0/1/2; direct branch loads base u16 at +0x10, adds codepoint-minus-range-start. Slot17 accesses 3-byte CWDH records and packs result; slot18 accesses 6-byte records, format/meaning pending.
Actual glyph producer 0x261BB20 contains UDIV at 0x261BB48/0x261BB7C/0x261BC3C/0x261BC4C, MSUB at 0x261BC40/0x261BC58 and MADD at 0x261BC5C/0x261BC64. These provide an actual coordinate arithmetic lead, not yet a confirmed formula. Commit 27c50677fbb36e1d0fe3a11aae00bae524038577 adds full bounded windows covering alternative branches and 0x2666AFC copy/setup sequence.
