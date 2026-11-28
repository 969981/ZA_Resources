# 地图资源映射

[返回总览](README.md) · [模型](ModelResourceMapping.md) · [[ImageResourceMapping]]

| 目标 | 原版入口 | 证据 |
|---|---|---|
| world | ui/data/map/map_field_00.arc, map_field_01.arc, map_top_00.arc | 地图 ARC 路径已核实 |
| locations | ui/tex/map_pic/; ui/data/map/map_info_00.arc | 67 BNTX 路径 |
| wild_zones | world/ik_scene/field/ 与地图配置 | 区域 ID、边界待验证 |
| dungeons | ui/data/map_dungeon/; hud_minimap_dungeon/ | 容器入口 |
| hyperspace | ui/data/map/map_field_dim_00.arc | 名称候选 |
| minimap | ui/data/hud_minimap/ | 15 条目录项，含语言版本 |
| spawn_points | world/ik_data/; world/ik_scene/ | 结合已有 encounter crosswalk |
| navmesh | field/navmesh/ | 原版导航网格目录 |
| geojson / tiles | 派生输出 | 坐标转换、区域标定待实现 |

[遭遇及刷新数据研究](../workflows/za-encounter-crosswalk.md)。地图面板、地点图片、可导航几何是三种资源。未验证坐标轴、比例及投影前不得输出伪精确地理数据。
