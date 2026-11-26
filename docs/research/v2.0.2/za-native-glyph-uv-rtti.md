---
title: ZA NativeGlyphUVResolver 与原生 UI RTTI
tags: [ZA, Glyph, BC4, RTTI, BNSH, Obsidian]
status: font-sheet-parity-pass-native-uv-and-shader-unverified
---
# ZA NativeGlyphUVResolver / Native UI RTTI
[[za-glyph-hermite-shader-locators]] · [[za-font-shader-flts-edge-cases]] · [[za-dynamic-texture-flts-renderer]]

## 实际验收
[Run 45781558206](https://github.com/969981/ZA_Resources/actions/runs/45781558206) PASS，commit 579d2510e750bc943eeefc47b7a581e39cc804e1；[artifact 15098955261](https://github.com/969981/ZA_Resources/actions/runs/45781558206/artifacts/15098955261) SHA256 10ca00816c26267918f8e39929324f42b1b82566ffbe05d432d98952f8e29345。
8 BFFNT containers / 9 sheets; 5242880 Alpha pixels compared using Pillow DDS and independent scalar BC4 endpoint/interpolation implementation; 0 differences, max error 0. Both paths share the original GOB deswizzle, so this validates BC4 interpolation, not independent swizzle or native framebuffer. The 52_64_bold BNTX declares 1052776 bytes, TGLP per-sheet raw field 526388, count 2, two 1024x1024 layers with verified storage stride 524288 each. No need to truncate or modify native files.
## Glyph UV diagnostic
16 models: row/column order, vertical flip including crop orientation, four gap/border choices. Rankings prioritize digit occupancy, space emptiness, valid crops, sum absolute alpha bbox width versus CWDH, edge hits. This is a diagnostic, NOT native UV determination or OCR. Every font has a candidate with ten nonempty digits. Best candidates:
| Font | mode | gap/border | width error sum |
|---|---|---|---:|
| 24_28 | row_flip | 1/1 | 0 |
| 26_30 | row_flip | 1/1 | 27 |
| 26_30_bold | row | 1/1 | 927 |
| 30_34_bold | column | 0/0 | 670 |
| 38_42_bold | column | 0/0 | 1338 |
| 42_52_bold | row_flip | 1/0 | 1715 |
| 52_64_bold | row_flip | 1/1 | 1284 |
| num | column | 0/0 | 505 |
24_28 matches 218 mappings, 216 nonempty, one empty U+0020, all nonempty widths match, but 216 edge hits. 26_30 same counts, width error 27. Other font scores are inconsistent; do not select a global coordinate formula or claim correct glyph identity. Native glyph UV, metrics semantics, crop orientation and GOB parity still need evidence.
## Native ELF
SHA256 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d.
[Previous scan 45775604194](https://github.com/969981/ZA_Resources/actions/runs/45775604194) ELF step PASS (overall font failed): 5 string hits, 4 ADRP+ADD candidates. .bfcpx xref 0x1283564; .bffnt xrefs 0x128B2DC and 0x128B34C. These are reference PCs, not function entry points. imgui_texture2d.trsha name not verified as ui2d shader.
New RTTI scan: 68 names, 68 typeinfo candidates, 0 vtable candidates in first pass. Examples (string VA): nn::font::ResFont 0x336E766, ResFontBase 0x336E779, RectDrawer 0x336E94C, nn::ui2d::AnimTransformBasic 0x336E9A7, DrawInfo 0x336EA5A, CaptureTexture 0x336EAC4, Picture 0x336EE65, TextBox 0x336EEBD. Typeinfo candidates ResFont 0x3C92240, ResFontBase 0x3C92398, RectDrawer 0x3C92B48, DrawInfo 0x3C92E00. Candidate typeinfo objects, not verified virtual functions.
Two embedded BNSH magic+BOM header candidates VA 0x3EF8000 (file offset 66030008), 0x3F00000 (66062776). Need validate header section sizes, shader code and native binding; not yet attributed to nn::ui2d.
Second pass commit 4822215529e478ba2792e59ca3950393c80f5d5a adds raw aligned typeinfo-pointer search and embedded BNSH address xrefs. Pending new run. No actual material formula recovered.
## Scripts
[Audit-ZA-NativeGlyphUV.py](../../../scripts/Audit-ZA-NativeGlyphUV.py), [Probe-ZA-NativeUIRTTI.py](../../../scripts/Probe-ZA-NativeUIRTTI.py), [CI](../../../.github/workflows/za-glyph-uv-native-rtti.yml). Local metadata under .za-work/glyph-uv/ and .za-work/ui-rtti/. No font or shader bytes published. Next: native font UV getter, RTTI pointer representation and vtable producer, embedded shader consumer, compare render output to runtime frames.
