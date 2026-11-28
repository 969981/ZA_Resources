# ZA 四大核心资源模块 V1
[总览](README.md) · [[ImageResourceMapping]] · [[ModelResourceMapping]]
## 基线
[全量路径验收](https://github.com/969981/ZA_Resources/actions/runs/46099799157)：238546 paths，169970 raw Git blobs，所有路径记录 RAW。路径数与描述符数量一致不是逐 Hash 对账；模型相关目录207888不等于模型数量。元数据 artifact 15245301208。
## ZAPokemonIconMapping
直接解析 Catalog/Personal，保留 637 个 native key 三元组、personal raw national、slot 与 exact path；图标按目录关联候选，保留一对多、无匹配、非标准名称。原生 gender/shiny 仍为空。历史证据见 [selector](../research/v2.0.2/za-native-pokemon-icon-selector.md) 和 [registration](../research/v2.0.2/za-icon-registration.md)。不使用 pm 前缀充当全国编号。
## ZAItemIconMapping
原生 world/exl/item_data/item_data/item_data.bin，Git blob 128dc0c3e423486c3c753f8bf17f0186fa40d241，50372 bytes；依照仓库 pkNX ZA ItemDataArray.fbs 直接读 row slot0 Id:i32，slot2 InternalName，slot3 IconName。实际 535 rows、375 distinct IconName。例 ID2160→item_0350、2162→item_0332、2137→item_1956。严格连接 ui/tex/icon_item/{IconName}/{IconName}.bntx，原生 ID 与资源名不混用。精灵球、超级石分类和 BallID 原生转换表后续解析；路径命中不等于运行时 UI 选择已确认。
## ZAUIResourceCore
固定历史 [UI artifact](https://github.com/969981/ZA_Resources/actions/runs/45771214568/artifacts/15094562074) 15094562074，导入 source/member/texture JSONL，每一条 PARSED alias 必须与当前 Git 树路径及 blob 一致，否则拒绝导入。BRTI 以 (blob,member_index,texture_index) 唯一定位；保留原始成员名/hash、像素 hash、解码状态。名称族分类仅 CANDIDATE；box marking 不当作 ribbon/mark；TypeID/BallID/RibbonID 等均不自动填写。原生渲染和双解码器对账未完成。历史 artifact 过期时需重新运行 UI pack。
## ZANativeModelCore
Catalog slots 1/2/3/6/8 以原始字符串精确匹配路径，缺失保留。其余模型、材质、骨骼、动画、纹理按同目录分组，所有共址关系均为 CANDIDATE，不伪造 mesh、material 或骨骼依赖。GLB 几何转换尚未实现。
## 复现
```powershell
python scripts/Build-ZAResourceCores.py --self-test
python scripts/Build-ZAResourceCores.py --ui-manifests .za-work/ZAImageResources/manifests
```
无 UI manifest 可运行其余模块，但 UI 表为空。输出 .za-work/ZAResourceCores/resource-cores.sqlite 与 JSONL、summary.json。ResourceID 兼容主 catalog；不覆盖旧数据库。原始输入只读，CI 不上传 PNG/DDS/GLB。
## 验收与后续
新 CI 验证原生 blob、固定版本行数、SQL 完整性和外键、历史 UI alias、共享 Item 图标和缺失记录。下一步原生 selector（性别、异色、fallback）、ItemType/BallID、TypeID、ribbon/mark 消费者；模型直接解析 TRMDL/TRMSH/TRMBF/TRSKL/TRMTR 字段与真实引用后再转换 GLB。当前仅实现四模块第一版，不声明全任务完成。
