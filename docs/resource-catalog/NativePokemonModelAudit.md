# ZA 原生宝可梦模型结构与外观选择研究
[总览](README.md) · [四核心](ResourceCores.md) · [模型](ModelResourceMapping.md)
基线 d718e66，CI [46100044670](https://github.com/969981/ZA_Resources/actions/runs/46100044670) 成功。535/535 ItemID 路径及 BRTI 名命中，35208 UI 纹理，637 catalog，1194 icons，4 unmatched，26 ambiguous；2545 exact slot paths / 638 missing。
## 原版字节实证
读取 v2.0.2/virtual/ik_pokemon/data/pm0001/pm0001_00_00/ 原版 blob，采用 vendored PokeDocs SV model fbs、gftool TRMDL 作为参考，逐字段验证，不将其他游戏 schema 无条件等同 ZA。
| 文件 | Git blob | 原版结构 |
|---|---|---|
| pm0001_00_00.trmdl | b7b1fa336a5ec5b66cdcc444aa9588ac4c92eb16 | 4 mesh（LOD0..3），1 skeleton，1 material，Custom indices 0..3 |
| pm0001_00_00.trmsh | d35565ccf3db9601f26efcfadfa1568a620c7e4e | buffer pm0001_00_00.trmbf；body/eye/left_tuta/right_tuta 四 shape |
| pm0001_00_00.trmbf | d001552bc57cf568c008c3cc3f8eab61c26c8100 | 4 buffers；首 index 19752 bytes，vertex 107232 bytes |
| pm0001_00_00.trskl | 7602c47972ae49eb8c29eaf5bb7a162888a8b128 | 114 transform nodes，91 bone records；root→origin→waist→spine_01 |
| pm0001_00_00.trmmt | ae30b02aa560a414b0c3b6e232befd79400ed5f0 | normal→pm0001_00_00.trmtr；rare→pm0001_00_00_rare.trmtr |
| pm0001_00_00.trmtr | bc18efc65d68479bf516e6534ea64b95f8f58e6b | 4 materials body_a/body_b/r_eye/l_eye |
| pm0001_00_00_rare.trmtr | c9ce0c05e7ff5eb47d7758239fb9bf1142dad4b5 | 同四材质，同纹理引用，RGBA 参数有变化 |

body_a BaseColorLayer1 normal=(0.253128,0.597,0.514534,1)，rare=(0.388768,0.527,0.235042,1)；BaseColorLayer2 normal=(0.085004,0.269,0.205202,1)，rare=(0.195306,0.403,0.106795,1)。LayerMaskMap 指向 body_a_lym.bntx。共享反射贴图为 ../../../share/specular_prb/poke_metal_default_prb/poke_metal_default_prb.bntx。可确认原版 normal/rare 材质配置差异，不代表已证明 runtime shiny flag 及最终 shader 颜色。
## 全量审计
新脚本 Audit-ZANativePokemonModels.py 直接解析六类模型文件，验证 Git blob 和结构边界；输出 mesh/material/buffer/skeleton/texture 精确相对引用、LOD、骨骼父索引/环、缓冲长度和 SHA256、normal/rare 参数差分。TRMSH attribute/stride 为参考 schema 原始字段，尚无 GLB 或顶点解码。
Catalog 缺失按 slot 统计；slot6 仅做目录内 icon 名称族候选，不自动当真路径修复。图标基于已验收数据库，验证 source blob，比较相同前缀末尾0/1 的 RGBA hash，并保留所有原生 Catalog/Personal 候选与异常名；不能将颜色差分等同于异色语义。性别、异色仍 NULL；需要 runtime trace 或独立已知样本证据。
```powershell
python scripts/Audit-ZANativePokemonModels.py --self-test
python scripts/Audit-ZANativePokemonModels.py --cores .za-work/ZAResourceCores/resource-cores.sqlite
```
输出 .za-work/ZANativeModelAudit/：model-structures、native-references、parse-errors、normal-rare-materials、variant-errors、catalog-missing、icon-pairs、icon-irregular JSONL 与 summary.json。仅元数据。全量 CI 待验收，失败逐项保留，不宣称几何、动画和 shader 已恢复。
