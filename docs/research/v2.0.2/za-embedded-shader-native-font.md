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
