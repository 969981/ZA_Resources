---
title: ZA Mega 石与红蓝宝珠为什么不能交换
aliases:
  - ZA Mega 石交换限制
  - ZA 宝珠交换限制
tags:
  - Pokemon/ZA
  - 逆向/交易
  - Mega
  - v2.0.2
version: "2.0.2"
evidence: MIXED
updated: 2026-11-06
---

# ZA Mega 石与红蓝宝珠为什么不能交换？

> [!summary] 当前结论（先看）
> **不能把“可以让宝可梦携带”误认为“可以随联机交换转交给另一个存档”。** 《传说 Z-A》里的 Mega 石可以携带并用于超级进化，但玩家交换实测表明不能用交换宝可梦的方式把 Mega 石送给别人。官方规则还明确，每一种 Mega 石只能持有一枚。对**朱红色宝珠（Red Orb）与靛蓝色宝珠（Blue Orb）**，可以确认它们用于固拉多/盖欧卡的原始回归；但 **v2.0.2 的确切禁止交换分支、与 Mega 石是否共用相同谓词，当前尚未通过原生代码/运行时断点证明**。

关联：[[za-item-data-and-classification|道具解析与分类]]。

## 1. 先拆开四种容易混淆的行为

| 行为 | 问题 | 不能推出 |
|---|---|---|
| `CanNotHold` | 宝可梦能否携带？ | 能否交换 |
| 背包拥有 | 当前存档是否拥有一件物品？ | 能否通过 Pokémon 转移 |
| 宝可梦联机交换 | 一只宝可梦是否满足交换条件？ | 携带物是否会一并过户 |
| 对战携带/战斗中夺取 | 战斗技能是否能夺取或交换携带物？ | Link Trade 的允许规则 |

尤其不要把旧世代“戏法/小偷/拍落对 Mega 石无效”当成对《Z-A》**联机交换协议**的证明；这是两条不同的机制。

### 什么已经得到确认？

- **CONFIRMED（Schema）**：`ItemDataArray.fbs` 有 `CanNotHold`、`Pocket`、`SlotMaxNum`、`WorkFormChange` 等字段，但**没有显式名叫 `CanTrade` 的字段**。
- **CONFIRMED（官方规则）**：官方 Z-A 排位规则说明同一种 Mega 石最多持有一个；游戏的 Mega 石可通过商店、碎片兑换等获得。
- **OBSERVED（玩家实测报道）**：社区关于 Z-A 的实测答复一致指出，Mega 石不能随携带它的宝可梦交换转移；有反馈称需要先卸下 Mega 石才能交易。应保存版本、操作和截图再升级为本项目的 CONFIRMED。
- **CONFIRMED（游戏文本）**：`ik_message/dat/English/common/tips.dat.json` 的第 282、286、290 等消息明确描述 Red Orb / Blue Orb 供固拉多/盖欧卡原始回归使用。
- **UNKNOWN（核心待解）**：是否通过专门物品黑名单、类目规则、物品数量上限、交换客户端预检查、服务器校验，或以上多层共同限制；对红蓝宝珠的完整实测矩阵仍待补。

> [!warning] 注意 `field_trade.dat.json`
> `Simp_Chinese/script/field_trade.dat.json` 的“……那只宝可梦似乎不满足交换的条件！”属于**NPC 花蓓蓓交换**语境，并非已证实的联机 Mega 石报错。不能单凭这条文本定位 Link Trade 的判定函数。

## 2. Mega 石为什么会受到特殊限制？

### 游戏规则与设计层面

《Z-A》的 Mega 石在宝可梦身上具有**可携带装备**属性，在玩家存档的获取侧又表现出**每种只能保有一枚的唯一性约束**。

官方排位规则文字：“It is possible to have no more than one of each kind of Mega Stone.” 这支持“同类型唯一”，**但不直接证明底层代码是哪种检查**。

将这两条规则放在一起，交换限制的合理目的包括：

1. 防止通过两个存档互相转移破坏每种 Mega 石的唯一数量限制；
2. 避免通过通信提前获得剧情、任务或排位奖励尚未解锁的 Mega 石；
3. 避免携带物与接收方背包的相同物品、奖励结算状态和存档所有权发生冲突。

**以上三点是设计动机推断（CANDIDATE），不是已经从原生 ExeFS 证实的判断分支。**

不要混淆：在阔星公司的“用 Mega 碎片**兑换** Mega 石”是 NPC 商店功能，不等于玩家间用 Link Trade **交换** Mega 石。

### 为何宝珠也值得单独验证？

- **朱红色宝珠（Red Orb）**：固拉多原始回归专属道具。
- **靛蓝色宝珠（Blue Orb）**：盖欧卡原始回归专属道具。
- 它们不是普通的“某属性宝石”，也不是靠名称含“宝珠”就自动划入 Mega Stone 枚举。
- 它们在 UI 分类、`ItemType`、`Pocket`、`SlotMaxNum`、`WorkFormChange` 和联网检查中是否**同** Mega 石：必须用真实 v2.0.2 主表与运行时检查确认。

“红蓝宝珠是珍贵且独有的原始回归道具，所以可能沿用不可转让的特殊物品规则”属于 **CANDIDATE**。没有实证前，不写“宝珠通过 ItemType=某某而被阻止”。

## 3. 具体证据：文件、可见字段、证明力

| 位置 | 能证明什么 | 不能证明什么 |
|---|---|---|
| `ItemDataArray.fbs` | 主表字段定义、无显式交易字段 | 没有其他交易限制代码 |
| `virtual/world/exl/item_data/item_data/item_data.bin` | 实际道具参数值（需解析后检查） | 所有逻辑都写在这张表 |
| `ItemType.fbs` | 0~9 的原始枚举名 | 某数字就是“禁止交易类” |
| `GameDumper9a.cs::DumpItems()` | ID、Pocket、TM、名称的现成解析路径 | Link Trade 实际判定函数 |
| `ShopLineupArray.fbs` | 商店解锁条件与物品目录 | 玩家对玩家是否可转交 |
| `tips.dat.json` | Mega 石、红蓝宝珠的官方游戏内用途文本 | Link Trade 的拦截细节 |
| `field_trade.dat.json` | 特定 NPC 交换消息 | 网络 Link Trade 的服务器错误 |

相关源文件：
- [ItemDataArray.fbs](../../../tools/pkNX/FlatBuffers/ZA/Item/Schemas/ItemDataArray.fbs)
- [ItemType.fbs](../../../tools/pkNX/FlatBuffers/ZA/Item/Schemas/Enums/ItemType.fbs)
- [GameDumper9a.cs](../../../tools/pkNX/pkNX.WinForms/Dumping/Gen9a/GameDumper9a.cs)
- [中文 NPC 交换文本](../../../Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/ik_message/dat/Simp_Chinese/script/field_trade.dat.json)
- [英文 Tips 文本](../../../Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/ik_message/dat/English/common/tips.dat.json)

外部交叉资料（不替代原生验证）：
- [Z-A 官方玩法：Mega 石获取与携带](https://legends.pokemon.com/en-us/news/adventure)
- [Z-A 官方排位赛特殊规则（每种 Mega 石最多 1 枚）](https://plza-news.pokemon-home.com/en/page/26.html)
- [Red Orb 与 Blue Orb 游戏列表](https://www.serebii.net/legendsz-a/items.shtml)
- [Z-A 玩家 Mega 石交换问答](https://www.reddit.com/r/PokemonLegendsZA/comments/1pwxhom/question_about_mega_stones/)
- [Z-A 玩家实际操作反馈](https://www.reddit.com/r/LegendsZA/comments/1ovy6i1)

## 4. 建议进行的最小对照实验

> [!important] 仅观察原版合法 UI 和已授权的本地测试环境
> 不绕过游戏联网校验，不修改服务器，不推导“强制送入受限道具”的补丁。抓到客户端是否阻止即可回答大部分设计问题。

准备两台/两份测试存档；分别记录版本 2.0.2、联机模式、进度与目标物品拥有数量。先用普通可携带物作为对照。

| 组 | 交换前携带物 | 接收方已有同类？ | 观察重点 |
|---|---|---|---|
| A | 无 | 无 | 裸 Pokémon 能否交换（基准） |
| B | 普通可携带物 | 无 | 是否正常携带传送 |
| C | 通信进化道具（如升级数据等） | 无 | 与 Mega 石的差异 |
| D | Mega 石 | 无 | 是否选取阶段直接阻止 |
| E | Mega 石 | 有 | 是否与已拥有数量相关 |
| F | Red Orb | 无 | 宝珠是否同 Mega 石 |
| G | Blue Orb | 有 | 宝珠是否随数量变化 |
| H | 从 D/F 卸下专属物后 | 不限 | 裸 Pokémon 能否继续交换 |

为每组保存：`buildId`、`itemId`、`internalName`、`pocket`、`slotMaxNum`、`holdBefore`、`tradeSelectAllowed`、`tradeCommitAllowed`、`errorTextId`、`heldAfter`、`bagBefore`、`bagAfter`。**记录阻止发生在哪一侧、哪个界面、哪个时机**，比仅截图“无法交换”更有证据力。

结果判断：
- 选取 Pokémon 时就灰掉：优先追踪 UI/客户端预过滤；
- 可确认后通信前拒绝：优先追踪本地准备阶段检查；
- 双方确认后拒绝/断开：需分别排除通信和校验失败；**不能直接宣称服务器反作弊**；
- 携带物回到原存档背包、宝可梦交换成功：与“整只 Pokémon 不可交易”完全不同，需单独记载。

## 5. 原生定位与 Hook 研究路线（只读）

1. 先运行 [[za-item-data-and-classification]] 中的 FlatBuffer 实表解析，逐一确认 Mega 石、Red Orb/Blue Orb 的 `Id`、`ItemType`、`Pocket`、`SlotMaxNum`、`CanNotHold`、`WorkFormChange`。
2. 追踪 **玩家间 Link Trade** 的选择 Pokémon → 读取 HeldItem → 读取道具表 → 是否通过 → 提交交换数据流程；不要拿 NPC 的 `field_trade` 当成网络函数名称。
3. 在合法本地测试中对普通道具与专属石分别记录只读断点、返回值、调用栈和外层状态；找到同一断点的差异才提出谓词假设。
4. 区分 **本地 UI 检查**、**宝可梦/物品序列化**、**交换协议一致性**、**接受方库存数量校验**；避免把某个错误提示直接当作根因。
5. 每个定位记录 `main+offset`、BuildID、函数前后指令、寄存器、调用方、被检查的 itemId、对照样本结果；只报告实际验证的地址。

### 判定流程的**研究模型**（非游戏真实代码）

~~~text
选中宝可梦
    ↓
能否选取宝可梦？ ──否──> 交易失败（物种/队伍/剧情限制等）
    ↓ 是
读取 HeldItem / ItemData / 接收方状态
    ↓
是否允许此携带物随交换转移？ ──否──> 阻止 / 退回物品 / 要求卸下
    ↓ 是
双方确认 → 通信 → 完成或错误回滚
~~~

任何一步的实现方式、函数名、字段偏移和地址**均未由本笔记确证**。

## 6. 不能混淆的相似现象

- **Mega 石可以给对应物种携带并战斗使用**，但不能因此说“Mega 石可以随宝可梦交换”。
- **普通通信进化携带物**可能需要在交换时随 Pokémon 一起走；不能将其交换逻辑概括为所有携带物通用。
- **Mega 碎片可兑换 Mega 石**不等于 Mega 石可在玩家间交易。
- **原始回归宝珠**不等于所有名称带“珠”的道具；研究对象须锁定精确 Item ID。
- **旧作 X/Y、ORAS 之间因版本差异不能互换新 Mega 石的规则**，不等于《Z-A》的限制机制，不能直接套用。

## 7. 最终验收标准

- [ ] v2.0.2 主表每个目标道具确切 ID 与名称已由二进制解析验证
- [ ] 确认 Mega 石与 Red/Blue Orb 的 ItemType、Pocket、SlotMaxNum、CanNotHold 原值
- [ ] 至少 1 种普通携带物、1 种 Mega 石、Red Orb、Blue Orb 均有真实交换对照
- [ ] 观察清楚“整个 Pokémon 不可选”还是“仅携带物不可转移”
- [ ] 能以同一条本地检查调用链复现两类物品的拒绝差异
- [ ] 未经实证不写死某个交易函数地址、物品黑名单偏移或服务器机制

**当前准确表述：** Z-A 的 Mega 石是可携带但通常不可经联机交换转交的存档唯一型特殊物品；红蓝宝珠的用途已明确，具体交换规则与其是否共用 Mega 石拦截路径，仍需 v2.0.2 数据和运行时实测确认。
