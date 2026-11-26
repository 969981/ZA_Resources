---
title: ZA 2.0.2 原生图标节点路径、字符串键及注册记录
tags: [ZA, UikitPokeIcon, ARM64, ResourceKey, PokemonIcon]
status: static-hash-records-verified-selector-unverified
---
# 图标选择器第四阶段
[[za-icon-selector-deep]] · [[za-native-pokemon-icon-selector]]

## 验收
[45769813328](https://github.com/969981/ZA_Resources/actions/runs/45769813328) 和 [45769935085](https://github.com/969981/ZA_Resources/actions/runs/45769935085) 均 success。ELF SHA256 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d。7 字符串、50 邻接 qword、8 数据指针、25 ADRP 引用候选、13 指令窗口；11 个连续字符串键候选的 Hash 和长度均全部匹配。静态证据，不宣称运行时选择器已恢复。

## UI 节点路径
0x32F5F06 = /switch_icon (12 bytes); 0x323BCAD = /P_icon_00 (10 bytes). 0x2CD73BC/0x2CD7418 通过 0x2A02B0 拼接输入与常量。0x2A02B0..0x2A0384 (95 direct branch refs) 按 X2 计数读取 X3 长度数组、X4 指针数组，以 0x3161510 逐段复制，再写 NUL；函数体未见 X1 容量检查，不可当安全接口。0x2CD6CC8..0x2CD6D1C 包装该路径并调用 0x7DEFC0，不是 BNTX 选择函数。
0x3160690 为导入跳板（GOT 0x3EE8048），调用语义与 strlen 一致，未验证动态符号名。

## ZAStringHash / 24-byte static string key
0x7DEFC0..0x7DF0B8 非空路径用 0xCBF29CE484222645 初始值及 0x100000001B3 乘数，逐 byte XOR/乘，u64 wrap。与标准 FNV-1a 初始值不同。空/null 输入走 0x40FE128 全局对象，不能假定返回 ABI 与非空一致。238 条直接分支引用。
非空路径 0x7DF074 BL 0x164C8；X0=1、X1=长度、X2/X3=栈上字符串指针和长度的地址、X4=Hash、X8=输出位置。0x164C8 重排 X0..X4 至 X1..X5，装入 X0=0x3FA0F00 后尾调用 0x1B4E240。527 条直接分支引用；尚未证明动态对象完整布局/分配行为。
静态 .data 字符串键布局（相邻 24-byte records verified）:
| Offset | Type | Meaning |
|---|---|---|
| +0 | u64 | ZA seeded FNV-like Hash |
| +8 | u64 | string ELF VA |
| +16 | u64 | byte length excluding NUL |
| Size | 0x18 | fixed stride |
| Hash VA | String | Hash | Len |
|---|---|---|---:|
| 0x3E0ACA0 | world/exl/pokemon_icon_offset/pokemon_icon_offset/pokemon_icon_offset | 0xB8D1043EC7C29973 | 69 |
| 0x3E27BB0 | ui/tex/icon_item/item_1785/item_1785.bntx | 0x581F45E350F97EDF | 41 |
| 0x3E27BC8 | ik_pokemon/data/pm0000/pm0000_00_00/icon/pm0000_00_00_00_0.bntx | 0xCB169366F0936962 | 63 |
| 0x3E27BE0 | normal | 0xE5583797BEFA0B92 | 6 |
| 0x3E27BF8 | kakutou | 0x5EDC3C7F4DF1F34F | 7 |
| 0x3E27C10 | hikou | 0x2A0BA9BD0114A2E3 | 5 |
| 0x3E27C28 | doku | 0x4B541F62E9CFE048 | 4 |

## Adjacent consumers and boundary
0x3E0ACA8/0x3E27BD0 are +8 string pointers, not bases of registration objects. Correct record bases 0x3E0ACA0/0x3E27BC8. Neighboring 0x3E0AC40/58/70/88 are UI keys, consumers at 0x2CB4838/0x2CB485C/0x2CB48C4 etc use 0x421C. No direct reference to offset record itself confirmed.
0x2CB4958 and 0x2CB4998 assign vptr 0x3E0ACC8 at object+0 and address+0x88/+0xD8 to object+0x20/+0x28, call 0xA71C60 on object+0x100 and tail-call 0x5DDAE8. These are adjacent class lifecycle candidates, not proven UikitPokeIcon class. 0x2CB49D8 returns 0x3E0ADE8.
0x2D69D00..0x2D69DB0: low 8-bit input indexes table at 0x3E27BE0 with stride 0x18 (UMADDL at 0x2D69D68); table starts normal/kakutou/hikou/doku. This is a type-name resource path candidate, NOT direct default icon consumer. 0x2D69DB4 reads pointer+length pair at +8, builds 5 parts; continue recovering actual constants. No verified default/fallback condition yet.
UikitPokeIcon literal 0x3296760 unchanged; no proven class link or runtime trace.

## Reproduce
python -m pip install capstone==5.0.3
python scripts/Probe-ZA-IconRegistration.py
Artifact ZAIconRegistration contains functions, strings, hash-records, registration-neighborhood, pointer-candidates, xref-candidates and summary.

## Decode CI scope repair
Previous BNTX workflow blocked at git ls-tree -rlz (size queries on partial clone can lazily fetch large blobs). Added checked-out-icons mode and updated decode workflow; only checked-out raw Pokemon/item/donut BNTX. Does not certify full archive or full-tree inventory. New run 45769992160 pending at time of writing; no independent pixel parity claimed.

## Next
Trace 0x1B4E240, 0x421C and 0x2D69DB4, scan .data string-key records by exact hash/length and recover consumers by record base/hash; find true icon texture request inputs and fallback condition; same Build ID runtime trace needed for gender/shiny and four pm0770 special icons.
