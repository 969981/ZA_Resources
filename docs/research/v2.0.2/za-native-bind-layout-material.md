---
title: ZA 2.0.2 原生纹理绑定与布局材质索引
tags: [ZA, ARM64, BFLYT, BNTX, TextureBinding]
status: elf-pass-layout-sample-verified-full-material-audit-pending
---
# 图标选择器第八阶段
[[za-ui-archive-texture-producers]] · [[za-texture-binding]] · [[za-resource-key-scanner]]

## 上轮归档验收
[45772723593](https://github.com/969981/ZA_Resources/actions/runs/45772723593) and [45772818194](https://github.com/969981/ZA_Resources/actions/runs/45772818194): both ELF and archives jobs passed. [ZAUIArchiveAudit](https://github.com/969981/ZA_Resources/actions/runs/45772818194/artifacts/15094378626).
980/980 paths, 665/665 unique blobs, 27842 members, errors 0. 3352 BFLYT, 20798 BFLAN, 1952 BFCpx, 538 BNSH, 538 BUSHVT, 664 BNTX. 37849 pic1, 3230 mat1, 3188 txl1, 8237 prt1, 3105 cnt1, 24967 usd1. ASCII UikitPokeIcon hits 0; P_icon_00 3729; switch_icon 164. These are member/section counts across distinct blobs, not unique images. Exact ASCII absence does not exclude alternate spelling/metadata.

## Correction: fixed item IDs
0x2D32C3C function entry. Input W1=0 -> W20=0x31C (796), W1=1 -> W20=0x31B (795), other values branch to 0x2D32DA4. Therefore this caller is a two-state fixed item selector, not a general held-item producer. 0x886240 loads literal "0" at 0x32A21D2 and tail branches to 0x88624C. Verified format %%%s%dd at 0x32B5474; width 4 produces %04d. 0x2D32D18 -> 0x2D335CC -> 0x2D33624 -> 0x3D45CC. Both original assets exist:
- ui/tex/icon_item/item_0795/item_0795.bntx, 45160 B, Git blob 3e829c5af5fe65eb76d93550ea98c4d49683aa67
- ui/tex/icon_item/item_0796/item_0796.bntx, 45160 B, Git blob 285833562f347aff09a6c3bd6db23ce4e4117f2c
General path formatting verified; arbitrary ItemID selection not proven.

## Native bind
ELF SHA256 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d.
[Run 45774314436](https://github.com/969981/ZA_Resources/actions/runs/45774314436) ELF job success, [artifact](https://github.com/969981/ZA_Resources/actions/runs/45774314436/artifacts/15095560788). 6 windows. Direct branch counts 0x3D45CC=23, 0xF65720=47, 0x10000C8=1, 0x2B50FC=17, 0x886240=82.
0x3D45CC..0x3D46B4:
- 0x3D4610 calls 0xF65720 with context+0xA8/+0xB0/+0xB8 handles; checks both output pointers.
- 0x3D4634 calls 0x10000C8(node view, flag), returns signed index/ID (missing branch -1). Function searches object+0x2D8 with composite key [node hash, flag], 0x1006080 and 0x10061E0; reads result+0x20.
- 0x3D4648 calls 0x2B50FC(texture path view) indirect output. Checks string prefix against 0x3EEE3A4; if comparison differs, constructs prefix+input via native seeded hash and 0x164C8, then calls 0xD3160. Actual prefix bytes not yet extracted; not asserting mount name.
- 0x3D465C calls 0xFFF5E0(object, node index, processed path, flag), returns W0. This is the next shared binding candidate, GPU write not proven.
- 0x796520 releases temporary path object; virtual +0x18 releases acquired handles; returns acquired-both AND binding result.
0xF65720 uses global table pointer at 0x3EC21C8, low 20 bits of input handle, stride 0x20, atomic halfword counters at slot-relative +0x28 and +0x2A, compares full handle at +0x10; output is two acquired pointers and third forwarded field. Actual type names unverified.

## Independent sample: pic1 -> mat1 -> txl1 -> BRTI
box/box_list_00.arc, member blyt/box_box_button_00.bflyt. txl1 at 288, mat1 at 388. Native material offsets section-relative; texture string offsets relative to txl1+12. pic1 material index at section+100; UV count candidate +102. Material names first 28 bytes, flags candidate +28, first texture-index candidate +44 (0x2C), not +40. First texture slot gated by flags&3 candidate; only sample-validated, not complete flag semantics.
| pic1 | material index | mat1 name | +0x2C u16 | txl1 / BRTI |
|---|---:|---|---:|---|
| P_bg_catch_ds_00 | 1 | P_bg_catch_ds_00 | 3 | common_wt_16px_00^r |
| P_bg_catch_00 | 2 | P_bg_catch_00 | 3 | common_wt_16px_00^r |
| P_icon_00 | 0 | P_icon_00 | 2 | box_icon_list_00^u |
| P_cursor_01 | 3 | P_cursor_01 | 1 | box_cursor_01^s |
| P_cursor_00 | 4 | P_cursor_00 | 0 | box_cursor_00^t |
All four exact txl1 names matched BRTI in timg/__Combined.bntx (13 BRTIs). BRTI indices 0,1,2,7 respectively for txl indices 0,1,2,3; sizes 84x68,108x94,120x120,16x16. Thus txl indices are not BRTI indices. P_icon_00 static placeholder does not establish runtime Pokemon texture. Materials flags 0x80155 (212 B) and 0x15 (84 B), all first maps fit +0x2C in this sample. cnt1 at 3748 includes literal [GF]UIKitButton twice; alternate component registration names should be inspected. No UikitPokeIcon attribution.

## Full layout scanner
scripts/Scan-ZA-LayoutBindings.py, scripts/Probe-ZA-NativeTextureBind.py. [Initial run](https://github.com/969981/ZA_Resources/actions/runs/45774314436) layouts checkout pending at last check. Initial material candidate +40 was incorrect in sample; corrected to +44 gated by low flag bits at commit 51b2842. [Corrected run](https://github.com/969981/ZA_Resources/actions/runs/45774453537) pending. No full material or pixel parity claims. Exact local name joins exclude other ARC/external lookup and dynamic textures.
Next trace 0xFFF5E0, 0xD3160, 0x1006080, actual prefix bytes 0x3EEE3A4; validate full layouts, component tokens, material flags and texture count. Runtime not tested.
