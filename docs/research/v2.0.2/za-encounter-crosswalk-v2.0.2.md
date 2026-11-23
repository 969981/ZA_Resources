---
title: "Z-A v2.0.2 全量遭遇配置交叉审计"
tags: [pokemon/za, encounter, research, pkhex]
status: "STATIC_CONFIGURATION_NOT_RUNTIME_PROOF"
---

# Z-A v2.0.2 全量静态遭遇账本

> [!important] 本文数字是来源静态配置，不证明游戏实机运行时可生成/可捕获。T1 Location 是 pkNX ManualPositionRip 最近邻归属；时间天气与任务条件保留原始值。

| 指标 | 数量 |
|---|---:|
| spawners | 2,211 |
| encounters | 1,966 |
| transform_records | 2,108 |
| dimension_refs | 1,500 |
| distinct_dimension_spawners | 476 |
| scene_points | 1,207 |
| spawners_scene_placed | 1,149 |
| spawners_hyperspace_referenced | 476 |
| encounter_edges | 3,268 |
| encounters_referenced | 1,385 |
| encounters_unreferenced | 581 |
| encounters_official_pkl_covered | 1,063 |

## Encounter 来源分类

| 类别 | 记录数 |
|---|---:|
| configured_spawn | 1,061 |
| no_spawner_ref | 580 |
| official_static | 44 |
| spawner_without_scene_or_dimension | 281 |

## PKHeX 逐关联边匹配结果

| 结果 | 关联边数 |
|---|---:|
| covered | 2,429 |
| no_official_location | 838 |
| overlap | 1 |

## 机器可读全量账本

- [Spawner 全量](za_encounter_crosswalk/za_spawners.csv)
- [Encounter 全量](za_encounter_crosswalk/za_encounters.csv)
- [Spawner 与 Encounter 全部关系](za_encounter_crosswalk/za_spawner_encounter_edges.csv)
- [异次元抽选引用](za_encounter_crosswalk/za_dimension_refs.csv)
- [场景对象、坐标和地点估计](za_encounter_crosswalk/za_scene_points.csv)
- [摘要与源 SHA-256](za_encounter_crosswalk/summary.json)

## 未闭合 / 需要实机验收

- static links do not prove runtime spawning
- time/weather/flags raw values not runtime interpreted
- T1 locations use pkNX nearest manual coordinate
- missing scene reference may mean scripted spawn
- PKHeX static/gift/trade exact comment IDs only

## 输入取证散列

- enc: SHA256 4e080206c5f88707a1c01c2e3aa78d75ab362f3138e38c8677b2e90583446b49, 503348 bytes
- sp: SHA256 611a5bb7e6d97e21494070cfc933d994021503f8f9b3d0591481082fce269e09, 1401772 bytes
- tr: SHA256 34628d8c1a8bd0fb3fdf3ecc32bd5ea593465158a7a321ee352665c05cd0b907, 148696 bytes
- dim: SHA256 ff80c8cbd0dd95269c0a617bd24870eff6838429433e5a1d35e30eb0ac1795fc, 89264 bytes
- scene_info: SHA256 cd6f8e77f3e15cc3cfeaa0f3f38b89cfb06b96141931bc49dd0ff0c8f99d7d70, 4487 bytes
- manual: SHA256 7e05aff5d03ba15bb3c9b12e42a229acf0996fb153bbc814e0c70b0796f52d27, 50841 bytes
- converter: SHA256 9b3596c46e8927a7eaf951a3f961e046866d2bc5f04665bfabd04dd8035cd48c, 3490 bytes
- pkhex_templates: SHA256 f7d19912dce009b44aea2d3c7c4566f5ed379e896cf302749f8db32829cbde23, 12201 bytes
- pkhex_normal: SHA256 38299970bf032893bff8b09f8f230a5b682ccbb8e57ef25ba281baabc8efdd2b, 9568 bytes
- pkhex_hyperspace: SHA256 5a456effe2a40a338da6a84b2f3381caede5685f1a34a1c6d741aa39aa1ca693, 9996 bytes
