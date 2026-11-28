# 图片资源映射

[返回总览](README.md) · [提取](ExtractionGuide.md) · [[ResourceFormatGuide]]

所有原版路径相对 Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/。
| 目标目录 | 原版路径或入口 | 已有证据与缺口 |
|---|---|---|
| pokemon | ik_pokemon/data/*/*/icon/ | 160×160 BC7 样本；原生 selector 待闭合 |
| items | ui/tex/icon_item/ | 379 BNTX 路径；535 ItemID 对照待验证 |
| balls | ui/tex/icon_item/; ui/data/btl_app/ | 道具/战斗 UI 区别，BallID 未确认 |
| types | ui/data/dummy/dummy_icon_type.arc | 54 BRTI: 18 单通道、18 彩色、18 文字 |
| moves | ui/data/btl_app/ | 原生招式分类图未确认 |
| ribbons / marks | UI 纹理索引；ui/data/status/ 候选 | ribbon/akashi 严格搜索无命中，不可宣称存在 |
| markings | icon_marking_00..05^s | 盒子标记名称候选，非证章 |
| badges | ui/data/hud_ryl/ | 排位奖章名称候选 |
| status | ui/data/status/; btl_app/ | UI 状态候选 |
| donuts | ui/tex/icon_donut/ | 82 BNTX 路径，普通/big |
| characters | ui/tex/chara/; ryl_npc/ | 48 / 37 路径 |
| clothing | ui/tex/hud_shopping/ | 356 路径，含商店素材，不全是服装 |
| logos | ui/tex/logo_brand/ | 54 路径 |
| maps | ui/tex/map_pic/; ui/data/map/ | 67 独立地点图片路径；地图层见地图文档 |
| illustrations | ui/tex/onepicture/; tips/ | 16 / 84 路径 |
| ui / atlases | ui/data/*/*.arc | SARC/BNTX/FLYT/FLAN；UV、动态纹理和材质未全部恢复 |

历史验收 35,208 解码候选、7,401 像素组（[报告](../research/v2.0.2/za-native-material-texture-resolver.md)），不等于所有图片或独立业务图标。保留像素、通道、语言、材质及原名。分类候选不可写成正式业务 ID。
