---
title: "Z-A v2.0.2｜58 场景对象、586 Spawner 缺口归因与事件生成链"
aliases: ["ZA Spawn Gap Triage", "ZA Trigger Battle Spawner Evidence"]
tags: [pokemon/za, encounter, flatbuffers, trinity, pkhex, arm64]
version: "2.0.2"
status: "STATIC_EVIDENCE_PARTIAL_RUNTIME_UNKNOWN"
updated: "2026-11-23"
---

# Z-A 生成器缺口归因：从场景到战斗与原生生成链

> [!important] 证据边界
> 此处的 CONFIRMED 指源文件字段级别的静态引用或已记录的主程序原生静态指令；**不是**模拟器/实机执行日志。CANDIDATE 来源于名称、相邻场景等未闭合线索。UNKNOWN 表示尚未证实，不能写成“该宝可梦无法遇到”或“该配置无效”。

## 第一阶段：58 个未匹配的场景对象

场景来源为 [za_scene_points.csv](za_encounter_crosswalk/za_scene_points.csv)，Spawner 映射来源为 [za_spawners.csv](za_encounter_crosswalk/za_spawners.csv)，按 ObjectTemplateName ↔ AppearanceSpawnerObjectInfoList.ObjectName **精确名称**匹配。

| 分类 | 数量 | 证据 | 处理 |
|---|---:|---|---|
| 野生区场景点 spn_a* | 36 | CONFIRMED 场景存在；Spawner 未精确命中 | 核对变体场景、未采用对象与独立动态表 |
| Boss 场景点 spn_boss_* | 16 | CONFIRMED 场景存在 | 14 个可找到对应 btl_spn_boss_* **名称候选**，须追 Battle/事件分配 |
| 野生区外围 spn_outzone_* | 5 | CONFIRMED 场景存在 | 核对候选生成器是否被删、转移或脚本创建 |
| test_pokemon_spawner_blue_object_01 | 1 | CONFIRMED 场景存在 | 可能为测试内容，具体语义 UNKNOWN |
| **总计** | **58** |  |  |

36 个野生区点中，30 个集中在 a0601_w01 的 v01、v02、v03 三套版本（每套 10 点）；此外 a0403_w01 有 4 点，a0303_w01 有 2 点。名字中带 `_nouse` 的对象也只有名称线索，不能由该后缀推出它绝对不会在运行时出现。

**14 个 Boss 候选不是已建立的场景→Spawner 精确连接。** 例如 `spn_boss_0359_01_object` 的名称能推导候选 `btl_spn_boss_0359_01`，但原始 Appearance.ObjectName 并不是前者；严禁将名称规范化当作真实 FlatBuffers 外键。另有 2 个 Boss 对象尚无这样的对应候选。

逐项：[58 行缺口 CSV](za_encounter_crosswalk/za_unmatched_scene_objects.csv)。

## 第二阶段：586 个未定位 Spawner

此处“未定位”仅指**未被当前 pkNX SceneInfo9a 选定的 Trinity 生成点精确连接，且未被 DimensionWildPokemon 的 SpawnerDataId 引用**；不包括动态脚本或专用战斗表。

| 来源线索（互斥名称类别） | 数量 | 后续验证 |
|---|---:|---|
| id_zdm_* | 268 | 当前异次元抽选表未引用；不等于游戏中永不出现 |
| id_spn* | 117 | 完整 CreateScenePath、生成类型、天气时间条件 |
| btl_* | 106 | 战斗场景／其他 battle 数据表 |
| id_sub* | 37 | **全部 37 个有原生 wild battle 表 actor_id 精确连接** |
| spn_boss* | 32 | 头目跟随单位、剧本 Spawn 结构与 Transform |
| 其他 | 26 | **全部 26 个有原生 wild battle 表 actor_id 精确连接** |
| **总计** | **586** |  |

跨类别的独立证据（**不能额外相加**）：
- **63 个不同 Spawner** 来自原始 `wild_btl_data_global.bin` 的 `actor_id` 精确关联（67 条战斗记录）。
- 其中 37 个为 id_sub*、26 个为其他命名类型。该文件共 68 条 battle 记录，另有 common/default。
- **140 个**在 `pokemon_spawner_transform_array.bin` 中找到精确同名对象；Transform 存在不等于当前场景放置。
- **38 个**在 PKHeX 静态遭遇模板源码注释中找到 exact Encounter ID 归属；与上述其他指标可能重叠。
- 因此还有 **523 个**未定位 Spawner 暂未发现 `wild_btl_data_global.bin` 的精确 Actor 入口；它们可能由其他系统调用。

真实战斗表为 8,308 字节：`Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/ik_event/bin/event_wild_battle_data/wild_btl_data_global.bin`。字段 `Battle[0]=Battle ID`、`Battle[1]=Actor ID`、`Battle[9]=Event ID`、`Battle[14]=Context ID`。每个字段的含义依据已有 [Scan-ZA-Rare-ARM64.py](../../../scripts/Scan-ZA-Rare-ARM64.py) 的实际读取/静态交叉验证。

例如（字段是源字节实读）：

| Battle ID | Actor ID | Event ID |
|---|---|---|
| btl_cleffy | id_chapter5_spn_d02_001 | bae_Ev_m05_2210 |
| btl_sub_119 | id_sub119_01 | bae_Ev_sub_119_010 |
| btl_sub_120 | id_sub120_01 | bae_Ev_sub_120_010 |

逐项：[586 行缺口 CSV](za_encounter_crosswalk/za_unlocated_spawners.csv) · [68 条 Battle 记录](za_encounter_crosswalk/za_wild_battle_actor_links.csv) · [缺口统计](za_encounter_crosswalk/za_gap_triage_summary.json)。

> [!note] 数据刷新状态
> 上述 CSV 第一版由已验收的源记录账本和原始 8,308B Battle 表立即生成，Spawner `CreateScenePath` 列仍待全量 1.4MB 原始文件的 CI 再生成填充。脚本已支持实读 CreateScenePath、BattleAreaId、DungeonName、标签与精确 Actor 入口；在 CI 真正通过之前，不能假称全部这些新字段已填充。

## 第三阶段：t1_i007a 的三个错误地点候选

已确认三个场景点位于 `world/ik_scene/field/area/t1_i007a/sub_scene/t1_i007a_gimmick/...`，即区别于普通 `area/t1` 的独立场景树，其原始坐标接近局部原点：

| Spawner | 场景 XYZ | 旧最近邻“地点” | 误配距离 |
|---|---|---:|---:|
| id_spn_d03_01_ev_001 | (2.35, 0.01, 4.40) | 202 | 242.007 |
| id_spn_d03_01_ev_002 | (-0.46, 0.01, 4.68) | 202 | 240.150 |
| id_spn_d03_01_ev_003 | (2.55, 0.01, 2.18) | 202 | 240.648 |

**修复策略**：在 [za_encounter_crosswalk.py](../../../scripts/encounters/za_encounter_crosswalk.py) 的 resolve_scene_location 内单独识别 `/area/t1_i007a/`，将 Location 留空，记录 `UNKNOWN_T1_I007A_LOCAL_COORDINATE` 和距离哨兵 -1。不能把 202 写入 PKL 或作为合法性覆盖证据。未知地点仍需查游戏内原生地图/地点字段或实机捕获 MetLocation 证据。此修复已进入代码与合成测试，重新生成 CSV/摘要以前旧报告的 202 仍是历史误配，不应引用。

## 第四阶段：事件 → 战斗 → Spawner → Encounter

**已静态闭合（源文件字段，不是实机调用栈）**：

```text
trigger_sub_0119.bin : Command53 -> btl_sub_119
wild_btl_data_global.bin : btl_sub_119 -> id_sub119_01
pokemon_spawner_data_array.bin : id_sub119_01 -> sub_119_diancie
encount_data_array.bin : sub_119_diancie / Lv70 / Rare=0x1FFFFFFF

trigger_sub_0120.bin : Command53 -> btl_sub_120
wild_btl_data_global.bin : btl_sub_120 -> id_sub120_01
pokemon_spawner_data_array.bin : id_sub120_01 -> sub_120_mewtwo
encount_data_array.bin : sub_120_mewtwo / Lv70 / Rare=0x1FFFFFFF
```

EX1/EX2 Trigger 文件的 Command 53 已在本轮重新按 ActivationCondition/TriggerCommand 的 FlatBuffers 结构读取并复核。新的 [za_trigger_battle_audit.py](../../../scripts/encounters/za_trigger_battle_audit.py) 会枚举整个 `ik_event/bin/trigger/**/*.bin`，提取每一条原始 Command53 及条件参数，精确关联 Battle/Spawner/Encounter；未匹配和解析错误均需保留。相关输出为 `za_trigger_battle_links.csv`、`za_trigger_source_manifest.csv`、`za_trigger_battle_summary.json`。

静态原生分支也已经在旧有真实 ELF SHA 核对中确认：

- `ELF VA 0x656144` 读取描述对象 +0x68 内部 Rare 模式，至 `0x65614C` 转换成 64 位模式。
- `0x656298` 调用 PID 生成入口 `0x656F80`。
- `0x657168` 指向 Never 防闪分支，`0x657198` 指向 Always 模式调整。
- `0xE3EB64` 为另一条生成入口；其调用者随后执行 TID/PID、Species、Form 等赋值。

来源：[原生 PID 分支研究](za-native-shiny-generator-pid-branch.md) 和 [EX1/EX2 GDB 验证指南](za-ex1-ex2-rare-provenance-gdb-validation.md)。**未闭合的是** FlatBuffers.EncountData.Rare → 内存描述对象 +0x68 的真实字段拷贝，以及实际战斗触发时的动态执行路径。无法仅用静态代码证明所有 586 个 Spawner 的实机行为。

## 源条件与运行时验证门禁

[原始 EncountData 条件](za-encounter-activation-conditions.md) 里已从真实数据读到 `phase_condition`、`momiji_wild_zone_condition`、`force_condition`。它们的原始 Op=5/1/0 不能未经运行时求值就解释为“任务已开放”“时间匹配”或“条件为真”。

后续用本地 GDB 只读记录器 [za_ex_rare_trace.py](../../../scripts/gdb/za_ex_rare_trace.py) 核查真实 PC、LR、字段 +0x68、PID/Species Setter。需先验证 ELF SHA、Build ID 和真实运行时模块映射，不能直接把静态 ELF VA 当作运行时 main+offset。未取得完整真实日志前，保持 UNKNOWN_RUNTIME。

## 复现命令（仓库根目录，PowerShell）

```powershell
$virtual = ".\Unpack\v2.0.2\romfs\arc\data.trpfs\virtual"
$ledger = ".\docs\research\v2.0.2\za_encounter_crosswalk"
$rawSpawner = "$virtual\world\ik_data\field\pokemon_spawner\pokemon_spawner_data\pokemon_spawner_data_array.bin"
$battle = "$virtual\ik_event\bin\event_wild_battle_data\wild_btl_data_global.bin"
$out = ".\.za-work\encounter-gap-audit"

py -3 scripts/encounters/za_gap_triage.py --ledger $ledger --spawner-bin $rawSpawner --battle-bin $battle --output $out --strict
py -3 scripts/encounters/za_trigger_battle_audit.py --virtual-root $virtual --battle-bin $battle --edges "$ledger\za_spawner_encounter_edges.csv" --output $out
py -3 -m unittest discover -s tests -p test_za_gap_triage.py -v
py -3 -m unittest discover -s tests -p test_za_trigger_battle_audit.py -v
```

CI 工作流：[za-encounter-full-crosswalk.yml](../../../.github/workflows/za-encounter-full-crosswalk.yml)。所有原始资源只读；导出的 CSV/JSON 保存源数据校验信息，所有未闭合匹配显式保留 UNKNOWN。
