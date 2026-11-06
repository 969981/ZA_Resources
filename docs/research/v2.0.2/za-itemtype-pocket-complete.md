---
title: ZA v2.0.2 535 条道具 ItemType × Pocket 全分组
aliases: [ZA ItemType 分类, ZA Pocket 分类]
tags: [Pokemon/ZA, 逆向/道具, FlatBuffers, Obsidian]
version: v2.0.2
status: CONFIRMED_GROUPING_DERIVED_MEANINGS
updated: 2026-11-06
---

# ZA v2.0.2：535 条道具 ItemType × Pocket 全分组

> [!success] 真实资源分组
> 来源：[`item_data.bin`](../../../Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/world/exl/item_data/item_data/item_data.bin) → `ItemDataArray.fbs` 的 535 条真实记录，按 `Id` 关联简体中文/英文 `itemname.dat.json`。以下 **12 个非空组合涵盖全部 535 条，不重不漏**。研究分类标签是从内容归纳，不等于已逆向命名的 ItemType 枚举。若同一名称重复出现，请以 ID 区分。

## 分类透视表

| ItemType | Pocket 0 | Pocket 1 | Pocket 2 | Pocket 3 | Pocket 4 | Pocket 5 | Pocket 6 | Pocket 7 | 合计 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | — | — | — | — | 29 | — | — | — | 29 |
| 1 | — | — | — | — | — | 66 | — | — | 66 |
| 2 | 19 | — | 39 | — | — | — | — | — | 58 |
| 3 | — | — | 6 | 7 | 15 | — | — | — | 28 |
| 4 | — | 26 | — | — | — | — | — | — | 26 |
| 5 | — | — | — | — | — | — | 160 | — | 160 |
| 6 | — | — | — | — | — | — | — | — | 0 |
| 7 | — | — | 68 | — | — | — | — | 92 | 160 |
| 8 | — | — | — | — | — | — | — | — | 0 |
| 9 | — | — | 8 | — | — | — | — | — | 8 |
| **合计** | 19 | 26 | 121 | 7 | 44 | 66 | 160 | 92 | **535** |

## 12 组语义汇总

| ItemType | Pocket | 条数 | 内容归纳（非游戏枚举原名） |
|---:|---:|---:|---|
| 0 | 4 | 29 | 重要/剧情/任务道具 |
| 1 | 5 | 66 | 树果 |
| 2 | 0 | 19 | 恢复 HP、状态与复活物品 |
| 2 | 2 | 39 | 能力培养（营养饮料/羽毛/糖果/薄荷） |
| 3 | 2 | 6 | 瓶盖、兑换货币与特殊素材 |
| 3 | 3 | 7 | 出售用贵重物与素材 |
| 3 | 4 | 15 | 卡娜莉玩偶（可收集类） |
| 4 | 1 | 26 | 精灵球 |
| 5 | 6 | 160 | 招式学习器 |
| 7 | 2 | 68 | 一般携带物、进化石、形态用物品 |
| 7 | 7 | 92 | Mega 石 |
| 9 | 2 | 8 | 进化用特殊道具及化石 |

## 推断边界

- `ItemType=0`：重要物品/剧情工具，实际包含钥匙、事件凭据、料理相关的特殊道具。
- `ItemType=1`：66 个树果，与 `Pocket=5` 完全对应。
- `ItemType=2`：同一类型分为恢复类 `Pocket=0`（19）与培养类 `Pocket=2`（39），因此 **ItemType 本身不等于 Pocket**。
- `ItemType=3`：多种零散素材、售卖贵重物、货币与玩偶，分布在 Pocket 2/3/4。
- `ItemType=4`：26 个精灵球；`ItemType=5`：160 个招式学习器。
- `ItemType=7`：一般携带物及特殊石类，68 个 Pocket 2 与 92 个 Pocket 7（Mega 石）；**红蓝宝珠 ItemType=7、Pocket=2**。
- `ItemType=9`：8 个特殊进化材料或化石，不能简单理解为“全部携带道具”。
- `ItemType=6` / `8`：本次 535 条记录中未出现，定义在枚举不代表游戏主表一定有数据。
- `CanNotHold` 与 `Pocket` 是独立字段，不能直接当作 Link Trade 是否允许转移的证据。

## 全量按组列出全部 535 个 ID（简中、英文及数量标记）

### ItemType=0 · Pocket=4 · 重要/剧情/任务道具（29 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 632 | 闪耀护符 | Shiny Charm | 1 | false |
| 700 | 电梯钥匙 | Elevator Key | 1 | false |
| 765 | 惩戒之壶 | Prison Bottle | 1 | false |
| 847 | 基格尔德多面体 | Zygarde Cube | 1 | false |
| 1278 | 洛托姆型录 | Rotom Catalog | 999 | true |
| 2588 | ２０２号客房的钥匙 | Key to Room 202 | 1 | false |
| 2589 | 厉害密阿雷格雷派饼 | Super Lumiose Galette | 1 | false |
| 2590 | 研究所的钥匙卡Ａ | Lab Key Card A | 1 | false |
| 2591 | 研究所的钥匙卡Ｂ | Lab Key Card B | 1 | false |
| 2592 | 研究所的钥匙卡Ｃ | Lab Key Card C | 1 | false |
| 2595 | 小石头 | Pebble | 1 | false |
| 2596 | 纪念戒指 | Cherished Ring | 1 | false |
| 2597 | 签名玩偶 | Autographed Plush | 1 | false |
| 2598 | 美味垃圾 | Tasty Trash | 1 | false |
| 2599 | 活力小树枝 | Revitalizing Twig | 1 | false |
| 2600 | 玳萝的遗忘物 | Lida’s Things | 1 | false |
| 2601 | 密阿雷黄油 | Lumiosian Butter | 1 | false |
| 2602 | 超级黄油 | Nice Butter | 1 | false |
| 2603 | 高级黄油 | Great Butter | 1 | false |
| 2604 | 究极黄油 | Amazing Butter | 1 | false |
| 2605 | 大师黄油 | Supreme Butter | 1 | false |
| 2606 | 异次元黄油 | Hyperspace Butter | 1 | false |
| 2607 | 丰缘的粗盐 | Hoennian Salt | 1 | false |
| 2608 | 黑香料 | Épice Noire | 1 | false |
| 2609 | 奥利瓦油 | Arboliva Oil | 1 | false |
| 2610 | 噼里啪啦糖果 | Popping Candy | 1 | false |
| 2611 | 重要信件 | Important Letter | 1 | false |
| 2612 | 纪念戒指 | Cherished Ring | 1 | false |
| 2613 | 脏围巾 | Dirty Scarf | 1 | false |

### ItemType=1 · Pocket=5 · 树果（66 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 149 | 樱子果 | Cheri Berry | 999 | false |
| 150 | 零余果 | Chesto Berry | 999 | false |
| 151 | 桃桃果 | Pecha Berry | 999 | false |
| 152 | 莓莓果 | Rawst Berry | 999 | false |
| 153 | 利木果 | Aspear Berry | 999 | false |
| 155 | 橙橙果 | Oran Berry | 999 | false |
| 156 | 柿仔果 | Persim Berry | 999 | false |
| 157 | 木子果 | Lum Berry | 999 | false |
| 158 | 文柚果 | Sitrus Berry | 999 | false |
| 169 | 榴石果 | Pomeg Berry | 999 | false |
| 170 | 藻根果 | Kelpsy Berry | 999 | false |
| 171 | 比巴果 | Qualot Berry | 999 | false |
| 172 | 哈密果 | Hondew Berry | 999 | false |
| 173 | 萄葡果 | Grepa Berry | 999 | false |
| 174 | 茄番果 | Tamato Berry | 999 | false |
| 184 | 巧可果 | Occa Berry | 999 | false |
| 185 | 千香果 | Passho Berry | 999 | false |
| 186 | 烛木果 | Wacan Berry | 999 | false |
| 187 | 罗子果 | Rindo Berry | 999 | false |
| 188 | 番荔果 | Yache Berry | 999 | false |
| 189 | 莲蒲果 | Chople Berry | 999 | false |
| 190 | 通通果 | Kebia Berry | 999 | false |
| 191 | 腰木果 | Shuca Berry | 999 | false |
| 192 | 棱瓜果 | Coba Berry | 999 | false |
| 193 | 福禄果 | Payapa Berry | 999 | false |
| 194 | 扁樱果 | Tanga Berry | 999 | false |
| 195 | 草蚕果 | Charti Berry | 999 | false |
| 196 | 佛柑果 | Kasib Berry | 999 | false |
| 197 | 莓榴果 | Haban Berry | 999 | false |
| 198 | 刺耳果 | Colbur Berry | 999 | false |
| 199 | 霹霹果 | Babiri Berry | 999 | false |
| 200 | 灯浆果 | Chilan Berry | 999 | false |
| 686 | 洛玫果 | Roseli Berry | 999 | false |
| 2651 | 异次元樱子果 | Hyper Cheri Berry | 999 | false |
| 2652 | 异次元零余果 | Hyper Chesto Berry | 999 | false |
| 2653 | 异次元桃桃果 | Hyper Pecha Berry | 999 | false |
| 2654 | 异次元莓莓果 | Hyper Rawst Berry | 999 | false |
| 2655 | 异次元利木果 | Hyper Aspear Berry | 999 | false |
| 2656 | 异次元橙橙果 | Hyper Oran Berry | 999 | false |
| 2657 | 异次元柿仔果 | Hyper Persim Berry | 999 | false |
| 2658 | 异次元木子果 | Hyper Lum Berry | 999 | false |
| 2659 | 异次元文柚果 | Hyper Sitrus Berry | 999 | false |
| 2660 | 异次元榴石果 | Hyper Pomeg Berry | 999 | false |
| 2661 | 异次元藻根果 | Hyper Kelpsy Berry | 999 | false |
| 2662 | 异次元比巴果 | Hyper Qualot Berry | 999 | false |
| 2663 | 异次元哈密果 | Hyper Hondew Berry | 999 | false |
| 2664 | 异次元萄葡果 | Hyper Grepa Berry | 999 | false |
| 2665 | 异次元茄番果 | Hyper Tamato Berry | 999 | false |
| 2666 | 异次元巧可果 | Hyper Occa Berry | 999 | false |
| 2667 | 异次元千香果 | Hyper Passho Berry | 999 | false |
| 2668 | 异次元烛木果 | Hyper Wacan Berry | 999 | false |
| 2669 | 异次元罗子果 | Hyper Rindo Berry | 999 | false |
| 2670 | 异次元番荔果 | Hyper Yache Berry | 999 | false |
| 2671 | 异次元莲蒲果 | Hyper Chople Berry | 999 | false |
| 2672 | 异次元通通果 | Hyper Kebia Berry | 999 | false |
| 2673 | 异次元腰木果 | Hyper Shuca Berry | 999 | false |
| 2674 | 异次元棱瓜果 | Hyper Coba Berry | 999 | false |
| 2675 | 异次元福禄果 | Hyper Payapa Berry | 999 | false |
| 2676 | 异次元扁樱果 | Hyper Tanga Berry | 999 | false |
| 2677 | 异次元草蚕果 | Hyper Charti Berry | 999 | false |
| 2678 | 异次元佛柑果 | Hyper Kasib Berry | 999 | false |
| 2679 | 异次元莓榴果 | Hyper Haban Berry | 999 | false |
| 2680 | 异次元刺耳果 | Hyper Colbur Berry | 999 | false |
| 2681 | 异次元霹霹果 | Hyper Babiri Berry | 999 | false |
| 2682 | 异次元灯浆果 | Hyper Chilan Berry | 999 | false |
| 2683 | 异次元洛玫果 | Hyper Roseli Berry | 999 | false |

### ItemType=2 · Pocket=0 · 恢复 HP、状态与复活物品（19 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 17 | 伤药 | Potion | 999 | false |
| 18 | 解毒药 | Antidote | 999 | false |
| 19 | 灼伤药 | Burn Heal | 999 | false |
| 20 | 解冻药 | Ice Heal | 999 | false |
| 21 | 解眠药 | Awakening | 999 | false |
| 22 | 解麻药 | Paralyze Heal | 999 | false |
| 23 | 全复药 | Full Restore | 999 | false |
| 24 | 全满药 | Max Potion | 999 | false |
| 25 | 厉害伤药 | Hyper Potion | 999 | false |
| 26 | 好伤药 | Super Potion | 999 | false |
| 27 | 万灵药 | Full Heal | 999 | false |
| 28 | 活力碎片 | Revive | 999 | false |
| 29 | 活力块 | Max Revive | 999 | false |
| 30 | 美味之水 | Fresh Water | 999 | false |
| 31 | 劲爽汽水 | Soda Pop | 999 | false |
| 32 | 果汁牛奶 | Lemonade | 999 | false |
| 33 | 哞哞鲜奶 | Moomoo Milk | 999 | false |
| 708 | 密阿雷格雷派饼 | Lumiose Galette | 999 | false |
| 2684 | 卡娜莉面包 | Canari Bread | 999 | false |

### ItemType=2 · Pocket=2 · 能力培养（营养饮料/羽毛/糖果/薄荷）（39 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 45 | ＨＰ增强剂 | HP Up | 999 | false |
| 46 | 攻击增强剂 | Protein | 999 | false |
| 47 | 防御增强剂 | Iron | 999 | false |
| 48 | 速度增强剂 | Carbos | 999 | false |
| 49 | 特攻增强剂 | Calcium | 999 | false |
| 50 | 神奇糖果 | Rare Candy | 999 | false |
| 52 | 特防增强剂 | Zinc | 999 | false |
| 565 | 体力之羽 | Health Feather | 999 | false |
| 566 | 肌力之羽 | Muscle Feather | 999 | false |
| 567 | 抵抗之羽 | Resist Feather | 999 | false |
| 568 | 智力之羽 | Genius Feather | 999 | false |
| 569 | 精神之羽 | Clever Feather | 999 | false |
| 570 | 瞬发之羽 | Swift Feather | 999 | false |
| 1124 | 经验糖果ＸＳ | Exp. Candy XS | 999 | false |
| 1125 | 经验糖果Ｓ | Exp. Candy S | 999 | false |
| 1126 | 经验糖果Ｍ | Exp. Candy M | 999 | false |
| 1127 | 经验糖果Ｌ | Exp. Candy L | 999 | false |
| 1128 | 经验糖果ＸＬ | Exp. Candy XL | 999 | false |
| 1231 | 怕寂寞薄荷 | Lonely Mint | 999 | false |
| 1232 | 固执薄荷 | Adamant Mint | 999 | false |
| 1233 | 顽皮薄荷 | Naughty Mint | 999 | false |
| 1234 | 勇敢薄荷 | Brave Mint | 999 | false |
| 1235 | 大胆薄荷 | Bold Mint | 999 | false |
| 1236 | 淘气薄荷 | Impish Mint | 999 | false |
| 1237 | 乐天薄荷 | Lax Mint | 999 | false |
| 1238 | 悠闲薄荷 | Relaxed Mint | 999 | false |
| 1239 | 内敛薄荷 | Modest Mint | 999 | false |
| 1240 | 慢吞吞薄荷 | Mild Mint | 999 | false |
| 1241 | 马虎薄荷 | Rash Mint | 999 | false |
| 1242 | 冷静薄荷 | Quiet Mint | 999 | false |
| 1243 | 温和薄荷 | Calm Mint | 999 | false |
| 1244 | 温顺薄荷 | Gentle Mint | 999 | false |
| 1245 | 慎重薄荷 | Careful Mint | 999 | false |
| 1246 | 自大薄荷 | Sassy Mint | 999 | false |
| 1247 | 胆小薄荷 | Timid Mint | 999 | false |
| 1248 | 急躁薄荷 | Hasty Mint | 999 | false |
| 1249 | 爽朗薄荷 | Jolly Mint | 999 | false |
| 1250 | 天真薄荷 | Naive Mint | 999 | false |
| 1251 | 认真薄荷 | Serious Mint | 999 | false |

### ItemType=3 · Pocket=2 · 瓶盖、兑换货币与特殊素材（6 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 795 | 银色王冠 | Bottle Cap | 999 | false |
| 796 | 金色王冠 | Gold Bottle Cap | 999 | false |
| 2137 | 索财灵的硬币 | Gimmighoul Coin | 999 | true |
| 2558 | 精通种子 | Seed of Mastery | 999 | false |
| 2618 | 超级碎片 | Mega Shard | 9999 | false |
| 2619 | 彩色螺丝 | Colorful Screw | 999 | true |

### ItemType=3 · Pocket=3 · 出售用贵重物与素材（7 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 86 | 小蘑菇 | Tiny Mushroom | 999 | false |
| 88 | 珍珠 | Pearl | 999 | false |
| 89 | 大珍珠 | Big Pearl | 999 | false |
| 92 | 金珠 | Nugget | 999 | false |
| 571 | 美丽之羽 | Pretty Feather | 999 | false |
| 581 | 巨大金珠 | Big Nugget | 999 | false |
| 582 | 丸子珍珠 | Pearl String | 999 | false |

### ItemType=3 · Pocket=4 · 卡娜莉玩偶（可收集类）（15 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 2620 | 红色卡娜莉玩偶 | Red Canari Plush | 1 | false |
| 2621 | 红色卡娜莉玩偶 | Red Canari Plush | 1 | false |
| 2622 | 红色卡娜莉玩偶 | Red Canari Plush | 1 | false |
| 2623 | 金色卡娜莉玩偶 | Gold Canari Plush | 1 | false |
| 2624 | 金色卡娜莉玩偶 | Gold Canari Plush | 1 | false |
| 2625 | 金色卡娜莉玩偶 | Gold Canari Plush | 1 | false |
| 2626 | 粉红色卡娜莉玩偶 | Pink Canari Plush | 1 | false |
| 2627 | 粉红色卡娜莉玩偶 | Pink Canari Plush | 1 | false |
| 2628 | 粉红色卡娜莉玩偶 | Pink Canari Plush | 1 | false |
| 2629 | 绿色卡娜莉玩偶 | Green Canari Plush | 1 | false |
| 2630 | 绿色卡娜莉玩偶 | Green Canari Plush | 1 | false |
| 2631 | 绿色卡娜莉玩偶 | Green Canari Plush | 1 | false |
| 2632 | 蓝色卡娜莉玩偶 | Blue Canari Plush | 1 | false |
| 2633 | 蓝色卡娜莉玩偶 | Blue Canari Plush | 1 | false |
| 2634 | 蓝色卡娜莉玩偶 | Blue Canari Plush | 1 | false |

### ItemType=4 · Pocket=1 · 精灵球（26 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 1 | 大师球 | Master Ball | 999 | false |
| 2 | 高级球 | Ultra Ball | 999 | false |
| 3 | 超级球 | Great Ball | 999 | false |
| 4 | 精灵球 | Poké Ball | 999 | false |
| 5 | 狩猎球 | Safari Ball | 999 | false |
| 6 | 捕网球 | Net Ball | 999 | false |
| 7 | 潜水球 | Dive Ball | 999 | false |
| 8 | 巢穴球 | Nest Ball | 999 | false |
| 9 | 重复球 | Repeat Ball | 999 | false |
| 10 | 计时球 | Timer Ball | 999 | false |
| 11 | 豪华球 | Luxury Ball | 999 | false |
| 12 | 纪念球 | Premier Ball | 999 | false |
| 13 | 黑暗球 | Dusk Ball | 999 | false |
| 14 | 治愈球 | Heal Ball | 999 | false |
| 15 | 先机球 | Quick Ball | 999 | false |
| 16 | 贵重球 | Cherish Ball | 999 | false |
| 492 | 速度球 | Fast Ball | 999 | false |
| 493 | 等级球 | Level Ball | 999 | false |
| 494 | 诱饵球 | Lure Ball | 999 | false |
| 495 | 沉重球 | Heavy Ball | 999 | false |
| 496 | 甜蜜球 | Love Ball | 999 | false |
| 497 | 友友球 | Friend Ball | 999 | false |
| 498 | 月亮球 | Moon Ball | 999 | false |
| 499 | 竞赛球 | Sport Ball | 999 | false |
| 576 | 梦境球 | Dream Ball | 999 | false |
| 851 | 究极球 | Beast Ball | 999 | false |

### ItemType=5 · Pocket=6 · 招式学习器（160 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 328 | 招式学习器００１ | TM001 | 1 | false |
| 329 | 招式学习器００２ | TM002 | 1 | false |
| 330 | 招式学习器００３ | TM003 | 1 | false |
| 331 | 招式学习器００４ | TM004 | 1 | false |
| 332 | 招式学习器００５ | TM005 | 1 | false |
| 333 | 招式学习器００６ | TM006 | 1 | false |
| 334 | 招式学习器００７ | TM007 | 1 | false |
| 335 | 招式学习器００８ | TM008 | 1 | false |
| 336 | 招式学习器００９ | TM009 | 1 | false |
| 337 | 招式学习器０１０ | TM010 | 1 | false |
| 338 | 招式学习器０１１ | TM011 | 1 | false |
| 339 | 招式学习器０１２ | TM012 | 1 | false |
| 340 | 招式学习器０１３ | TM013 | 1 | false |
| 341 | 招式学习器０１４ | TM014 | 1 | false |
| 342 | 招式学习器０１５ | TM015 | 1 | false |
| 343 | 招式学习器０１６ | TM016 | 1 | false |
| 344 | 招式学习器０１７ | TM017 | 1 | false |
| 345 | 招式学习器０１８ | TM018 | 1 | false |
| 346 | 招式学习器０１９ | TM019 | 1 | false |
| 347 | 招式学习器０２０ | TM020 | 1 | false |
| 348 | 招式学习器０２１ | TM021 | 1 | false |
| 349 | 招式学习器０２２ | TM022 | 1 | false |
| 350 | 招式学习器０２３ | TM023 | 1 | false |
| 351 | 招式学习器０２４ | TM024 | 1 | false |
| 352 | 招式学习器０２５ | TM025 | 1 | false |
| 353 | 招式学习器０２６ | TM026 | 1 | false |
| 354 | 招式学习器０２７ | TM027 | 1 | false |
| 355 | 招式学习器０２８ | TM028 | 1 | false |
| 356 | 招式学习器０２９ | TM029 | 1 | false |
| 357 | 招式学习器０３０ | TM030 | 1 | false |
| 358 | 招式学习器０３１ | TM031 | 1 | false |
| 359 | 招式学习器０３２ | TM032 | 1 | false |
| 360 | 招式学习器０３３ | TM033 | 1 | false |
| 361 | 招式学习器０３４ | TM034 | 1 | false |
| 362 | 招式学习器０３５ | TM035 | 1 | false |
| 363 | 招式学习器０３６ | TM036 | 1 | false |
| 364 | 招式学习器０３７ | TM037 | 1 | false |
| 365 | 招式学习器０３８ | TM038 | 1 | false |
| 366 | 招式学习器０３９ | TM039 | 1 | false |
| 367 | 招式学习器０４０ | TM040 | 1 | false |
| 368 | 招式学习器０４１ | TM041 | 1 | false |
| 369 | 招式学习器０４２ | TM042 | 1 | false |
| 370 | 招式学习器０４３ | TM043 | 1 | false |
| 371 | 招式学习器０４４ | TM044 | 1 | false |
| 372 | 招式学习器０４５ | TM045 | 1 | false |
| 373 | 招式学习器０４６ | TM046 | 1 | false |
| 374 | 招式学习器０４７ | TM047 | 1 | false |
| 375 | 招式学习器０４８ | TM048 | 1 | false |
| 376 | 招式学习器０４９ | TM049 | 1 | false |
| 377 | 招式学习器０５０ | TM050 | 1 | false |
| 378 | 招式学习器０５１ | TM051 | 1 | false |
| 379 | 招式学习器０５２ | TM052 | 1 | false |
| 380 | 招式学习器０５３ | TM053 | 1 | false |
| 381 | 招式学习器０５４ | TM054 | 1 | false |
| 382 | 招式学习器０５５ | TM055 | 1 | false |
| 383 | 招式学习器０５６ | TM056 | 1 | false |
| 384 | 招式学习器０５７ | TM057 | 1 | false |
| 385 | 招式学习器０５８ | TM058 | 1 | false |
| 386 | 招式学习器０５９ | TM059 | 1 | false |
| 387 | 招式学习器０６０ | TM060 | 1 | false |
| 388 | 招式学习器０６１ | TM061 | 1 | false |
| 389 | 招式学习器０６２ | TM062 | 1 | false |
| 390 | 招式学习器０６３ | TM063 | 1 | false |
| 391 | 招式学习器０６４ | TM064 | 1 | false |
| 392 | 招式学习器０６５ | TM065 | 1 | false |
| 393 | 招式学习器０６６ | TM066 | 1 | false |
| 394 | 招式学习器０６７ | TM067 | 1 | false |
| 395 | 招式学习器０６８ | TM068 | 1 | false |
| 396 | 招式学习器０６９ | TM069 | 1 | false |
| 397 | 招式学习器０７０ | TM070 | 1 | false |
| 398 | 招式学习器０７１ | TM071 | 1 | false |
| 399 | 招式学习器０７２ | TM072 | 1 | false |
| 400 | 招式学习器０７３ | TM073 | 1 | false |
| 401 | 招式学习器０７４ | TM074 | 1 | false |
| 402 | 招式学习器０７５ | TM075 | 1 | false |
| 403 | 招式学习器０７６ | TM076 | 1 | false |
| 404 | 招式学习器０７７ | TM077 | 1 | false |
| 405 | 招式学习器０７８ | TM078 | 1 | false |
| 406 | 招式学习器０７９ | TM079 | 1 | false |
| 407 | 招式学习器０８０ | TM080 | 1 | false |
| 408 | 招式学习器０８１ | TM081 | 1 | false |
| 409 | 招式学习器０８２ | TM082 | 1 | false |
| 410 | 招式学习器０８３ | TM083 | 1 | false |
| 411 | 招式学习器０８４ | TM084 | 1 | false |
| 412 | 招式学习器０８５ | TM085 | 1 | false |
| 413 | 招式学习器０８６ | TM086 | 1 | false |
| 414 | 招式学习器０８７ | TM087 | 1 | false |
| 415 | 招式学习器０８８ | TM088 | 1 | false |
| 416 | 招式学习器０８９ | TM089 | 1 | false |
| 417 | 招式学习器０９０ | TM090 | 1 | false |
| 418 | 招式学习器０９１ | TM091 | 1 | false |
| 419 | 招式学习器０９２ | TM092 | 1 | false |
| 618 | 招式学习器０９３ | TM093 | 1 | false |
| 619 | 招式学习器０９４ | TM094 | 1 | false |
| 620 | 招式学习器０９５ | TM095 | 1 | false |
| 690 | 招式学习器０９６ | TM096 | 1 | false |
| 691 | 招式学习器０９７ | TM097 | 1 | false |
| 692 | 招式学习器０９８ | TM098 | 1 | false |
| 693 | 招式学习器０９９ | TM099 | 1 | false |
| 2160 | 招式学习器１００ | TM100 | 1 | false |
| 2162 | 招式学习器１０２ | TM102 | 1 | false |
| 2163 | 招式学习器１０３ | TM103 | 1 | false |
| 2164 | 招式学习器１０４ | TM104 | 1 | false |
| 2165 | 招式学习器１０５ | TM105 | 1 | false |
| 2166 | 招式学习器１０６ | TM106 | 1 | false |
| 2167 | 招式学习器１０７ | TM107 | 1 | false |
| 2168 | 招式学习器１０８ | TM108 | 1 | false |
| 2169 | 招式学习器１０９ | TM109 | 1 | false |
| 2170 | 招式学习器１１０ | TM110 | 1 | false |
| 2171 | 招式学习器１１１ | TM111 | 1 | false |
| 2172 | 招式学习器１１２ | TM112 | 1 | false |
| 2173 | 招式学习器１１３ | TM113 | 1 | false |
| 2174 | 招式学习器１１４ | TM114 | 1 | false |
| 2175 | 招式学习器１１５ | TM115 | 1 | false |
| 2176 | 招式学习器１１６ | TM116 | 1 | false |
| 2177 | 招式学习器１１７ | TM117 | 1 | false |
| 2178 | 招式学习器１１８ | TM118 | 1 | false |
| 2179 | 招式学习器１１９ | TM119 | 1 | false |
| 2180 | 招式学习器１２０ | TM120 | 1 | false |
| 2181 | 招式学习器１２１ | TM121 | 1 | false |
| 2182 | 招式学习器１２２ | TM122 | 1 | false |
| 2183 | 招式学习器１２３ | TM123 | 1 | false |
| 2184 | 招式学习器１２４ | TM124 | 1 | false |
| 2185 | 招式学习器１２５ | TM125 | 1 | false |
| 2186 | 招式学习器１２６ | TM126 | 1 | false |
| 2187 | 招式学习器１２７ | TM127 | 1 | false |
| 2188 | 招式学习器１２８ | TM128 | 1 | false |
| 2189 | 招式学习器１２９ | TM129 | 1 | false |
| 2190 | 招式学习器１３０ | TM130 | 1 | false |
| 2191 | 招式学习器１３１ | TM131 | 1 | false |
| 2192 | 招式学习器１３２ | TM132 | 1 | false |
| 2193 | 招式学习器１３３ | TM133 | 1 | false |
| 2194 | 招式学习器１３４ | TM134 | 1 | false |
| 2195 | 招式学习器１３５ | TM135 | 1 | false |
| 2196 | 招式学习器１３６ | TM136 | 1 | false |
| 2197 | 招式学习器１３７ | TM137 | 1 | false |
| 2198 | 招式学习器１３８ | TM138 | 1 | false |
| 2199 | 招式学习器１３９ | TM139 | 1 | false |
| 2200 | 招式学习器１４０ | TM140 | 1 | false |
| 2201 | 招式学习器１４１ | TM141 | 1 | false |
| 2202 | 招式学习器１４２ | TM142 | 1 | false |
| 2203 | 招式学习器１４３ | TM143 | 1 | false |
| 2204 | 招式学习器１４４ | TM144 | 1 | false |
| 2205 | 招式学习器１４５ | TM145 | 1 | false |
| 2206 | 招式学习器１４６ | TM146 | 1 | false |
| 2207 | 招式学习器１４７ | TM147 | 1 | false |
| 2208 | 招式学习器１４８ | TM148 | 1 | false |
| 2209 | 招式学习器１４９ | TM149 | 1 | false |
| 2210 | 招式学习器１５０ | TM150 | 1 | false |
| 2211 | 招式学习器１５１ | TM151 | 1 | false |
| 2212 | 招式学习器１５２ | TM152 | 1 | false |
| 2213 | 招式学习器１５３ | TM153 | 1 | false |
| 2214 | 招式学习器１５４ | TM154 | 1 | false |
| 2215 | 招式学习器１５５ | TM155 | 1 | false |
| 2216 | 招式学习器１５６ | TM156 | 1 | false |
| 2217 | 招式学习器１５７ | TM157 | 1 | false |
| 2218 | 招式学习器１５８ | TM158 | 1 | false |
| 2219 | 招式学习器１５９ | TM159 | 1 | false |
| 2220 | 招式学习器１６０ | TM160 | 1 | false |
| 2221 | 招式学习器１６１ | TM161 | 1 | false |

### ItemType=7 · Pocket=2 · 一般携带物、进化石、形态用物品（68 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 80 | 日之石 | Sun Stone | 999 | false |
| 81 | 月之石 | Moon Stone | 999 | false |
| 82 | 火之石 | Fire Stone | 999 | false |
| 83 | 雷之石 | Thunder Stone | 999 | false |
| 84 | 水之石 | Water Stone | 999 | false |
| 85 | 叶之石 | Leaf Stone | 999 | false |
| 107 | 光之石 | Shiny Stone | 999 | false |
| 108 | 暗之石 | Dusk Stone | 999 | false |
| 109 | 觉醒之石 | Dawn Stone | 999 | false |
| 116 | 水流卡带 | Douse Drive | 999 | false |
| 117 | 闪电卡带 | Shock Drive | 999 | false |
| 118 | 火焰卡带 | Burn Drive | 999 | false |
| 119 | 冰冻卡带 | Chill Drive | 999 | false |
| 214 | 白色香草 | White Herb | 999 | false |
| 217 | 先制之爪 | Quick Claw | 999 | false |
| 218 | 安抚之铃 | Soothe Bell | 999 | false |
| 221 | 王者之证 | King’s Rock | 999 | false |
| 222 | 银粉 | Silver Powder | 999 | false |
| 230 | 气势头带 | Focus Band | 999 | false |
| 231 | 幸运蛋 | Lucky Egg | 999 | false |
| 232 | 焦点镜 | Scope Lens | 999 | false |
| 233 | 金属膜 | Metal Coat | 999 | false |
| 234 | 吃剩的东西 | Leftovers | 999 | false |
| 236 | 电气球 | Light Ball | 999 | false |
| 237 | 柔软沙子 | Soft Sand | 999 | false |
| 238 | 硬石头 | Hard Stone | 999 | false |
| 239 | 奇迹种子 | Miracle Seed | 999 | false |
| 240 | 黑色眼镜 | Black Glasses | 999 | false |
| 241 | 黑带 | Black Belt | 999 | false |
| 242 | 磁铁 | Magnet | 999 | false |
| 243 | 神秘水滴 | Mystic Water | 999 | false |
| 244 | 锐利鸟嘴 | Sharp Beak | 999 | false |
| 245 | 毒针 | Poison Barb | 999 | false |
| 246 | 不融冰 | Never-Melt Ice | 999 | false |
| 247 | 咒术之符 | Spell Tag | 999 | false |
| 248 | 弯曲的汤匙 | Twisted Spoon | 999 | false |
| 249 | 木炭 | Charcoal | 999 | false |
| 250 | 龙之牙 | Dragon Fang | 999 | false |
| 251 | 丝绸围巾 | Silk Scarf | 999 | false |
| 252 | 升级数据 | Upgrade | 999 | false |
| 253 | 贝壳之铃 | Shell Bell | 999 | false |
| 258 | 粗骨头 | Thick Club | 999 | false |
| 259 | 大葱 | Leek | 999 | false |
| 266 | 力量头带 | Muscle Band | 999 | false |
| 267 | 博识眼镜 | Wise Glasses | 999 | false |
| 268 | 达人带 | Expert Belt | 999 | false |
| 270 | 生命宝珠 | Life Orb | 999 | false |
| 275 | 气势披带 | Focus Sash | 999 | false |
| 289 | 力量护腕 | Power Bracer | 999 | false |
| 290 | 力量腰带 | Power Belt | 999 | false |
| 291 | 力量镜 | Power Lens | 999 | false |
| 292 | 力量束带 | Power Band | 999 | false |
| 293 | 力量护踝 | Power Anklet | 999 | false |
| 294 | 力量负重 | Power Weight | 999 | false |
| 296 | 大根茎 | Big Root | 999 | false |
| 324 | 可疑补丁 | Dubious Disc | 999 | false |
| 534 | 朱红色宝珠 | Red Orb | 999 | false |
| 535 | 靛蓝色宝珠 | Blue Orb | 999 | false |
| 537 | 美丽鳞片 | Prism Scale | 999 | false |
| 538 | 进化奇石 | Eviolite | 999 | false |
| 540 | 凸凸头盔 | Rocky Helmet | 999 | false |
| 564 | 一般宝石 | Normal Gem | 999 | false |
| 639 | 弱点保险 | Weakness Policy | 999 | false |
| 640 | 突击背心 | Assault Vest | 999 | false |
| 646 | 泡沫奶油 | Whipped Dream | 999 | false |
| 647 | 香袋 | Sachet | 999 | false |
| 849 | 冰之石 | Ice Stone | 999 | false |
| 2401 | 妖精之羽 | Fairy Feather | 999 | false |

### ItemType=7 · Pocket=7 · Mega 石（92 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 656 | 耿鬼进化石 | Gengarite | 1 | false |
| 657 | 沙奈朵进化石 | Gardevoirite | 1 | false |
| 658 | 电龙进化石 | Ampharosite | 1 | false |
| 659 | 妙蛙花进化石 | Venusaurite | 1 | false |
| 660 | 喷火龙进化石Ｘ | Charizardite X | 1 | false |
| 661 | 水箭龟进化石 | Blastoisinite | 1 | false |
| 662 | 超梦进化石Ｘ | Mewtwonite X | 1 | false |
| 663 | 超梦进化石Ｙ | Mewtwonite Y | 1 | false |
| 664 | 火焰鸡进化石 | Blazikenite | 1 | false |
| 665 | 恰雷姆进化石 | Medichamite | 1 | false |
| 666 | 黑鲁加进化石 | Houndoominite | 1 | false |
| 667 | 波士可多拉进化石 | Aggronite | 1 | false |
| 668 | 诅咒娃娃进化石 | Banettite | 1 | false |
| 669 | 班基拉斯进化石 | Tyranitarite | 1 | false |
| 670 | 巨钳螳螂进化石 | Scizorite | 1 | false |
| 671 | 凯罗斯进化石 | Pinsirite | 1 | false |
| 672 | 化石翼龙进化石 | Aerodactylite | 1 | false |
| 673 | 路卡利欧进化石 | Lucarionite | 1 | false |
| 674 | 暴雪王进化石 | Abomasite | 1 | false |
| 675 | 袋兽进化石 | Kangaskhanite | 1 | false |
| 676 | 暴鲤龙进化石 | Gyaradosite | 1 | false |
| 677 | 阿勃梭鲁进化石 | Absolite | 1 | false |
| 678 | 喷火龙进化石Ｙ | Charizardite Y | 1 | false |
| 679 | 胡地进化石 | Alakazite | 1 | false |
| 680 | 赫拉克罗斯进化石 | Heracronite | 1 | false |
| 681 | 大嘴娃进化石 | Mawilite | 1 | false |
| 682 | 雷电兽进化石 | Manectite | 1 | false |
| 683 | 烈咬陆鲨进化石 | Garchompite | 1 | false |
| 684 | 拉帝亚斯进化石 | Latiasite | 1 | false |
| 685 | 拉帝欧斯进化石 | Latiosite | 1 | false |
| 752 | 巨沼怪进化石 | Swampertite | 1 | false |
| 753 | 蜥蜴王进化石 | Sceptilite | 1 | false |
| 754 | 勾魂眼进化石 | Sablenite | 1 | false |
| 755 | 七夕青鸟进化石 | Altarianite | 1 | false |
| 756 | 艾路雷朵进化石 | Galladite | 1 | false |
| 757 | 差不多娃娃进化石 | Audinite | 1 | false |
| 758 | 巨金怪进化石 | Metagrossite | 1 | false |
| 759 | 巨牙鲨进化石 | Sharpedonite | 1 | false |
| 760 | 呆壳兽进化石 | Slowbronite | 1 | false |
| 761 | 大钢蛇进化石 | Steelixite | 1 | false |
| 762 | 大比鸟进化石 | Pidgeotite | 1 | false |
| 763 | 冰鬼护进化石 | Glalitite | 1 | false |
| 764 | 蒂安希进化石 | Diancite | 1 | false |
| 767 | 喷火驼进化石 | Cameruptite | 1 | false |
| 768 | 长耳兔进化石 | Lopunnite | 1 | false |
| 769 | 暴飞龙进化石 | Salamencite | 1 | false |
| 770 | 大针蜂进化石 | Beedrillite | 1 | false |
| 2559 | 皮可西进化石 | Clefablite | 1 | false |
| 2560 | 大食花进化石 | Victreebelite | 1 | false |
| 2561 | 宝石海星进化石 | Starminite | 1 | false |
| 2562 | 快龙进化石 | Dragoninite | 1 | false |
| 2563 | 大竺葵进化石 | Meganiumite | 1 | false |
| 2564 | 大力鳄进化石 | Feraligite | 1 | false |
| 2565 | 盔甲鸟进化石 | Skarmorite | 1 | false |
| 2566 | 雪妖女进化石 | Froslassite | 1 | false |
| 2567 | 席多蓝恩进化石 | Heatranite | 1 | false |
| 2568 | 达克莱伊进化石 | Darkranite | 1 | false |
| 2569 | 炎武王进化石 | Emboarite | 1 | false |
| 2570 | 龙头地鼠进化石 | Excadrite | 1 | false |
| 2571 | 蜈蚣王进化石 | Scolipite | 1 | false |
| 2572 | 头巾混混进化石 | Scraftinite | 1 | false |
| 2573 | 麻麻鳗鱼王进化石 | Eelektrossite | 1 | false |
| 2574 | 水晶灯火灵进化石 | Chandelurite | 1 | false |
| 2575 | 布里卡隆进化石 | Chesnaughtite | 1 | false |
| 2576 | 妖火红狐进化石 | Delphoxite | 1 | false |
| 2577 | 甲贺忍蛙进化石 | Greninjite | 1 | false |
| 2578 | 火炎狮进化石 | Pyroarite | 1 | false |
| 2579 | 花叶蒂进化石 | Floettite | 1 | false |
| 2580 | 乌贼王进化石 | Malamarite | 1 | false |
| 2581 | 龟足巨铠进化石 | Barbaracite | 1 | false |
| 2582 | 毒藻龙进化石 | Dragalgite | 1 | false |
| 2583 | 摔角鹰人进化石 | Hawluchanite | 1 | false |
| 2584 | 基格尔德进化石 | Zygardite | 1 | false |
| 2585 | 老翁龙进化石 | Drampanite | 1 | false |
| 2586 | 捷拉奥拉进化石 | Zeraorite | 1 | false |
| 2587 | 列阵兵进化石 | Falinksite | 1 | false |
| 2635 | 雷丘进化石Ｘ | Raichunite X | 1 | false |
| 2636 | 雷丘进化石Ｙ | Raichunite Y | 1 | false |
| 2637 | 风铃铃进化石 | Chimechite | 1 | false |
| 2638 | 阿勃梭鲁进化石Ｚ | Absolite Z | 1 | false |
| 2639 | 姆克鹰进化石 | Staraptite | 1 | false |
| 2640 | 烈咬陆鲨进化石Ｚ | Garchompite Z | 1 | false |
| 2641 | 路卡利欧进化石Ｚ | Lucarionite Z | 1 | false |
| 2642 | 泥偶巨人进化石 | Golurkite | 1 | false |
| 2643 | 超能妙喵进化石 | Meowsticite | 1 | false |
| 2644 | 好胜毛蟹进化石 | Crabominite | 1 | false |
| 2645 | 具甲武者进化石 | Golisopite | 1 | false |
| 2646 | 玛机雅娜进化石 | Magearnite | 1 | false |
| 2647 | 狠辣椒进化石 | Scovillainite | 1 | false |
| 2648 | 戟脊龙进化石 | Baxcalibrite | 1 | false |
| 2649 | 米立龙进化石 | Tatsugirinite | 1 | false |
| 2650 | 晶光花进化石 | Glimmoranite | 1 | false |

### ItemType=9 · Pocket=2 · 进化用特殊道具及化石（8 条）

| ID | 简体中文名称 | English | SlotMaxNum | CanNotHold |
|---:|---|---|---:|---|
| 103 | 秘密琥珀 | Old Amber | 999 | false |
| 710 | 颚之化石 | Jaw Fossil | 999 | false |
| 711 | 鳍之化石 | Sail Fossil | 999 | false |
| 1582 | 伽勒豆蔻手环 | Galarica Cuff | 999 | false |
| 1592 | 伽勒豆蔻花圈 | Galarica Wreath | 999 | false |
| 1691 | 黑奇石 | Black Augurite | 999 | false |
| 1861 | 咒术之铠 | Malicious Armor | 999 | false |
| 2344 | 庆祝之铠 | Auspicious Armor | 999 | false |


## 导出和后续

- [全量 ItemData 50 字段 CSV](data/za-v2.0.2-items-all-fields.csv)
- [12 个组的机器可读汇总 JSON](data/za-v2.0.2-itemtype-pocket-groups.json)
- [535 条按类型排序的 CSV](data/za-v2.0.2-items-grouped.csv)
- [[za-items-real-data-audit|道具实测与 Mega 石/宝珠对比]]
- [[za-trade-native-candidates|联机交易原生静态证据]]


## 自动重现分组

~~~bash
python scripts/Export-ZA-Items.py --repo . --version v2.0.2 --output .za-work/items
python scripts/Group-ZA-ItemData.py --input .za-work/items/za-v2.0.2-items-all-fields.csv --output .za-work/items
~~~

对应 [导出脚本](../../../scripts/Group-ZA-ItemData.py) 和 [成功 CI](https://github.com/969981/ZA_Resources/actions/runs/42222265189)。该脚本对 v2.0.2 检验 535 条、12 个组合，保留重复中文名和实际 Item ID。
