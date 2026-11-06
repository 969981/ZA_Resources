---
title: ZA v2.0.2 CSV 完整阅读指南
aliases: [ZA CSV 怎么看, ZA 数据表入门]
tags: [ZA, Obsidian, CSV, guide]
version: "2.0.2"
source: ZA_Resources
status: 实物校验
---
# ZA v2.0.2 — 先看这一篇

> [!summary] 一句话概括
> 这些 CSV 是从 Z-A 2.0.2 的原始 ROM 文件提取并转换的**静态配置表**。最重要的三个问题分别查：**是什么宝可梦** → `ZA_encounters_flat.csv`；**在哪里、怎么刷新** → `ZA_spawner_encounter_join.csv`；**坐标在哪** → `ZA_spawn_points.csv`。不是实时内存记录，也不是游戏运行结果。

数据入口：[GitHub CSV 总目录](https://github.com/969981/ZA_Resources/tree/docs/za-v2.0.2-obsidian-extraction/Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/_tables)；详细原始字段见 [[13-遭遇表逐列解读]]；完整关联见 [[14-生成器刷新与坐标]]。

## 01. 首先明白四个不同层次

1. **源二进制**：`virtual/world/.../encount_data_array.bin`、`*.bfbs`。`.bin` 保存实际数据，`.bfbs` 是 FlatBuffers Reflection schema（字段名和类型）。
2. **原样解码**：`encounter.json.gz` 等，是根据 `.bfbs` 解出的嵌套 JSON，尽量保留原始结构；`encounter.records.csv` 每行用 `row_json` 包裹一个顶层容器。
3. **展开表**：`ZA_encounters_flat.csv` 把每条遭遇展开成一行；`ZA_trainer_parties.csv` 把每只训练家队伍成员展开成一行。
4. **关联表**：`ZA_spawner_encounter_join.csv` 按 `encountDataId` 和 `id` 做严格字符串 JOIN，把生成器与对应遭遇参数写到一起；地图名称中的区域号当前部分是**推断**，不是已经验证的外键。

`encounter.records.csv` 仅 13 行，但其中的 `row_json.root` 数组合计含 **1,966 条**遭遇。不要把“CSV 行数”误当成“宝可梦种类数量”。`spawner.records.csv` 也仅有 13 个顶层组，但内层合计 **2,211 个**生成器。

## 02. 哪张表是干什么的

| 你想查 | 应查看的 CSV | 解释 |
| --- | --- | --- |
| 宝可梦编号、形态和等级上下限 | `encounters/ZA_encounters_flat.csv` | 一行是一条**遭遇定义**；可重复使用，不是一次实际出现 |
| 什么刷新点引用什么遭遇 | `encounters/ZA_spawner_encounter_join.csv` | 一行是一个**生成器→遭遇引用** |
| 地图三维位置 | `maps/ZA_spawn_points.csv` | 一行是一个**生成器的物体位置引用**，可能未找到对应坐标 |
| 20 个野生区域的代码和名称键 | `maps/ZA_zones.csv` | 区域 code、`PLACENAME` key、BGM/快速旅行 flag |
| 训练家配队 | `trainers/ZA_trainer_parties.csv` | 每行一个有 `devId` 的队伍槽 |
| 训练家更多设置 | `trainers/trainer.records.csv` | AI、Mega、招式字段、实际 6 槽结构都在原始 JSON |
| 招式属性分类 | `battle/waza_attribute.records.csv` | `wazaIdList` 不是升级学习表 |
| 头目额外招式、数值配置 | `battle/oyabun_waza.records.csv` / `oyabun_setting.records.csv` | 参数还需校验实际使用场景 |
| 道具球 / 宝可梦掉落 | `items/ZA_item_lottery.csv` | 记录道具抽选项的 raw 权重与数量 |
| 图鉴主表 | `pokedex/EXL_pokedex_raw.csv` | **无 schema 的结构探针**，没有真实字段名 |
| 道具主表 | `items/EXL_items_raw.csv` | 同上，只有偏移和字节，非“已解析道具属性” |
| 来源是否可信、成功率 | `_audit/manifest.csv`、`_audit/published-csv-sha256.json` | 文件源路径、状态、原始字节长度、哈希 |

完整目录还有 `records.csv`、`preview.csv`：
- `*.records.csv`：原始顶层 JSON 一行一条；通常含嵌套数组。
- `*.preview.csv`：**只有前 100 行**，方便 GitHub 网页打开。
- 原名 `*.csv`：**全部行**，大文件可点 Raw 或下载。
- `*.json.gz`：更方便 Python 递归处理的完整结构，存于 [Actions Artifacts](https://github.com/969981/ZA_Resources/actions/workflows/za-real-data-export.yml)。

## 03. 如何理解“行”和“编号”

| 概念 | 示例 | 是否已经证实 |
| --- | --- | --- |
| `encounterId` | `ect_a0201_w01_v01_z460_Alpha` | 原始表 `id`，唯一 |
| `spawnerId` | `id_spn_a0201_w01_v01_001_A` | 原始生成器 `id`，唯一 |
| `speciesId` | `460` | 原始 `devNo`，作为宝可梦种类 ID |
| `objectName` | `spn_a0201_w01_v01_001` | 生成器对象名，可与坐标的 `Name` 精确匹配 |
| `zoneID` | `a0201_w01` | 在 `field_wild_zone` 中是真实字段 |
| `placeNameKey` | `PLACENAME_wild_a0201_w01` | 只是本地化文字键，不是已经翻译的中文地点名 |
| `main+RVA` | — | **上述 CSV 没有运行时内存地址**，勿将空间坐标当偏移 |

## 04. 三个立刻可用的例子

**例 A：按物种编号过滤。** 打开 `ZA_encounters_flat.csv`，筛选 `speciesId=460`，读每一条配置的 `encounterId/minLevel/maxLevel/formNo`；同种物种可能被多张区域或任务遭遇表使用，不能去重后说只在一个地点出现。

**例 B：按生成器反查。** 在 `ZA_spawner_encounter_join.csv` 筛选 `spawnerId=id_spn_a0201_w01_v01_001_A`，得到 `encounterId=ect_a0201_w01_v01_z460_Alpha`、`speciesId=460`、`minLevel=33`、`maxLevel=35`，以及 `oyabunProbabilityRaw=100.0`。要验证是否必定头目，仍须结合主程序与现场采样。

**例 C：找坐标。** 在 `ZA_spawn_points.csv` 筛选这个 `spawnerId`，对应 `objectName=spn_a0201_w01_v01_001`、`x≈-406.921`、`y≈-1.261`、`z≈-831.644`。这三个值是资源中的三维坐标，不是内存地址，也不能单凭它们判断世界地图名称。

> [!warning] 不能直接推断
> `rareRaw` ≠ “闪光概率”；`rareTypeRaw` ≠ “训练家锁闪”；`talentValue=-1` ≠ “宝可梦拥有 -1 个体值”；`weight=100` ≠ “独立出现概率 100%”；`maxCount` ≠ 游戏场景中始终同时存在的数量。详见 [[20-字段缺省值与证据级别]]。

## 05. 核验数字

[导出核验 JSON](https://github.com/969981/ZA_Resources/blob/docs/za-v2.0.2-obsidian-extraction/Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/_tables/_audit/ZA_relation_summary.json)：
- 20/20 张指定 BFBS 源表可解码；
- 1,966 个不重复 `encounterId`；2,211 个生成器；
- 3,268 次 `encountDataId → id` 引用全部命中（0 个不匹配）；
- 2,226 条出生物体记录中 1,302 条按名称命中已有坐标；
- 3,557 条训练家配置、8,005 个含物种 ID 的队伍槽；
- 图鉴/道具无 Schema 的记录只能证明结构：364/396/535/6。

**注意：** “20/20 成功”只是本轮挑选的 20 张 BFBS 表，并不代表整个 ROM 的语义解析 100%。[[01-资源树与证据等级]] 列出原生提取与全盘二次转换的不同审计数字。

## 下一篇

- [[13-遭遇表逐列解读]]：把 22 列真正读懂；
- [[14-生成器刷新与坐标]]：完整外键和坐标关系；
- [[15-训练家队伍与战斗]]：训练家、技能、头目；
- [[16-道具掉落与图鉴原始表]]：无 schema、道具权重、图鉴研究；
- [[17-地图区域与触发条件]]：地图、剧情 flag、phase；
- [[18-导出复现与验收]]：脚本、CSV、字段完整性；
- [[19-实操查询与案例]]：筛选、SQL、Python 查询；
- [[20-字段缺省值与证据级别]]：重要的可信性边界。
