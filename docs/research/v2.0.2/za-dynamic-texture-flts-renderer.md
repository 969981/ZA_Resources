---
title: ZA DynamicTextureResolver FLTS 与 NativeMaterialRenderer
tags: [ZA, CTL1, FLTS, Hermite, BFLYT, renderer, Obsidian]
status: native-samples-confirmed-render-hypothesis-ci-pending
---
# ZA 动态纹理与材质成品恢复
[[za-native-material-texture-resolver]] · [[za-ui-layout-material-animation]] · [[za-image-resource-pack]]

## 2026-11-26 已验收基线
[45772417428](https://github.com/969981/ZA_Resources/actions/runs/45772417428) 两 job PASS。native-material 实际读取 54578 records，52818 boundary-fit candidates，1760 partial。0x815/84 bytes 1139 条，和 0x15 同尺寸，0x800 疑似无附加字段开关，语义未知。基线 7401 unique decoded pixel groups，不代表 7401 个最终 UI 图标。

## ctl1 原始字节证据
源路径前缀 Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/ui/data/，直接读取提交 dc11df724ae56dc979d662275b7454df916404fd 的 ARC。
| ARC / layout | section offset (relative FLYT) | section size | capture count |
|---|---:|---:|---:|
| hud_ball/hud_ball_00.arc / hud_ball_00.bflyt | 1212 | 156 | 2 |
| btl_app/btl_app_waza_last_01.arc / btl_app_waza_last_01.bflyt | 7412 | 252 | 4 |
| quest_info/resident_ui.arc / resident_ui.bflyt | 1100 | 816 | 11 |
ctl1 +8 u16 count; +12 records, each 48 bytes. record +0 and +4 u32 offsets relative section start: capture name and source pane name. +8..+47 retained raw; float at +44 = 1.0 in these 17 samples; semantics candidate. hud_ball T_guide_00_D→T_guide_00 (txt1 +6056, msg_ui_btl_ball_cancel), T_name_00_D→T_name_00 (txt1 +2792). waza T_00_D..T_03_D→T_00..T_03. resident_ui T_num_00..02_D, T_quest_00..01_D, T_quest_no_00..01_D, T_reward_00..02_D, T_reward_m_00_D → respective source pane. fnl1 offsets relative +12 table, e.g. system24_jpn.fcpx, system26_bold_jpn.fcpx, system30_bold_jpn.fcpx. txt1 font index +90 and material index +88 are candidate fields. Runtime text content, font glyph layout and GPU capture remain unknown.
Crosswalk checks exact blob + layout member + texture name against previous 912 MISSING records, not merely _D suffix. Fixed-width pane names preserved even without NUL in this independent scanner; old FLYT parser errors not automatically declared fixed.

## FLTS 原版 Hermite 曲线证据
btl_app_waza_last_01.arc:
- anim/btl_app_waza_last_01_keep.bflan, P_btn_ef_00..03, target index=1, property=1, data type=2, frame/value/tangent triples (0,-0.8000000119,0.0533333346), (30,0.8000000119,0.0533333346).
- P_type_base_21, index=1, property=1, (0,0,0.0333333351), (30,1,0.0333333351).
- select_00, P_sel_ef_03, index=1, property=3, (0,1,0.0178571437), (28,1.5,0.0178571437).
- reset_00, P_sel_ef_03..05, properties 3/4, one key (0,1,0).
Data type 2 key stride 12 (three little-endian f32). Property 1 translation candidate, 3/4 scale candidates; exact SRT component, units and loop semantics require native/runtime validation. Hermite candidate with tangents multiplied by frame delta, endpoint clamp, rejects non-strict ordering. Full 4796 FLTS tag entries may expand into more property tracks. Do not equate tag counts with track counts.

## NativeMaterialRenderer 隔离原型
[Render-ZA-UIMaterialCandidates.py](../../../scripts/Render-ZA-UIMaterialCandidates.py) only flags 0x15, single texture, full UV, identity SRT, uniform vertex color, verified sample coordinate bytes and sampler 04/04. Compare stored-byte space per-channel two hypotheses:
- multiply: q = round(x * color1 / 255)
- endpoint: q = round((color0 * (255-x) + color1 * x)/255)
Then uniform vertex modulation and local pane alpha. Both preserve identity endpoints in synthetic fixtures. No runtime shader evidence, no parent alpha, sampling, pane transforms, multiple textures, blend framebuffer, text, color space or premultiplication validation. Texture-size isolated preview, not game-equivalent UI. Source RGBA, material SHA, source compressed storage hash, result hashes, colors and candidate model disagreement retained. Optional local PNG under .za-work only; no CI upload of game pictures.

## Reproduction
```powershell
python scripts/Audit-ZA-DynamicTextures.py --self-test
python scripts/Audit-ZA-DynamicTextures.py --missing .za-work/ui-resolver/layout-refs.jsonl
python -m pip install Pillow==12.3.0
python scripts/Render-ZA-UIMaterialCandidates.py --self-test
python scripts/Render-ZA-UIMaterialCandidates.py
# 有权处理的本地图片，另一个目录
python scripts/Render-ZA-UIMaterialCandidates.py --out .za-work/ui-render-local --export
```
[CI](../../../.github/workflows/za-ui-dynamic-render.yml) two jobs. capture-flts scans raw ARC and pinned previous missing refs; isolated-render scans six explicit sample ARC. Artifacts metadata only. Results pending.
Next: full capture and FLTS counts, remaining 1760 material flags, runtime shader evidence, native font and locale text, material/frame binding and independent pixel parity before promoting isolated hypotheses.

## 2026-11-26 isolated-render 实际验收
[Run 45773359748](https://github.com/969981/ZA_Resources/actions/runs/45773359748) isolated-render job PASS。6 ARC / 197 pic1；92 recipes eligible and rendered, 91 unsupported flags, 11 nonidentity SRT, 3 non-full UV；multiply 30 changed from source, endpoint 31 changed, 6 recipes models disagree, each model 70 unique output pixel groups. No PNG publication. HUD P_01 uses icon_key_b_00^t with color0=(54,54,76,0), color1=(255,255,255,255), local alpha=255; the two hypotheses yield different SHA256. P_00 uses color1=(0,0,0,255), local alpha=31 and both models agree. Model agreement is not native verification. capture-flts full job pending at documentation update.
