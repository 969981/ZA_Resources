---
title: ZA v2.0.2 道具解析与多维分类
aliases:
  - Z-A 道具数据结构
  - ZA ItemData 解析
tags:
  - Pokemon/ZA
  - 逆向/道具
  - FlatBuffers
  - v2.0.2
version: "2.0.2"
evidence: CONFIRMED-SCHEMA
updated: 2026-11-06
---

# ZA v2.0.2 道具解析与多维分类

> [!abstract] 阅读目标
> 从 `item_data.bin` 提取 **道具 ID、内部名称、图标、背包分类、价格、持有规则、招式机、治疗与形态变化参数**，再关联中文文本及商店/掉落来源。**数据结构已由仓库 Schema 和 pkNX 源码确认；本文不把尚未导出的实际字段值当成实测结论。**

关联笔记：[[za-mega-stone-orb-trade-restrictions|为什么 Mega 石与红蓝宝珠不能随交换转移]]

## 1. 证据链与文件定位

游戏版本：`v2.0.2`。从根目录出发：

| 层 | 真实路径 | 意义 | 证据 |
|---|---|---|---|
| 原始主表 | `Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/world/exl/item_data/item_data/item_data.bin` | **50,372 字节**的道具 FlatBuffer 二进制，原始输入 | CONFIRMED：仓库目录 |
| Schema | `tools/pkNX/FlatBuffers/ZA/Item/Schemas/ItemDataArray.fbs` | 字段顺序、类型、含义注释 | CONFIRMED：源码 |
| 类型枚举 | `tools/pkNX/FlatBuffers/ZA/Item/Schemas/Enums/ItemType.fbs` | `ITEMTYPE_0` ~ `ITEMTYPE_9`；**目前只有数字名** | CONFIRMED：Schema |
| 共用类型 | `tools/pkNX/FlatBuffers/ZA/Shared/Schemas/Shared/WazaID.fbs` | 招式 ID 及引用类型定义 | CONFIRMED：路径 |
| 现成导出器 | `tools/pkNX/pkNX.WinForms/Dumping/Gen9a/GameDumper9a.cs` 的 `DumpItems()` | 解析主表、按 Pocket 分类、导出 TM、关联英文名称 | CONFIRMED：源码 |
| 中文名称 | `Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/ik_message/dat/Simp_Chinese/common/itemname.dat` / `itemname.tbl` | 名称消息与索引表 | CONFIRMED：仓库目录 |
| 中文说明 | 同目录 `iteminfo.dat` / `iteminfo.tbl` | 物品说明文本 | CONFIRMED：仓库目录 |
| 商店 | `world/exl/shop/shop_item_lineup/shop_item_lineup.bin` | 道具商店清单和解锁条件 | CONFIRMED：Schema + 文件 |
| 隐藏道具 | `world/ik_data/field/random_pop_item/random_pop_item_table/random_pop_item_table_data/random_pop_item_table_data_array.bin` | 权重、数量、激活条件 | CONFIRMED：pkNX 源码 |

原始 Trinity 源文件不得修改。`virtual_converted` 目前**不代表所有 .bin 已有语义化输出**：既有转换流水线把很多二进制标记为 UNSUPPORTED/STRUCTURE_ONLY，不能将“已扫描”写成“完整解析”。详见 [二次转换说明](../../workflows/za-virtual-converted-v2.0.2.md)。

## 2. 主表真正存储什么？

`ItemDataArray.fbs` 的根对象是 `ItemDataArray { Table:[ItemData] }`。每一项的主键是 `Id:int (key)`。不要用“表中的第 N 行”替代物品 ID：更新版本、排序或缺失 ID 可能让两者不同。

| 字段 | 含义 | 解读边界 |
|---|---|---|
| `Id` | 道具数值 ID | 后续全部关联的主键 |
| `InternalName` | 内部识别字符串 | 不保证是本地化名称 |
| `IconName` | 图标标识 | 还要通过 UI/纹理资源核对具体图片 |
| `ItemType` | 数字枚举 0~9 | **枚举名没有验证后的语义标签** |
| `Pocket` | 背包分组编号 | 不等于 ItemType，也不等于“可交易” |
| `SortNum` | 列表排序值 | 不代表 ID 或稀有度 |
| `SlotMaxNum` | 可堆叠/槽位数量相关参数 | 是否与每种 Mega 石限持 1 个对应，待值与运行时校验 |
| `Price` | 价格相关字段 | 不能直接推出全部商店售价/卖价 |
| `PriceMegaShard` | Mega 碎片定价相关字段 | 要与商店清单核对 |
| `PriceColorfulScrew` | 彩色螺丝定价相关字段 | 要与对应商店核对 |
| `CanNotHold` | 禁止作为携带物的标记 | **不是** `CanNotTrade` |
| `MachineWaza` / `MachineIndex` | 招式机招式 ID / 索引 | 索引的有效值和展示编号按 pkNX 代码验证 |
| `WorkEvolutional` | 进化用途 | 不能单靠它判定进化方法 |
| `WorkFormChange` | 形态变化用途 | Mega、原始回归、其他形态变化须二次区分 |
| `MintNature` | 薄荷对应性格参数 | 数值仍需实表验证 |
| `EquipPower` / `AutoHealPriority` | 携带加成/自动治疗相关 | 字段语义以源码命名为线索，实际效果还需测试 |
| `CanUseInBattle` | 战斗可用性相关标记 | 不能推断是否能在交换中携带 |
| `SwapIntoId` | 特殊转换目标 ID | Schema 明注：Pebble → Zygardite 的特殊用途 |
| `HealPercentage` / `RevivePercentage` / `WorkRevival` | 恢复和复活参数 | 分清百分比、复活状态与战斗限制 |
| `WorkAttack`、`WorkDefense`、`WorkSpAttack`、`WorkSpDefense`、`WorkSpeed`、`WorkAccuracy`、`WorkCritical` 等 | 临时强化、能力相关效果 | 要区分效果值与实际公式 |
| `WorkFriendly1` ~ `WorkFriendly3`、`ExpPointGain`、`MaxUseLevel` | 亲密度/经验/等级约束 | 需结合实际道具测试 |

> [!warning] 不要误判三件事
> 1. `ItemType` 是 Schema 枚举（0~9），**不是**官方的中文十类名称。
> 2. `Pocket` 是背包展示维度，不保证全部道具同一口袋就有相同交换规则。
> 3. 主表**没有明确名为 `CanTrade` 或 `CanNotTrade` 的字段**；交换限制可能位于另外的业务逻辑、专用表、黑名单或联网校验中。

## 3. 建议采用三层分类

数据模型里应同时保留三个独立维度，而不要简单给每个物品一个“分类”字符串。

### A. 游戏原生维度（完整保留原值）

- `ItemType`：`ITEMTYPE_0` … `ITEMTYPE_9`，在查明数值意义前保持原样。
- `Pocket`：`Pocket_0`、`Pocket_1` 等，等拿真实样本和背包 UI 对照后再命名。
- `CanNotHold`、`CanUseInBattle`、`WorkEvolutional`、`WorkFormChange`：分别保留布尔原值，不替代交易规则。

### B. 研究用功能维度（可多标签）

| 人工功能标签 | 典型内容 | 主要判据 |
|---|---|---|
| 捕捉用品 | 精灵球等 | 名称+UI+使用效果 |
| 回复与状态 | 伤药、解毒、复活等 | Heal/WorkRecv/WorkRevival |
| 能力与培养 | 经验糖果、薄荷、能力强化 | ExpPointGain/MintNature 等 |
| 招式机 | 各类 TM | MachineIndex 和 MachineWaza |
| 一般携带物 | 对战加成或特殊效果 | CanNotHold=false + 使用说明 |
| 普通进化道具 | 属性进化石、通信进化携带物 | WorkEvolutional + 实际使用流程 |
| Mega 石 | 物种专属 Mega Stone | 已核实的名称、图标、对应 Mega 形态 |
| 原始回归宝珠 | **朱红色宝珠 / 靛蓝色宝珠**（Red Orb / Blue Orb） | 固拉多/盖欧卡的剧情、说明及战斗效果 |
| 形态变化物 | 其他改变形态的特殊物品 | WorkFormChange + 物种/形态条件 |
| 剧情与收藏 | 剧情重要道具、收集品 | 获取来源、UI、剧情逻辑 |
| 商店/货币 | Mega 碎片、彩色螺丝等 | 商店兑换机制和实际用途 |
| 未知/未分类 | 文本或效果不完整 | UNKNOWN，禁止名称猜测即确证 |

一个物品可以同时是“可携带”“形态变化”“剧情获取”“每种仅一枚”；这些是**多标签，不是互斥类别**。

### C. 交换/持有策略维度（**独立证据表**）

建议新增派生字段：`holdObserved`、`linkTradeObserved`、`tradeOutcome`、`maxCountObserved`、`runtimePredicate`、`evidenceStatus`。这些字段不要回填或伪装成原生 `ItemData` 字段；未验证时设为 `UNKNOWN`。

## 4. 可重复的解析办法

### 方法一：使用仓库内 pkNX（首选）

`tools/pkNX/pkNX.WinForms/Dumping/Gen9a/GameDumper9a.cs` 已有 `DumpItems()`：
1. 读取 `world/exl/item_data/item_data/item_data.bin` 并以 `ItemDataArray` 解码；
2. 导出主表 JSON/文本；
3. 以 `z => z.Id` 关联文本，生成 `item_table.txt`；
4. 使用 `GroupBy(z => z.Pocket)` 导出 `pouch_<Pocket>.txt`；
5. 按 `MachineIndex` 生成 `tm.txt`、`tm_by_name.txt` 等。

注意：此处源代码默认选用 `English` 名称。若希望中文，需检查其 `GetCommonText("itemname", language, cfg)` 参数与文本资源，不能仅用文件序号盲目拼接。

### 方法二：用 flatc 将**已解包的 .bin** 转 JSON

先确保本机安装 `flatc`，并从仓库根目录执行（下列为解析命令，需在本机真实运行验收）：

~~~bash
mkdir -p .za-work/items
flatc -t --strict-json --defaults-json \
  -I tools/pkNX/FlatBuffers/ZA/Item/Schemas \
  -I tools/pkNX/FlatBuffers/ZA/Shared/Schemas \
  -o .za-work/items \
  tools/pkNX/FlatBuffers/ZA/Item/Schemas/ItemDataArray.fbs \
  -- Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/world/exl/item_data/item_data/item_data.bin
~~~

期望输出 `.za-work/items/item_data.json`。如编译器对其他 includes 仍提示缺失，按 `Shared/*.fbs` 的实际路径增加 `-I`；不要改写原始 Schema。Windows PowerShell 可将这条命令改为单行执行。

接着可将 JSON 输出为 CSV（示例需对输出字段进行核对）：

~~~python
import csv, json
from pathlib import Path

source = Path(".za-work/items/item_data.json")
data = json.loads(source.read_text(encoding="utf-8"))
rows = data.get("Table", data.get("table", []))
assert isinstance(rows, list) and rows, "未解析出 ItemDataArray.Table"
rows = sorted(rows, key=lambda x: int(x.get("Id", x.get("id"))))
assert len({int(r.get("Id", r.get("id"))) for r in rows}) == len(rows), "ID 重复"

columns = ["Id", "ItemType", "InternalName", "IconName", "Price",
           "Pocket", "SlotMaxNum", "SortNum", "PriceMegaShard",
           "PriceColorfulScrew", "CanNotHold", "MachineWaza",
           "MachineIndex", "WorkEvolutional", "WorkFormChange",
           "CanUseInBattle", "SwapIntoId"]
out = Path(".za-work/items/items_core.csv")
with out.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
print(f"输出 {len(rows)} 条: {out}")
~~~

> [!important] 这是**可复现实验步骤**，不是声称已在本次环境成功执行了全部 50,372 字节的数据解析。应记录 `flatc --version`、输入 SHA-256、输出数量、错误日志，并在 v2.0.2 实样上核验数值。

### 方法三：联中文名称/说明

- 先解码 `ik_message/dat/Simp_Chinese/common/itemname.dat` 和 `iteminfo.dat`。
- 保留消息 `index`、`displayText`、`rawDecodedUtf16Hex`、控制符与源路径。
- 读 `itemname.tbl` 以保留哈希/名字信息；**不要因为 DAT 消息索引和 TBL 行号相同就认定两者已准确映射**。
- 用 pkNX 的 `GetCommonText("itemname", language, cfg)` 与 `TableUtil.GetNamedTable(..., z => z.Id)` 做对应验证，必要时通过游戏内背包截图复核。
- 对每一行保留 `sourcePath`、`itemId`、`textKey`、`locale`、`confidence`。

## 5. 来源和掉落不是 ItemData 本身

`ShopLineupArray.fbs` 的 `ShopInventory` 有 `Item:uint`、`DisplayIndex` 和多层 `Conditions`；它回答“哪家商店、何时出现”，不回答“物品本身的功效”。

`ItemTableDataDBArray.fbs` 的掉落彩票含 `ItemId:string`、`Weight`、`MaxCount`、`ActivationConditionArray`；其 ItemId **可能是内部字符串而非整数 ID**，必须通过有效关联键建立 crosswalk，不能直接强转成数字。

`ZARewardItemDataArray.fbs` 含 `ItemID`、`Quantity`、`Weight` 及连胜上下限，可用于奖励表研究；重量不等于实际概率，需验证随机抽取和条件过滤程序。

`DumpFieldItems()` / `DumpHiddenItems()` / `DumpMegaCrystals()` 还会读取场景 `.trscn` 位置、隐藏物品表与 Mega 晶体。物品“存在于主表”**不代表**玩家能在当前版本获得。

## 6. 推荐最终数据结构与验收

文件建议：`items_raw_v2.0.2.json`、`items_core_v2.0.2.csv`、`items_localized_zhHans_v2.0.2.csv`、`items_sources_v2.0.2.csv`、`items_trade_evidence_v2.0.2.csv`。

必做检查：
- [ ] 输入 SHA-256、字节数、FlatBuffer root/vtable 边界正常
- [ ] `ItemDataArray.Table` 实际解析记录数、最小/最大 ID、重复 ID
- [ ] `ItemType` 和 `Pocket` 逐值计数，不捏造枚举中文名
- [ ] 中英文本按道具 ID 核对，缺失/孤儿条目有单独清单
- [ ] Mega 石、Red Orb、Blue Orb、进化道具抽样核对图标和背包分类
- [ ] Shop/Drop/Reward 使用已验证的关联键，记录映射失败项
- [ ] 区分 `CONFIRMED`（Schema/实际字节）、`CANDIDATE`（语义猜测）、`UNKNOWN`（未验证）、`REJECTED`（反证）
- [ ] 不修改 `virtual/` 原始资源；输出提交到受控的派生目录

## 7. 源码索引

- [ItemDataArray.fbs](../../../tools/pkNX/FlatBuffers/ZA/Item/Schemas/ItemDataArray.fbs)
- [ItemType.fbs](../../../tools/pkNX/FlatBuffers/ZA/Item/Schemas/Enums/ItemType.fbs)
- [ShopLineupArray.fbs](../../../tools/pkNX/FlatBuffers/ZA/Item/Schemas/ShopLineupArray.fbs)
- [ItemTableDataDBArray.fbs](../../../tools/pkNX/FlatBuffers/ZA/Item/Schemas/ItemTableDataDBArray.fbs)
- [ZARewardItemDataArray.fbs](../../../tools/pkNX/FlatBuffers/ZA/Item/Schemas/ZARewardItemDataArray.fbs)
- [GameDumper9a.cs](../../../tools/pkNX/pkNX.WinForms/Dumping/Gen9a/GameDumper9a.cs)

见 [[za-mega-stone-orb-trade-restrictions]] 继续研究“能带在身上”与“能通过联机交换转移”的区别。
