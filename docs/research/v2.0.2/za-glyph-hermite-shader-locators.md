---
title: ZA 字形 BNTX、FLTS 插值与 ELF Shader 定位
tags: [ZA, FFNT, BNTX, FLTS, ELF, Obsidian]
status: native-sample-evidence-full-ci-pending
---
# ZA 字形纹理、Hermite 与 Shader 定位
[[za-font-shader-flts-edge-cases]] · [[za-dynamic-texture-flts-renderer]] · [[za-image-resource-pack]]

## cpt1 全量回归
[45774395175](https://github.com/969981/ZA_Resources/actions/runs/45774395175) 两 job PASS，commit 207bd9ef92cdcf392329a75eeba9080f277be06a：912/912 unique source, 156 distinct capture names, 912 missing TXL refs matched. 10216 FLTS tracks, 67096 keys unchanged. Static source closed only for successfully parsed layouts; native framebuffer not verified.

## TGLP embedded BNTX 原版证据
直接读取 ref fa39938351749c6bc98031b2d3fa97828a9474aa 的 ui/font/bin 下五个 BFFNT。
| Font | cell width x height | grid columns x rows | sheet dimensions |
|---|---|---|---|
| font_din_24_28 | 28x30 | 8x33 | 256x1024 |
| font_din_26_30 | 29x33 | 8x30 | 256x1024 |
| font_din_26_30_bold | 31x32 | 16x15 | 512x512 |
| font_din_30_34_bold | 35x36 | 14x27 | 512x1024 |
| font_din_num | 26x26 | 9x37 | 256x1024 |
TGLP at file+52 in these samples. +8/+9 cell width/height, +10 u8 sheet count=1, +11 raw maximum width candidate, +12 u32 BNTX byte length, +16 raw u16 (NOT sheet count), +18 format raw=12, +20/+22 columns/rows, +24/+26 dimensions, +28 absolute file pointer=4096. At +4096 BNTX magic; first two inspected BRTI names "0", BC4 0x1D01, channels [1,1,1,2], image_dim=5 (array view), array_count=1, depth=1, block height log2=4, 1 mip, storage 131072 bytes. Single-layer array storage reused existing decoder after strict guards; no font redistribution. Candidate crop x=1+col*(cellw+1), y=1+row*(cellh+1); actual native glyph UV not confirmed. CI validates all 8 sheets and records alpha bboxes, hash and CWDH metrics; optional local PNG only.

## FLTS repeated frame evaluator
Preserve original duplicate groups. Three explicit hypotheses: first (retain first), last (retain last), split (incoming first, outgoing last; exact frame last). Evaluate at 1/4,1/2,3/4 interval, record disagreements. Neither candidate promoted to native. Example bag P_icon_03 frame 40 same value +0.8 with incoming tangent .04 and outgoing 0; split has plausible interpretation, but actual native evaluator needed. 
## Shader ELF
Read-only SHA-pinned main.elf 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d. Search layout/capture/combiner/texture/font strings in nonexec LOAD, RELA exact addend references, direct ADR and nearby ADRP+ADD candidates. No function ID inferred from approximate xref; no GPU code/formula verified. 
## Reproduction
- [Decode-ZA-BFFNTGlyphs.py](../../../scripts/Decode-ZA-BFFNTGlyphs.py)
- [Audit-ZA-FLTSHermite.py](../../../scripts/Audit-ZA-FLTSHermite.py)
- [Probe-ZA-UIShaderELF.py](../../../scripts/Probe-ZA-UIShaderELF.py)
- [Workflow](../../../.github/workflows/za-glyph-hermite-shader.yml)
```powershell
python -m pip install Pillow==12.3.0
python scripts/Decode-ZA-BFFNTGlyphs.py
python scripts/Audit-ZA-FLTSHermite.py --self-test
python scripts/Audit-ZA-FLTSHermite.py
python scripts/Probe-ZA-UIShaderELF.py
```
Outputs .za-work/font-glyphs, .za-work/flts-eval, .za-work/ui-shader-elf. CI metadata only, pending actual results. Native glyph spacing, shader program bindings, repeat-frame evaluator, KRNG and final screenshot parity remain open.
