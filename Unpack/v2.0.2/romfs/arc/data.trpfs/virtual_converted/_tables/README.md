# ZA v2.0.2 — CSV 数据索引

从 ROM 的 `virtual/` 提取并转换，生成文件整理在本目录，原文件不修改。
用于 GitHub 网页浏览的大 CSV 提供前 100 行的 `.preview.csv`，完整 CSV 仍然保留。

> [!IMPORTANT]
> 图鉴和 EXL 道具的原始字段目前**没有 Schema**，只能查看字段槽位，
> **不能根据原始值推断锁闪、固定个体或游戏内部 ID 的真实语义**。
> 部分区域关联是命名推断；遇到无法匹配的坐标不能视为原资源不存在。

## 详细阅读指南

- [完整 Obsidian 目录](https://github.com/969981/ZA_Resources/tree/docs/za-v2.0.2-obsidian-extraction/docs/obsidian/ZA-v2.0.2)
- [CSV 使用总指南](https://github.com/969981/ZA_Resources/blob/docs/za-v2.0.2-obsidian-extraction/docs/obsidian/ZA-v2.0.2/12-CSV%E9%98%85%E8%AF%BB%E6%80%BB%E6%8C%87%E5%8D%97.md)
- [字段与关联解读](https://github.com/969981/ZA_Resources/blob/docs/za-v2.0.2-obsidian-extraction/docs/obsidian/ZA-v2.0.2/14-%E7%94%9F%E6%88%90%E5%99%A8%E5%88%B7%E6%96%B0%E4%B8%8E%E5%9D%90%E6%A0%87.md)

## 按类别查看

### 遭遇、生成器与宝可梦场景配置 — encounters/

- [ZA_encounters_flat.csv](encounters/ZA_encounters_flat.csv) — 1,966 行 · [前100行](encounters/ZA_encounters_flat.preview.csv)
- [ZA_spawner_encounter_join.csv](encounters/ZA_spawner_encounter_join.csv) — 3,268 行 · [前100行](encounters/ZA_spawner_encounter_join.preview.csv)
- [encounter.records.csv](encounters/encounter.records.csv) — 13 行
- [spawner.records.csv](encounters/spawner.records.csv) — 13 行
- [pokemon.records.csv](encounters/pokemon.records.csv) — 3 行

### 地图、区域和出生位置 — maps/

- [ZA_spawn_points.csv](maps/ZA_spawn_points.csv) — 2,226 行 · [前100行](maps/ZA_spawn_points.preview.csv)
- [ZA_zones.csv](maps/ZA_zones.csv) — 20 行
- [spawn_transform.records.csv](maps/spawn_transform.records.csv) — 86 行
- [wild_zone.records.csv](maps/wild_zone.records.csv) — 20 行
- [field_wild_zone.records.csv](maps/field_wild_zone.records.csv) — 20 行
- [field_location.records.csv](maps/field_location.records.csv) — 50 行
- [field_scene_area.records.csv](maps/field_scene_area.records.csv) — 125 行 · [前100行](maps/field_scene_area.records.preview.csv)
- [area_jump.records.csv](maps/area_jump.records.csv) — 83 行

### 训练家及队伍 — trainers/

- [ZA_trainer_parties.csv](trainers/ZA_trainer_parties.csv) — 8,005 行 · [前100行](trainers/ZA_trainer_parties.preview.csv)
- [trainer.records.csv](trainers/trainer.records.csv) — 3,557 行 · [前100行](trainers/trainer.records.preview.csv)
- [trainer_env.records.csv](trainers/trainer_env.records.csv) — 1 行

### 道具、商店与掉落 — items/

- [ZA_item_lottery.csv](items/ZA_item_lottery.csv) — 459 行 · [前100行](items/ZA_item_lottery.preview.csv)
- [EXL_items_raw.csv](items/EXL_items_raw.csv) — 535 行 · [前100行](items/EXL_items_raw.preview.csv)
- [EXL_shops_raw.csv](items/EXL_shops_raw.csv) — 6 行
- [pokemon_drop.records.csv](items/pokemon_drop.records.csv) — 1 行
- [item_ball.records.csv](items/item_ball.records.csv) — 1 行
- [item_ball_spawner.records.csv](items/item_ball_spawner.records.csv) — 11 行
- [item_type.records.csv](items/item_type.records.csv) — 4 行

### 图鉴（无 Schema 原始字段） — pokedex/

- [EXL_pokedex_raw.csv](pokedex/EXL_pokedex_raw.csv) — 364 行 · [前100行](pokedex/EXL_pokedex_raw.preview.csv)
- [EXL_dex_distribution_raw.csv](pokedex/EXL_dex_distribution_raw.csv) — 396 行 · [前100行](pokedex/EXL_dex_distribution_raw.preview.csv)

### 招式属性、头目和战斗参数 — battle/

- [waza_attribute.records.csv](battle/waza_attribute.records.csv) — 25 行
- [oyabun_waza.records.csv](battle/oyabun_waza.records.csv) — 371 行 · [前100行](battle/oyabun_waza.records.preview.csv)
- [oyabun_setting.records.csv](battle/oyabun_setting.records.csv) — 1 行
- [battle_setting.records.csv](battle/battle_setting.records.csv) — 1 行
- [capture.records.csv](battle/capture.records.csv) — 1 行

### 数据来源和核验清单 — _audit/

- [manifest.csv](_audit/manifest.csv) — 20 行

## 校验

- BFBS 解码：20/20 成功；失败 0。
- 生成器→遭遇引用：3,268 次；未匹配 0。
- CSV 完整文件：31 个（不包括预览 CSV）。
- [关联结果](_audit/ZA_relation_summary.json) · [转换清单](_audit/manifest.json) · [CSV SHA-256 清单](_audit/published-csv-sha256.json)

原始完整 `*.json.gz` 仍在 Actions Artifacts；相关研究文档见 `docs/obsidian/ZA-v2.0.2/`。
