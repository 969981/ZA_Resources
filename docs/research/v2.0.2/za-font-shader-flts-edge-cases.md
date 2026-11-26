---
title: ZA 原版字体、Shader 与 FLTS 边界研究
tags: [ZA, FCPX, FFNT, FLTS, material, Obsidian]
status: font-and-edge-audit-pass-shader-runtime-unverified
---
# ZA Font / Shader / FLTS Edge Cases
[[za-dynamic-texture-flts-renderer]] · [[za-native-material-texture-resolver]] · [[za-image-resource-pack]]
## 实际验收
[45773359748](https://github.com/969981/ZA_Resources/actions/runs/45773359748) PASS：912/912 missing txl refs exact ctl1 match, 156 names, 907 unique source, 5 missing. 4796 FLTS tags, 10216 tracks, 67096 keys. [45774282941](https://github.com/969981/ZA_Resources/actions/runs/45774282941) PASS: artifact [15095785295](https://github.com/969981/ZA_Resources/actions/runs/45774282941/artifacts/15095785295), SHA256 b4c73d856fae85f2af20fbc4b13c5742f335e4c21525eac640bca9ade960cc71.
## Font containers
原始目录 Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/ui/font/bin/。80 files: 63 BFCpx, 8 BFFNT, 8 BFOTF, 1 settings.bin. 48 FCPX reference offsets match, 15 raw scan only, 8 FFNT parsed, 1744 glyph width records and 1744 codepoint records, no parser errors. No glyph atlas decode or native font rendering. No fonts published.
FCPX header magic FCPX, version 0x09030000, header 0x14. Direct bytes of system24_jpn.bfcpx (172 bytes), system24_simp.bfcpx (260 bytes), bmp_din_26_30.bfcpx (64 bytes), ref 4ff2dffd0432757ebf17c7b0bc3339598cfbe9d1:
- offsets base +0x18; mode 0 at +0x18 bitmap name ref +0x1C/+0x24; mode 1 size float +0x1C, count candidate +0x24; name offsets +0x44/+0x5C with 40-byte stride. Other modes retain raw.
- system24_simp links or_font.otf and nintendo_udsg-r_ext_zh-cn_003.bfttf / nintendo_udsg-r_org_zh-cn_003.bfttf. Across inventory 44 external references to four names (also nintendo_udjxh-db_zh-tw_003.bfttf and nintendo_udsg-r_ko_003.bfttf). Not found under current font/bin; no assumption about system firmware or other sources.
- font_din_26_30.bffnt 153456 bytes, version 0x04010000, FINF at 20, TGLP at 52, CWDH at 139368, CMAP at 140040/140068/140096, KRNG at 140340. CWDH signed left, unsigned width, signed advance; CMAP direct/table/sparse candidate records. TGLP glyph pixels, KRNG semantics pending.
- BFOTF does not begin plain OTTO in sample UniversNextPro-Cond; wrapper encoding unknown. Do not rename and assume decoded.
## 0x815 material
1139/1139 exact 84-byte base block boundary (44+4+20+16), no tail, unknown bit 0x800. Direct native sample pokedex/pokedex_detail.arc material W_b_form_00RT and W_b_dexnum_00RT: flags 0x815, map index 11, sampler 04/04, identity SRT. Separate structure boundary classification; no shader semantics or rendering eligibility promotion. 75 additional partial records flags 0x800, size 44, pending boundary-specific validation.
## FLTS duplicate frames
7307 strict; 2898 duplicate-conflict (different values and/or tangents); 11 duplicate-identical; zero descending. Example bag/bag_top_00.arc anim/cmn_temochi_icon_01_keep.bflan target P_icon_03, SRT index 1 property 1: (0,-0.8,0.04), (40,0.8,0.04), (40,0.8,0), (99,0.8,0). Likely incoming/outgoing tangent or discontinuity; preserve order and duplicates; do not dedup or choose native endpoint behavior without runtime evidence.
## 5 capture gaps
All C_capture_00, common_bg/common_bg_00.arc, cross_fade/cross_fade.arc, transition/transition_dim_00.arc, transition/transition_dim_simple_00.arc, transition/transition_rankup_00.arc. Direct bytes confirm cpt1 pane in first two, size 84; offsets 1468/576; ctl1 offsets 980/316. Remaining three could not be fully fetched/parsed in direct sample tool; full CI needed. Added cpt1 to pane scanner; rerun pending.
## Shader
396 path candidates, broad includes texture/material files under shader paths, not 396 shader programs. system_resource/gfx2/shader/NX64/env_ikkaku/{material,special,system}; BNSH/TRSHA pairs include imgui, imgui_texture2d, effect, copy_image, default. No evidence that imgui is game NW layout shader. Next inspect main.elf strings/xrefs and program binding; never infer endpoint formula from filename. Runtime framebuffer parity absent.
## Reproduction
[Audit-ZA-FontShader.py](../../../scripts/Audit-ZA-FontShader.py), [Audit-ZA-UIEdgeCases.py](../../../scripts/Audit-ZA-UIEdgeCases.py), [CI](../../../.github/workflows/za-ui-font-edge.yml). Outputs inventory.json, flag815.jsonl, flts-order.jsonl, summary.json. Pinned artifact inputs, metadata only.
