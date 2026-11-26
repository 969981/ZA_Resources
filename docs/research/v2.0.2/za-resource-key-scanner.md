---
title: ZA 2.0.2 全量静态资源键扫描及原生查找机制
tags: [ZA, ARM64, ZAResourceKeyScanner, ZATypeImageResolver]
status: static-key-scan-pass-runtime-unverified
---
# 图标选择器第五阶段
[[za-icon-registration]] · [[za-icon-selector-deep]] · [[za-native-pokemon-icon-selector]]

## CI 验收
[45771079875](https://github.com/969981/ZA_Resources/actions/runs/45771079875) 首次扫描取得键记录，但反汇编读取跨 section 边界返回 None，导致 job failure。修复后 [45771150185](https://github.com/969981/ZA_Resources/actions/runs/45771150185) success。第三轮增加精确常量字节及工厂函数窗口 [45771258289](https://github.com/969981/ZA_Resources/actions/runs/45771258289) 已 success，统计完全一致。
ELF SHA256 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d。
扫描所有文件支持 PT_LOAD 中 8 字节对齐的 24 字节记录；字符串目标为 allocated file-backed sections，要求 1..4096 bytes、无内嵌 NUL、末尾 NUL、原生 seed Hash 完全相符。支持 AArch64 R_AARCH64_RELATIVE RELA addend。未覆盖动态对象、其他布局、未对齐/超长/非 NUL 字符串、未映射数据和其他重定位方式。
| Metric | Count |
|---|---:|
| Aligned positions | 8322158 |
| Bounded length | 62578 |
| Valid pointer and terminator | 7680 |
| Exact hash | 7318 |
| Unique strings and hashes | 5268 |
| Different strings with same hash | 0 |
| Duplicate records beyond one per string | 2050 |
| Image/UI keyword candidates | 147 |
| Selected record-base ADR/ADRP+ADD candidates | 21 |

Segments: PT_LOAD[0] 51789680 bytes, 6473708 positions, 0 matches; PT_LOAD[1] 10870784 bytes, 1358846 positions, 0 matches; PT_LOAD[2] 3916848 bytes, 489604 positions, 7318 matches. .data 7197, other mapped PT_LOAD[2] 121.
Categories: other_string 6200, other_path 971, mark_or_badge_candidate 54, other_icon 61, item_icon 4, ui_pokemon_node 25, pokemon_icon_offset 1, pokemon_icon 1, other_image_or_ui 1. Keyword labels not proof of resource types; one confirmed BNTX path for default pm0000, no additional Pokemon BNTX path among this layout. This does not exclude other static layouts.
Artifacts: [ZAResourceKeys](https://github.com/969981/ZA_Resources/actions/runs/45771150185/artifacts/15094191329). resource-keys.jsonl, image-key-candidates.jsonl, hash-collisions.jsonl, image-key-xrefs.jsonl, functions.jsonl, type-path-constants.jsonl, type-table-contiguous.jsonl, summary.json.
## 0x421C
Actual function 0x421C..0x422C: ldr q0,[x0]; ldr x9,[x0,#0x10]; stp x9,xzr,[x8,#0x10]; str q0,[x8]; ret.
Copies 24-byte static hash/name/length to 32-byte indirect-result wrapper and clears +0x18. No lookup in this function. Dynamic field +0x18 semantics unresolved.
## 0x1B4E240
0x164C8 forwards to 0x1B4E240 with manager VA 0x3FA0F00 and Hash in X5. X8 saved in X26. Low hash byte selects per-bucket region manager+0x840+((hash&0xff)<<10), lock byte manager+0x22+((hash&0xff)*8); atomic byte lock using LDAXRB/STXRB and thread ID bits. At 0x1B4E370..0x1B4E3BC loads 16-byte control group, SIMD equality, mask extraction, full 64-bit hash comparison; branch to 0x1B4E4B8 on equality. Hash-table lookup/intern candidate, not direct BNTX lookup. Allocation/refcount/collision comparison semantics to verify.
## 0x2D69DB4
Bounded function 0x2D69DB4..0x2D69E20 calls 0x2A02B0 with five strings and lengths. Native parts [17-byte literal at 0x323C7BA, descriptor1.Name, 1-byte literal at 0x325F8F2, descriptor2.Name, 11-byte literal at 0x32CA665]. C-string reads grptxt_icon_type_, _, _color_00^q. Exact byte slices verified in third run. Parent 0x2D69D00 uses input low8 as 24-byte table index and calls 0x88624C with X2=0x32A21D2, W1=2; numeric formatting semantics not assumed. Table start 0x3E27BE0 contains 26 contiguous validated records:
0 normal, 1 kakutou, 2 hikou, 3 doku, 4 jimen, 5 iwa, 6 mushi, 7 ghost, 8 hagane, 9 honoo, 10 mizu, 11 kusa, 12 denki, 13 esper, 14 koori, 15 dragon, 16 aku, 17 yousei, 18 none, 19 mahi, 20 nemuri, 21 koori, 22 yakedo, 23 doku, 24 dokudoku, 25 hinshi.
First 18 correspond standard types, 18 none, 19..25 status names; contiguous records alone do not prove all 26 valid indexes for the type consumer. Actual key is grptxt UI name, not a BNTX path.
## Reproduce
python -m pip install capstone==5.0.3
python scripts/Scan-ZA-ResourceKeys.py
## Next
Trace true UI widget texture binding, resource manager lookup, raw Catalog→asset selector, and layout archives containing generated grptxt nodes; distinguish physical textures from UI resource strings. Cross-check raw icon decoder 1655 RGBA hashes with independent decoder. Runtime validation not performed.

## Third run verified
[45771258289](https://github.com/969981/ZA_Resources/actions/runs/45771258289) success; [artifact](https://github.com/969981/ZA_Resources/actions/runs/45771258289/artifacts/15093184679). Counts identical. Exact 17/1/11 byte parts are grptxt_icon_type_, _, _color_00^q (suffix includes literal ^q). Input at 0x32A21D2 is "0"; 0x88624C uses W1=2 and nested calls to 0x31607C0 with format pointer 0x32B5474, then seeded hash and 0x283F0. Fourth run verified the literal at 0x32B5474 is %%%s%dd. With input string 0 and width 2, standard printf-style evaluation yields %02d; the second formatting call renders the type index. This is a statically reconstructed UI group-text key, not a BNTX path or runtime trace.
0x1B4E4B8: 16-byte slot [hash, object pointer], loads pointer +8 and writes into output, tests object flags at +8 &3; nonzero increments packed atomic word by 0x400. 0x1B4E4F4 onward tests len<0x6f, uses bucket+0x48 freelist or virtual allocator with len+0x19, alignment 8; initializes object hash at +0. Intern table candidate, no BNTX data load proved.
0x38B90: input points to object pointer; produces 32-byte view [hash, string ptr, length, owner pointer]; nonzero low flags cause atomic +0x400, string offsets selected +0x11 or +0x18; length via 0x2E-byte[+0x3F] or 0x6E-byte[+0x7F] or u32[+0x14]. 0x421C same view layout with owner=null. Native packed flags/length/storage branches preserved; no assumption of exact C++ type name.
Three extension-matching records in keyword candidates: item_1785 full BNTX path, pm0000 full BNTX path, ".bntx" extension-only string at record 0x3E28138 (hash AE49EDF5D08552A1). Important next target: xrefs to this suffix record and adjacent string keys, beyond UI node paths.

## Fourth run verified: complete type key template
[45771348067](https://github.com/969981/ZA_Resources/actions/runs/45771348067) success; [final artifact](https://github.com/969981/ZA_Resources/actions/runs/45771348067/artifacts/15094490714). 7318 records, 5268 unique strings and 0 distinct-string hash collisions reproduced.
0x32B5474 exact bytes 25 25 25 73 25 64 64 = %%%s%dd. At 0x8862C4 the first formatting call uses "0", 2; at 0x8862D8 second uses low-byte type ID. Reconstructed standard formatting for type 0: grptxt_icon_type_00_normal_color_00^q; type 9: grptxt_icon_type_09_honoo_color_00^q. 18 standard type names verified; none and status entries contiguous but legal index bounds not established. Next map generated keys to layout/font/texture consumers instead of treating them as standalone BNTX paths.
