---
title: ZA v2.0.2 rare 高位模式分组与特殊事件的生成器对账
aliases: [ZA rare模式矩阵, ZA 传说遭遇来源, Qst074咩利羊]
tags: [pokemon, ZA, rare, shiny, ARM64, encounter, runtime]
version: "2.0.2"
status: 源配置E2-生成器外键E3-闪光机制待E4
---
# Rare 原始高位模式：剧情、野生、头目与特殊闪光样本的差分

> [!important] 本篇新完成了什么
> 在 [[29-rare锁闪与特殊事件差异]] 已确认的 1,966 条 `rareRaw` 基础上，继续**按真实 Encounter ID 的文本前缀分组**，并用 `encountDataId=id` 严格查到生成器引用，输出两张可直接过滤的 CSV。分组仅按名字推断，`rare` 三个高位数值的**运行时分支含义仍未得到本仓库独立 ARM64 验证**。

## 1. 已完成的实物 CSV

- [ZA_rare_context_matrix.csv](https://github.com/969981/ZA_Resources/blob/docs/za-v2.0.2-obsidian-extraction/Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/_tables/encounters/ZA_rare_context_matrix.csv)：根据 Encounter 名称前缀，把全部 1,966 条配置分为若干来源类别，再对不同 `rareHex` 统计数量和关联生成器次数。
- [ZA_rare_event_spawner_crosscheck.csv](https://github.com/969981/ZA_Resources/blob/docs/za-v2.0.2-obsidian-extraction/Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/_tables/encounters/ZA_rare_event_spawner_crosscheck.csv)：7 组关键剧情样本，含 **中文名称、等级、六项 IV 原值、四招 ID、spawner ID、区域推断**。
- [ZA_rare_static_summary.json](https://github.com/969981/ZA_Resources/blob/docs/za-v2.0.2-obsidian-extraction/Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/_tables/_audit/ZA_rare_static_summary.json)：全部源统计与 SHA 引用方式，明确 no_verified_main_rva。
- 生成器：[scripts/Audit-ZA-Rare.py](https://github.com/969981/ZA_Resources/blob/docs/za-v2.0.2-obsidian-extraction/scripts/Audit-ZA-Rare.py)；同一 Actions 工作流每次更新脚本均重新生成 CSV。

## 2. 三种 `rareRaw` 实际出现在哪里？

三种值低 28 位都是 `0x0FFFFFFF`，差异仅在高 4 位。**高 4 位含义尚未独立解析为 enum。**

| 按 ID 前缀归类（启发式） | `0x1FFFFFFF` | `0x2FFFFFFF` | `0x3FFFFFFF` |
|---|---:|---:|---:|
| `btl_ect_boss*`（Boss 战斗命名） | 100 | 0 | 0 |
| `ect_boss*`（Boss 配置命名） | 44 | 0 | 0 |
| `sub_*`（支线命名） | 46 | 0 | 0 |
| `m[数字]*`（主线命名） | 24 | 0 | 0 |
| `ect_a*_w*`（野生区命名） | 6 | **1** | 275 |
| `ect_outzone*`（外围区域命名） | 1 | 0 | 904 |
| `ect_zdm*`/`ect_d*`（异次元命名） | 5 | 0 | 503 |
| 其他命名 | 55 | 0 | 2 |
| **合计** | **281** | **1** | **1,684** |

**这里的分类不是游戏实际的内部枚举名。** 比如 `ect_a*_w*` 内也有教程、剧情固定头目和任务特殊项，不能把这一行全当“普通野生”。

尤其 `0x1FFFFFFF` 的 6 条“野生区命名”记录包括：
- `ect_a0202_w02_v01_z475_Alpha`（devNo 475，70级）；
- `ect_a0301_w02_v01_z675_Alpha`（devNo 675，70级）；
- `ect_a0403_w01_v01_z208_Alpha`（devNo 208，70级）；
- `ect_a0102_w01_v01_z659_tuto` 和 `...z661_tuto`（教程记录）；
- `ect_a0102_w01_v01_z179_NC`（特殊咩利羊候选）。

这说明简单“`ect_a` 开头＝允许闪光”不成立，需看实际生成入口和传入的 `rare`。

## 3. 六类事件的真实生成器 ID 已经连接

| 原始 Encounter ID | 中文名称 | 等级 | Rare | 对应 Spawner |
|---|---|---:|---|---|
| `sub_119_diancie` | 蒂安希 | 70 | `0x1FFFFFFF` | `id_sub119_01` |
| `sub_120_mewtwo` | 超梦 | 70 | `0x1FFFFFFF` | `id_sub120_01` |
| `m10_x` | 哲尔尼亚斯 | 75 | `0x1FFFFFFF` | `id_chapter10_X` |
| `m10_y` | 伊裴尔塔尔 | 75 | `0x1FFFFFFF` | `id_chapter10_Y` |
| `m04_zygarde10` | 基格尔德 | 33 | `0x1FFFFFFF` | `id_chapter4_01` |
| `ect_boss_0718_01` | 基格尔德 | 84 | `0x1FFFFFFF` | **本轮 spawner 外键未命中** |
| `ect_a0102_w01_v01_z179_Qst074` | 咩利羊 | 11 | **`0x2FFFFFFF`** | `id_spn_a0102_w01_v01_Qst074` |

前六个非 `Qst074` 样本中，有些 `rare=0x1FFFFFFF` 可能对应剧情锁闪路径，但**这还不是确定的分支解释**；最后一条是完整 1,966 条里唯一的 `0x2FFFFFFF`。

`ect_boss_0718_01` 没出现在该批 spawner 的引用里，**不表示它未被游戏使用**：Boss 战斗专用加载器、事件脚本或另外的配置入口均可能直接使用它。

## 4. 为什么咩利羊是最重要的正向差分？

`ect_a0102_w01_v01_z179_Qst074` 的原始属性：
- `speciesId=179`，`minLevel=maxLevel=11`；
- `rare=0x2FFFFFFF`；
- 六项 `talentValue=-1/-1/-1/-1/-1/-1`；
- 生成器 `id_spn_a0102_w01_v01_Qst074`，推断区域 `a0102_w01`。

公开的闪光机制资料指出任务咩利羊是**固定闪光**样本：[PokeStats 的 Z-A 闪光方法与规则](https://pokestats.gg/shiny-hunting-hub/games/legends-za)。这里形成非常有价值的对照：游戏原始配置的唯一 `0x2FFFFFFF`，恰好落在已报告固定闪光的任务实体上。

但必须注意两层证据：**“公开资料描述固定闪光”是外部经验/资料证据；“rare 高 4 位为 2”是本仓库二进制事实。** 只有查到主程序从 `rare` 取高位、进入强制闪光处理、最终写回 PID 的实际分支，才能证明二者的因果关系。当前还缺少该证据，**不得据此把全游戏稀有字段强行标成 shiny lock 的既定 enum**。

## 5. 静态例外对照如何指导 GDB 实测

建议在相同 v2.0.2 Build ID 下检查：

```text
A: id_spn_a0102_w01_v01_Qst074 → ect_...z179_Qst074 → rare=0x2FFFFFFF
B: id_sub119_01 → sub_119_diancie → rare=0x1FFFFFFF
C: id_sub120_01 → sub_120_mewtwo → rare=0x1FFFFFFF
D: id_spn_a0201_w01_v01_001_A → ect_...z460_Alpha → rare=0x3FFFFFFF
```

首个目标不是“不断刷新看出不出闪”，而是取得三类原始值在主程序**第一处不同分支**的输入寄存器/内存字段、函数 RVA、调用者和返回结果，再观察 PID/EC、TID/SID、最终闪光 XOR/强制处理。与第一次命中一起记 `BuildID`、`main+RVA` 和现场日志。没有现场证据前 `shinyLocked` 一律保留 `unknown`。

参考：[[07-ExeFS地址与动态验证]]、[[21-锁闪与个体字段研究清单]]、[[29-rare锁闪与特殊事件差异]]。

## 6. 静态配置 ≠ 最终游戏行为

本批全部 1,966 条 `rare` 值都只属于 **Encounter 配置**。其他创建入口如礼物、传说特殊扫描、交易和战斗脚本可能使用不同生成器或不走同一个 `encountDataId`。即便外部闪光攻略说某类传说可以闪，也不能反过来从“这只宝可梦”本身推断所有其 Encounter 必然相同。静态锁闪研究的单位必须是**生成入口、配置 ID 和运行时路径**，而不是单纯物种编号。

**本次确实完成：** 13 个分类组合的数量统计，7 个指定特殊事件的真实 spawner 对账，脚本和审核 JSON 已回存 GitHub。**尚待完成：** 对 2.0.2 `main.elf` 的 rare 分支汇编级验证与最终 PID 写入对照。
