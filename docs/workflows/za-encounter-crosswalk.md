---
title: "Z-A v2.0.2 遭遇交叉关联完整复现与异常复核"
tags: [pokemon/za, encounter, pkhex, flatbuffers, research]
version: "2.0.2"
status: "STATIC_CONFIGURATION_AUDIT"
---

# Z-A v2.0.2 全量 Spawner→Encounter→Scene→PKHeX 审计

> [!important] 证据边界
> 数据表的静态引用，不证明实机运行时满足天气、时间、任务触发或刷新条件。未匹配到当前场景的 Spawner 可能属于动态脚本、Boss 或遗漏场景，不能标记为实际不可获得。

## 代码与完整数据

- [原始 FlatBuffers 解析器](../../scripts/encounters/za_resource_inspect.py)
- [全量静态关联与官方 PKL 比对](../../scripts/encounters/za_encounter_crosswalk.py)
- [激活条件原始字段解析](../../scripts/encounters/za_condition_audit.py)
- [合成测试](../../tests/test_za_encounter_crosswalk.py)
- [自动化运行、审计及提交](../../.github/workflows/za-encounter-full-crosswalk.yml)
- [完整运行结果和 CSV 账本](../research/v2.0.2/za-encounter-crosswalk-v2.0.2.md)

## Windows PowerShell 7 手工复现

从仓库根目录执行。Python 3.12，全部仅用标准库。原始资源根为 Unpack/v2.0.2/romfs/arc/data.trpfs/virtual。本流程不修改游戏资源。

先下载 PKHeX 对照基线：

```powershell
$base = "https://raw.githubusercontent.com/kwsch/PKHeX/master"
$pk = ".\.za-work\pkhex"
New-Item -ItemType Directory -Force -Path $pk | Out-Null
Invoke-WebRequest "$base/PKHeX.Core/Legality/Encounters/Data/Gen9/Encounters9a.cs" -OutFile "$pk\Encounters9a.cs"
Invoke-WebRequest "$base/PKHeX.Core/Resources/legality/wild/Gen9/encounter_za.pkl" -OutFile "$pk\encounter_za.pkl"
Invoke-WebRequest "$base/PKHeX.Core/Resources/legality/wild/Gen9/encounter_hyperspace_za.pkl" -OutFile "$pk\encounter_hyperspace_za.pkl"
```

随后运行：

```powershell
$virtual = ".\Unpack\v2.0.2\romfs\arc\data.trpfs\virtual"
$out = ".\.za-work\za-crosswalk"
py -3 scripts/encounters/za_encounter_crosswalk.py --virtual-root $virtual --scene-info tools/pkNX/pkNX.WinForms/Subforms/Gen9a/Map/Info/SceneInfo9a.cs --manual tools/pkNX/pkNX.WinForms/Subforms/Gen9a/Map/ManualPositionRip.cs --converter tools/pkNX/FlatBuffers/ZA/Shared/Gen9/SpeciesConverterZA.cs --pkhex-templates "$pk\Encounters9a.cs" --pkhex-normal "$pk\encounter_za.pkl" --pkhex-hyperspace "$pk\encounter_hyperspace_za.pkl" --output $out --strict
py -3 scripts/encounters/za_condition_audit.py --virtual-root $virtual --output $out
py -3 -m unittest discover -s tests -p test_za_encounter_crosswalk.py -v
```

使用 CI 结果时需以摘要中的 SHA-256 核对原始版本与 PKHeX 基线。master 是滚动上游；长期重现应记录或固定 PKHeX 提交号。运行生成的文件默认位于 .za-work，不会自动写回 PKHeX。

## 输出文件

| 文件 | 对账内容 |
|---|---|
| za_spawners.csv | 全部 Spawner：场景放置、Location 候选、异次元引用、原始条件数量 |
| za_encounters.csv | 全部 Encounter：种族号转换、形态、等级、异色、静态类别 |
| za_spawner_encounter_edges.csv | 全部配置关联及 PKHeX 槽位匹配 |
| za_dimension_refs.csv | 异次元 Type、Rank、Pattern、Spawner 和原始权重 |
| za_scene_points.csv | Trinity 场景名称、位置、地点来源、近邻距离 |
| za_activation_conditions.csv | Condition、Op、Param 原始值，按 Spawner / Encounter / Target 来源 |
| summary.json / za_condition_summary.json | 统计、输入 SHA-256 及未验证语义 |

## 已确认的基础事实

原始资源为 Spawner 2,211、Encounter 1,966、Transform 2,108、异次元引用 1,500（476 个不同 Spawner ID）。按 pkNX SceneInfo9a 的场景清单提取 1,207 个对象，1,149 个能与 Spawner 名称精确对应；另有 58 个未命中场景对象，以及 586 个没有命中当前场景清单或异次元表的 Spawner。静态 Spawner→Encounter 引用边有 3,268 条。

## 三个需人工确认的地点异常

三个场景点都来自 t1_i007a_pokemon_spawner_0.trscn，实际坐标处于局部原点附近；pkNX ManualPositionRip 的最近邻把它们标为 Location 202，但距离超过 240，因此不能当作已证实的游戏获得地点。

| Spawner | XYZ | 最近邻距离 |
|---|---|---:|
| id_spn_d03_01_ev_001 | (2.35, 0.01, 4.40) | 242.007 |
| id_spn_d03_01_ev_002 | (-0.46, 0.01, 4.68) | 240.150 |
| id_spn_d03_01_ev_003 | (2.55, 0.01, 2.18) | 240.648 |

## PKHeX 等级区间比较陷阱

Location 12 的 Species=16 有 Lv5–8 和 Lv3–5 两个 PKL 槽位。源 ect_outzone_a0102_z016_01_low 的 Lv3–5 应被第二个完整覆盖。匹配代码必须遍历所有候选并优先完整覆盖，不可在遇到第一个部分重叠时直接结束。

## 后续验证

- 从原始任务、事件、固定战斗数据定位 58 个未匹配场景对象、586 个未定位 Spawner 的来源。
- 将 Condition/Op/Param 与运行时判定关联，区分真正的限制和默认激活项。
- 用实机或可复现动态日志核查特殊场景的 Location。
- 结合 PKHeX Static/Gift/Trade 模板的固定 IV、Nature、Moves、PID/RNG，不能仅用野生 PKL 判断合法性。
