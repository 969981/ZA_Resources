# 模型资源映射

[返回总览](README.md) · [格式](ResourceFormatGuide.md) · [[MapResourceMapping]]

| 目标 | 原版路径 | 说明 |
|---|---|---|
| pokemon | ik_pokemon/data/*/*/ | 模型、骨骼、材质、动画、LOD、图标 |
| characters | ik_chara/model_pc/, model_pc_base/, model_uq/ | 玩家与人物模型候选 |
| clothing | ik_chara/model_cc_base/, model_cc_ir/, model_cc_vr/ | 服装配置候选 |
| balls / items | ik_chara/model_ob/ | 75 一级目录；ob0201_00_masterball 已实证 |
| buildings / environment | field/model/{env,t1,t2,t3,t4}/ | 场景分类需解析对象 |
| animations | ik_pokemon/data/; ik_chara/motion_*/ | tranm、tracm、traef 等 |
| materials / textures | 各模型目录 | trmtr/trmmt 与 BNTX，rare 材质另存 |
| effects | ik_effect/data/ | 原生特效候选 |

原生 Catalog ik_pokemon/catalog/catalog/poke_resource_table.trpmcatalog 有 637 条记录，不能等同物种或 GLB 数量。
样本 ik_pokemon/data/pm0001/pm0001_00_00/：trmdl、trmsh、trmbf、trskl、trmtr、trmmt、trpokecfg、rare.trmtr、lod1..3、body_a_alb/nrm/ao/lym.bntx。
后续应按 Catalog→mesh/buffer→skeleton→material→texture→animation 绑定，输出 GLB 和独立渲染 PNG；必须验证坐标、权重、材质及异色。当前仅路径索引，没有 GLB 转换实现。
