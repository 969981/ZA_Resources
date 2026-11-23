---
title: "Z-A v2.0.2｜宝可梦遭遇原始二进制结构实读"
aliases: ["ZA Encounter Resource Formats", "ZA 生成器与场景 FlatBuffers"]
tags: [pokemon/za, flatbuffers, trinity, pkhex, encounter]
version: "2.0.2"
status: "PARTIAL_REAL_BYTES_VERIFIED"
updated: "2026-11-23"
---

# Z-A v2.0.2 遭遇资源：五类原始格式及实测内容

> [!important] 取证状态
> 本页区分直接读取原始字节（CONFIRMED）、既有仓库静态研究复用（PREVIOUSLY_VERIFIED）、仅依据 schema 的字段定义（SCHEMA）、尚未解码/未验证（UNKNOWN）。本次直接通过 GitHub 的 base64 文件内容接口读取 3 份小于 1 MiB 的 .bin 和 3 份 .trscn，按 FlatBuffers 偏移访问。超过 1 MiB 的 Spawner 原始文件，当前接口只返回空内容；本轮不伪称重新解析了它。git blob SHA 不是源文件 SHA-256。

统一资源根目录：

```text
Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/
  world/ik_data/field/pokemon/encount_data/encount_data/encount_data_array.bin
  world/ik_data/field/pokemon_spawner/pokemon_spawner_data/pokemon_spawner_data_array.bin
  world/ik_data/field/spawner_transform_data/pokemon_spawner_transform/pokemon_spawner_transform/pokemon_spawner_transform_array.bin
  world/ik_data/field/dimension/dimension_wild_pokemon/dimension_wild_pokemon/dimension_wild_pokemon_array.bin
  world/ik_scene/field/area/.../*.trscn
```

## 文件类型概览

| 资源 | 实际字节 | 解析规模 | 证据 |
|---|---:|---|---|
| encount_data_array.bin | 503,348 | 13 DB / 1,966 EncountData | CONFIRMED 本次读取 |
| pokemon_spawner_data_array.bin | 1,401,772 | 13 DB / 2,211 Spawner | PREVIOUSLY_VERIFIED，见下文旧研究 |
| pokemon_spawner_transform_array.bin | 148,696 | 86 DB / 2,108 Transform records | CONFIRMED 本次读取；坐标值未逐条验证 |
| dimension_wild_pokemon_array.bin | 89,264 | 1 DB / 18 PokeType / 90 RankItem / 500 PatternItem / 1,500 Spawner references | CONFIRMED 本次读取 |
| t1_wild_a0101_w01_pokemon_spawner_0.trscn | 31,584 | 14 顶层对象 / 46 子对象 | CONFIRMED 本次读取 |
| t2_pokemon_spawner_0.trscn | 35,296 | 20 顶层对象 / 56 子对象 | CONFIRMED 本次读取 |
| t3_pokemon_spawner_0.trscn | 72,792 | 38 顶层对象 / 104 子对象 | CONFIRMED 本次读取 |

所有前四种 .bin 都采用 FlatBuffers root uoffset32 → table/vtable → vector → 各个子 table 的布局；*.bfbs 是编译过的 FlatBuffers schema，与原始数据文件 *.bin 不同。

## 1. EncountData：实体遭遇参数

Schema：[EncountDataDBArray.fbs](../../../tools/pkNX/FlatBuffers/ZA/World/Schemas/Encount/EncountDataDBArray.fbs)。

```text
EncountDataDBArray.Table[]
  -> EncountDataDB.Table[]
    -> EncountData
       Id: string
       DevNo: DevID
       MinLevel / MaxLevel: int
       Sex / FormNo / Rare: int
       Tokusei / Seikaku: int
       TalentScale / TalentVNum: int
       OyabunProbability: float
       OyabunAdditionalLevel: int
       ActivationConditionArray
       TalentValue / StrengthenValue
       Moves / Item / ItemDropInfoList
```

真实读取 13 个 DB 的行数（按源原始顺序）：

```text
144, 119, 3, 222, 82, 15, 234, 214, 198, 18, 8, 238, 471
合计 1,966
```

真实记录示例（这里 DevNo 为游戏内部编号；导出 PKL 前应调用 pkNX 的 SpeciesConverterZA 转换）：

| Id | DevNo | FormNo | Lv | Rare |
|---|---:|---:|---:|---|
| ect_boss_0359_01 | 359 | 0 | 25 | 0x1FFFFFFF |
| btl_ect_boss_0359_01 | 359 | 1 | 25 | 0x1FFFFFFF |
| ect_boss_0080_01 | 80 | 0 | 34 | 0x1FFFFFFF |
| btl_ect_boss_0080_01 | 80 | 1 | 34 | 0x1FFFFFFF |

原始 Rare 统计：`0x1FFFFFFF=281` (Never)、`0x2FFFFFFF=1` (Always)、`0x3FFFFFFF=1684` (Random)，按 pkNX 的 GetShiny 映射；不是每条记录都可作为野外捕捉槽。唯一 Always 样本在既有研究中为 `ect_a0102_w01_v01_z179_Qst074`。

## 2. PokemonSpawnerData：遭遇组/条件/数量/概率

Schema：[PokemonSpawnerDataDBArray.fbs](../../../tools/pkNX/FlatBuffers/ZA/World/Schemas/Spawner/PokemonSpawnerDataDBArray.fbs)。

```text
PokemonSpawnerDataDBArray.Table[] -> PokemonSpawnerDataDB.Table[]
  -> PokemonSpawnerData
     Id
     AppearanceSpawnerObjectInfoList[]:
       ObjectName, CreateScenePath, DungeonName, BattleAreaId, TagList
       Zone, Ai, Appearance { MinCount, MaxCount }
     ActivationConditionList / ActivationConditionForUiList
     CoolTime { Condition, Time }
     EncountDataInfoList[]:
       EncountDataId, Weight, MaxCount, AdditionalLevel, TagList,
       ShowMapIcon, AppearedTimeCondition, AppearedWeatherCondition,
       Ai, ActivationConditionList, ActivationConditionForUiList,
       Repop { AfterCaptured, AfterDefeated }
```

该文件 1,401,772 B，既有真实解析记录 13 DB / 2,211 Spawner。源字段交叉引用已有如下**真实静态关系**：

| 战斗 | Spawner ID | Spawner 中引用的 EncountDataId |
|---|---|---|
| btl_sub_119 | id_sub119_01 | sub_119_diancie, sub_119_melecie_01, sub_119_melecie_02 |
| btl_sub_120 | id_sub120_01 | sub_120_mewtwo |

证据：[EX1/EX2 Spawner Crosswalk](za-ex1-ex2-spawner-crosswalk.json)，以及 [Trace-ZA-EX-Spawner.py](../../../scripts/Trace-ZA-EX-Spawner.py)。**本次没有重新读取这份大于 1MiB 的完整文件**。

要复核每个 Spawner 的 Weight、MaxCount、time/weather 与 repop，必须在本地对该 bin 做 FlatBuffers 逐行解码；不应将 Weight 当作 PKL 必有字段。

## 3. SpawnerTransform：场景对象名称与 Transform

Schema：[SpawnerTransformDataDBArray.fbs](../../../tools/pkNX/FlatBuffers/ZA/World/Schemas/Spawner/SpawnerTransformDataDBArray.fbs)。

```text
SpawnerTransformDataDBArray.Table[] -> SpawnerTransformDataDB.Table[]
  -> SpawnerTransformData
     Name: string
     Position: PackedVec3f
     Rotation: PackedVec3f
     AttachTransformEnable: bool
```

本次直接解析到 86 个 DB，合计 2,108 条。真实 Name 样本：
`spn_boss_0015_01_follower01_object`、
`spn_boss_0015_01_follower02_object`、
`spn_boss_0354_02_follower01_object`。

> [!warning] 坐标证据限制
> 已确认 Name 与条目数量；这批 FlatBuffers 的 Position/Rotation 字段本轮尚未得到可靠谱的数值读取结果，**不能把字段附近的 offset 直接按三个 float 解读**。原始取值需与实际 bfbs、FlatSharp 对象及场景实例中的坐标交叉验证。下文 .trscn 的真实三维坐标则已从 SRT 结构解析成功。

## 4. DimensionWildPokemon：异次元多层抽选

Schema：[DimensionWildPokemonDBArray.fbs](../../../tools/pkNX/FlatBuffers/ZA/World/Schemas/Dimension/DimensionWildPokemonDBArray.fbs)。

```text
DimensionWildPokemonDBArray (1 DB)
  -> DimensionWildPokemon (18 types)
    -> RankItems (90)
      -> PatternItems (500)
        PatternNo, LotteryWeight
        -> SpawnerItems (1,500 references)
          SpawnerDataId, LotteryWeight
```

1,500 条引用指向 476 个不同的 Spawner ID。真实样本：
- PokeType=0, Rank=0, PatternNo=1, PatternWeight=100：`id_zdm_random_t00_r01_016` / `id_zdm_random_t00_r01_504` / `id_zdm_random_t00_r01_659`，其 LotteryWeight 均为 100。
- PokeType=0, Rank=0, PatternNo=2：`id_zdm_random_t00_r01_661` / `id_zdm_random_t00_r01_504` / `id_zdm_random_t00_r01_016`。
- 本轮读取的 Spawner lottery weight 范围：3—100。

**注意**：这还不是最终每只宝可梦的实际出现概率。应连接 SpawnerData.EncountDataInfoList 的 Weight、条件、模式抽选以及游戏运行时代码才能给出综合概率。PKL 只携带合法性槽位，不能完整表达抽选树。

## 5. .trscn：Trinity 场景对象嵌套 FlatBuffers

Schema：[TrinitySceneObjectTemplate.fbs](../../../tools/pkNX/FlatBuffers/ZA/Trinity/Schemas/TrinitySceneObjectTemplate.fbs)、[TrinitySceneObject.fbs](../../../tools/pkNX/FlatBuffers/ZA/Trinity/Schemas/TrinitySceneObject.fbs)、[SRT.fbs](../../../tools/pkNX/FlatBuffers/pkNX.Structures.FlatBuffers/Schemas/Geometry/SRT.fbs)。

```text
TrinitySceneObjectTemplate
  ObjectTemplateName
  Objects[]:
    Type: "trinity_ObjectTemplate" / "trinity_ScenePoint" / ...
    Data: byte[] = 单独的子 FlatBuffers
    SubObjects[]（递归）
      ...
  -> 对 ObjectTemplate 的 Data 再解码：
     TrinitySceneObjectTemplateData
       ObjectTemplateName
       ObjectTemplateExtra
       ObjectTemplatePath
       Type = "trinity_SceneObject"
       Data: byte[] = 再一层 FlatBuffers
       -> TrinitySceneObject
          Name: pokemon_spawner_*_object
          Position: SRT
             Scale: PackedVec3f
             Rotation: PackedVec3f
             Translation: PackedVec3f (3 x float32)
```

本轮从真实 v2.0.2 .trscn 字节读到：

| 场景 | Top level / Subobjects | 生成点与坐标 (X,Y,Z) |
|---|---|---|
| T1 Wild | 14 / 46 | `spn_a0101_w01_v01_011` → (-760.7057, 0.1804, -826.3315) |
| T1 Wild | 同上 | `spn_a0101_w01_v01_012` → (-774.4426, 0.1824, -832.1913) |
| T2 Labs | 20 / 56 | `spn_d01_01_001` → (-1.6876, 0.0043, 66.3537) |
| T3 Sewer | 38 / 104 | `spn_d02_01_001` → (60.0000, 0.0050, -17.5000) |

T1 样本以 `pokemon_spawner_sphere_object` 为主，T2/T3 样本以 `pokemon_spawner_box_object` 为主；这两个实际场景对象类型并非种族或遭遇概率。实际启用哪些点、匹配到哪些 Pokémon，需要用 `ObjectTemplateName` 连接 Spawner 的 `AppearanceSpawnerObjectInfoList.ObjectName`，再从 `EncountDataInfoList.EncountDataId` 关联遭遇配置。

## 全链路关系与 PKL 边界

```text
*.trscn (生成点、形状、坐标)
   │ ObjectTemplateName
   ↓
PokemonSpawnerData (ID、出现条件、候选组、权重)
   │ EncountDataId
   ↓
EncountData (宝可梦、形态、等级、性别、Rare、头目配置)
   │ + 地图 Location ID
   ↓
pkNX SpawnRipper9a -> t1/t2/t3_slot_sets.json -> encounter_za.pkl

DimensionWildPokemon -> SpawnerDataId -> PokemonSpawnerData
   ↓
pkNX ExportHyperspacePickle -> encounter_hyperspace_za.pkl

特殊任务 / 固定神兽 / 礼物 / 交换
   -> PKHeX Static / Gift / Trade 模型，不能统统塞入 wild PKL
```

相关：[Z-A PKL 工具与命令](../../workflows/za-encounter-pkl.md)、[现有锁闪与 EX1/EX2 研究](za-legendary-shiny-lock-diancie-mewtwo-events.md)。

> [!todo] 待完成的严格验收
> 完整本地 RomFS 解析全部 .trscn 场景；spawner 大文件字段抽样与源 SHA-256；transform 坐标字节读取方式复核；空地点/未命中对象审计；官方 PKHeX 两份 PKL 逐槽差异；合法性实际样本回归。
