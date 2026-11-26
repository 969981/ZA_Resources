---
title: ZAImageResources 分类资源包与 UI ARC 审计
tags: [ZA, images, SARC, BNTX, Obsidian]
status: native-samples-confirmed-full-audit-pending
---
# ZAImageResources
[[za-image-resource-audit]] · [[za-bntx-pokemon-icon-mapping]] · [[za-native-pokemon-icon-selector]]

## 原版直接字节证据（2026-11-26）
研究基线 b5e561d7b04bc3f4e7118a63fd3df0221b74f371。源路径前缀 Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/ui/data/。通过 GitHub 原始二进制读取 little-endian SARC/SFAT/SFNT 与 BNTX BRTI 指针。
| ARC | Git blob | bytes | SFAT 成员 | BNTX 偏移 | BRTI |
|---|---|---:|---:|---:|---:|
| dummy/dummy_icon_type.arc | 84041be6b92126a55c665705111493c35d98d487 | 340096 | 2 | 20480 | 54 |
| hud_ball/hud_ball_00.arc | bdf5ae0b5c05afdc5a9e9abff342f31fa0bcd762 | 463664 | 25 | 385024 | 7 |
| btl_app/btl_app_trainer_ball_00.arc | 5435dda2c4e4965b4f22aafa57f4da68f29b6a2b | 111868 | 20 | 77824 | 4 |
| btl_app/btl_app_hit_marker_00.arc | 8390126ea32c24acd0aa73ca8547b4f7c4425f19 | 47868 | 7 | 24576 | 未枚举 |

均包含 timg/__Combined.bntx。属性容器完整枚举 54 个 BRTI：18 个 60×60 BC4 (0x1D01, selector 1/1/1/2)，18 个 36×36 BC3 色彩图标，18 个 150×36 BC3 文字图标 (0x1C01, selector 2/3/4/5)。名称从 grptxt_icon_type_00_normal_00^s 到 grptxt_icon_type_17_yousei_00^s；01 kakutou、02 hikou、03 doku、04 jimen、05 iwa、06 mushi、07 ghost、08 hagane、09 honoo、10 mizu、11 kusa、12 denki、13 esper、14 koori、15 dragon、16 aku。原始名称 token 并非已证明的运行时 TypeID。
训练家球 UI 的 btl_app_icon_ball_00^t 为 32×32 BC5 (2/2/2/3)；不能认定为独立 BallID 图标。hud_ball 有 dummy_icon_item^t 等占位、按钮纹理。BFLYT/BFLAN 原生存在，但 UV、材质、动画选择及 shader 语义待证。

## 本地分类输出约定
.za-work/ZAImageResources/{pokemon,items,balls,types,moves,badges,ribbons,donuts,characters,maps,ui,atlases,manifests,database,docs}。
每个来源保留原始路径、Git blob、源 SHA256、ARC 成员偏移与 SHA256、BRTI 名称、像素 SHA256、通道选择、尺寸及解码状态。相同 blob 去重计算但保留所有路径。SQLite 分离 source/member/texture/mapping，ID 语义未经证实保留空值。PNG 仅在有权处理的本地输出，不提交游戏素材。atlases/docs 预留并不代表 UV 裁切完成。

## P0/P1 验收
- [ ] 全量 980 ARC / 665 独立 blob 基线对账；分卷单独标记。
- [ ] BC1/2/3/4/5/7 像素解码、BC4/5 选择器重组及双解码器对账。
- [ ] BFLYT 材质/UV、BFLAN 选择帧与图集裁切。
- [ ] 535 ItemID 与 379 道具 BNTX、共享图标、占位与缺失。
- [ ] 属性、球、奖章、招式分类、缎带证章原生 ID 消费者，禁止猜测。
- [ ] 宝可梦 catalog/config/selector 与四张未关联纹理。
- [ ] 甜甜圈 ID 和普通/big 变体；最终与 HOME、SWSH 统一。
