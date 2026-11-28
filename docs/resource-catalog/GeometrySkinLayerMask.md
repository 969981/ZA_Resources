# ZA 原生网格、骨骼绑定及 LayerMask V1

[总览](README.md) · [上一阶段](NativePokemonModelAudit.md)
上一轮 [46100276807](https://github.com/969981/ZA_Resources/actions/runs/46100276807) success：8384/8384 模型结构、69673 exact relative refs、466 normal/rare pairs、11181 RGBA diffs、591 icon pairs (590 different,1 equal)。638 Catalog missing: slot6=637 (636 icon name family candidates), slot8=1。仍非运行时 selector proof。
## 妙蛙种子直接字节证据
源路径 ik_pokemon/data/pm0001/pm0001_00_00/，TRMSH d35565ccf3db9601f26efcfadfa1568a620c7e4e、TRMBF d001552bc57cf568c008c3cc3f8eab61c26c8100、TRSKL 7602c47972ae49eb8c29eaf5bb7a162888a8b128。六类属性单流 stride=48:
| offset | type | usage |
|---:|---:|---|
|0|51|POSITION float3|
|12|43|NORMAL half4|
|20|43|TANGENT half4|
|28|48|TEXCOORD float2|
|36|22|BLEND_INDICES uint8x4|
|40|39|BLEND_WEIGHTS unorm16x4|
| shape | vertices | indices | max index |
|---|---:|---:|---:|
|body|2234|9876|2233|
|eye|64|312|63|
|left_tuta|197|906|196|
|right_tuta|197|906|196|
合计2692 vertices,12000 indices。body index segments 6234+3642。眼部 palette=[3]，首顶点 indices=[3,0,0,0] weights=[65535,0,0,0]，rig=3 对应 node5 head。局部 palette 下标解释不成立（3>=1）；支持直接 RigIndex。左藤蔓首顶点 ids=[59,60,0,0]、weights=[33423,32112,0,0]，raw sum=65535；palette 长11，59、60不可能为局部下标。114 transform nodes，91 非负 rig，91 bone records，max rig=90。该结论限样本；全量保留 direct/local 两种候选并逐正权重检查，不将零权重填充值当有效关节。
## 全量验证
新脚本逐 TRMDL→TRMSH→TRMBF→TRSKL 验证；按 shape ordinal 连接 buffer，读取 stride、属性 type、offset、位置范围、index part offset/count、关节和权重。TRSKL 保存 scale/rotation/translation、pivot、parent、rig、四个原始 Vec3 matrix 字段。矩阵行列约定、欧拉顺序、bind/inverse bind 的真实语义未证实，不生成伪正确 skin。多流和未知类型显式报告；vertex layer 作 stream 是候选，多个属性共用 buffer 的解释需验证。无顶点位置、权重或索引原始数据上传，仅统计/结构元数据。
## LayerMask
直接读取 TRMTR texture、shader options、int/float、RGBA 参数。参考仓库 tools/gftool/GFTool.Renderer/Shaders/IkCharacter.glsl (blob 4b54548762e184e445e6c6baf538c246c3ba8e61)：经 UV、layer_weights 后，基础项 BaseColor*texel*max(1-sum(w),0)，按 RGBA 顺序 mix 四层 tint，BaseColorMultiply 决定 tint 是否乘 texel；随后 saturation/darkness。实现仅核心候选混色函数，未实现原生采样、swizzle、layer_weights、sRGB、UV、光照，绝不称原版 Shader。下一步按原版 Shader 二进制与实机参考校准。
## 复现
```powershell
python scripts/Audit-ZAGeometrySkin.py --self-test
python scripts/Audit-ZAGeometrySkin.py
```
产物 .za-work/ZAGeometrySkinAudit/ 下 mesh-skin、skeletons、layer-materials、errors JSONL 与 summary.json。全量 CI 待验收；必须读取错误及歧义统计，不以 workflow success 代替全部绑定通过。
## GLB exporter gate
几何：索引/顶点边界、材质区间；蒙皮：正权重唯一映射、骨骼层级、bind pose 单位矩阵回归、变换/坐标验证；材质：原生 mask channel/color space/UV 与 normal/rare 对照。全部满足后再实现 ZANativeModelExporter，先 LOD0 单样本，再全量；当前没有 GLB 输出。
