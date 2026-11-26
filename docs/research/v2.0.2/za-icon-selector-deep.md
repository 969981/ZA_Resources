---
title: ZA 2.0.2 图标选择器、物种编号与偏移表深度研究
tags: [ZA, UikitPokeIcon, ARM64, PokemonIconOffset]
status: static-audit-pass-runtime-unverified
---
# 图标选择器第三阶段
[[za-native-pokemon-icon-selector]] · [[za-bntx-pokemon-icon-mapping]]

## CI 验收
[45769288256](https://github.com/969981/ZA_Resources/actions/runs/45769288256) assets/elf 两 job 成功，SHA pinned ELF 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d。原全树路径审计 45767331031 已取消；不将其当作成功。像素解码未验收。

## 物种编号
637 条 Catalog，367 个不同 slot0 物种键，366 个不同 pm 资源编号；正向无冲突；反向唯一冲突 pm1071 对应键 967 与 978。与 Personal 原始 national 字段不一致 268 条，涉及 135 个不同物种键/资源编号对。650→720、651→721、652→722、653→717、654→718、655→719、658→725、718→770。此为实际 Catalog 转换字典，不等于证明资产编号历史原因；Personal 字段名沿用参考 schema，需与原生名称表继续验证。PR7 的派生中文名称 CSV 中键 718=基格尔德、770=噬沙堡爷，说明 pm0770 不能直接当全国图鉴编号。

## pm0770
Catalog 718 Form 0/3→12，1/2→11，4→13，5→51；14/15 没有 Catalog 行但均有各自两张 160x160 BC7 BNTX、两份配置、模型、骨骼、材质与动画。
完整 Git 子树：14 有 14 BNTX、15 有 10 BNTX（各含 2 图标），均 22 TRACM、22 TRANM、9 TRAEF、2 TRSKL；两者均有 TRMDL/TRMMT/TRMSH/TRMTR/TRMBF。真实 TRMMT ASCII：
- 14: body_mesh_shape, head_mesh_shape, core_mesh_shape, eye_mesh_shape
- 15: bodya_mesh_shape, bodyb_mesh_shape, core_mesh_shape
这是核心/细胞样外观的候选证据，不是已确认形态或 UI 触发条件。四个图标 SHA256 见上一轮 icon-crosswalk。不得把它们强行绑定 Form 6/7。

## PokemonIconOffset
world/exl/pokemon_icon_offset/pokemon_icon_offset/pokemon_icon_offset.bin 1836 bytes, SHA256 e7bea5b70a83df0348f930e99f29cacbaebb126eca232d28b25a468dae6ec6b9。Root=12, vector=20, 63 rows; 42 distinct slot1 species candidates; 63/63 slot1/2 (absent defaults 0 candidate) match Catalog key pairs. All slot3/4 values equal slot5/6 respectively after zero normalization. No slot1=718 row; slot1=770 row exists and matches separate game species, not pm0770.
| Slot | Present | Representation candidate |
|---|---:|---|
| 0 |63|u32 serial 1..63|
| 1 |63|u32 species key|
| 2 |26|u32 form key|
| 3 |7|f32 component A|
| 4 |61|f32 component B|
| 5 |7|f32 component A2|
| 6 |61|f32 component B2|
Examples key 449/0 B=-0.25, 168/0 B=0.3, 115/0 B=0.05, 115/1 B=-0.09, 4/0 A=0.1 B=-0.2. Absent raw fields preserved as null. Axes/scale/default/UI contexts not proven.

## ARM64 actual observations
0x2CD6CC8..0x2CD6D1C is a bounded helper (preceding RET, stack frame and RET), two direct BL callers at 0x2CD6B00 and 0x2CD6B98.
0x2CD6CDC saves X0 in X19, 0x2CD6CEC saves X8 in X20. 0x2CD6CF0 BL 0x3161520 with X0=SP,W1=0,W2=0x100; 0x2CD6CFC BL 0x2CD73BC (X0=SP,X1=saved input); 0x2CD6D08 BL 0x7DEFC0 (X0=saved X8,X1=SP). Nearby 0x2CD6D20 equivalent helper calls 0x2CD7418 instead. Suggest indirect result construction/string or path transformation, not proof of Species/Form/Gender/Shiny selector.
Two aligned data pointers: 0x3E0ACA8→0x32E07A3 pokemon_icon_offset; 0x3E27BD0→0x326855E default icon path. 0 exact code refs in current targeted ADR/ADRP+ADD/LDR search, 0 exact RELA addend hits in scanned sections. UikitPokeIcon at 0x3296760 remains string evidence only. No object type or vtable attribution claimed.
Next expanded run follows 0x2CD73BC, 0x2CD7418 and 0x7DEFC0. Actual runtime selection requires same Build ID GDB/host trace, with paired Form/Gender/Shiny inputs and selected native texture path; no live session available in this audit.

## Artifacts
`scripts/Probe-ZA-IconSelectorDeep.py`, `.github/workflows/za-icon-selector-deep.yml`. CI artifacts metadata only (species-resource-crosswalk.jsonl, pokemon-icon-offset.jsonl, pm0770-resources.jsonl, elf-pointer-candidates.jsonl, elf-deep-xrefs.jsonl, elf-direct-branches.jsonl, elf-deep-windows.jsonl and summaries).
