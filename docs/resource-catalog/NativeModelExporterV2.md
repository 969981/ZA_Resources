# ZANativeModelExporter V2 — Textured Model
[总览](README.md) · [V1](NativeModelExporterV1.md) · [网格/材质](GeometrySkinLayerMask.md)
## 基线
V1 [46100990025](https://github.com/969981/ZA_Resources/actions/runs/46100990025) success；589/590 bind pose pass；保留原生网格、91 joint、114 nodes、2692 vertices、12000 indices。V2 复用严格 V1，限 pm0001 LOD0。
## 原版 BNTX 样本
路径 ik_pokemon/data/pm0001/pm0001_00_00/。body_a_alb 512×512 BC7 SRGB 10 mips，body_a_lym 512×512 BC7 UNORM 10，body_a_nrm 512×512 BC5 UNORM 10，body_a_ao 512×512 BC4 UNORM 10；body_b_alb/lym 256×512 10，eye_alb 32×32 6，eye_lym/nrm 128×128 8。body_a_alb 原生 mip offsets 4096,266240,331776,348160,352256,353280,353792,354304,354816,355328；对应 span 262144,65536,16384,4096,1024,512,512,512,512,512。按每级独立 GOB span、缩减 block height、严格边界解码，不把整文件当单 mip。BC5 identity selector 缺失 B/A 采用标准候选补值0/1，法线仅 XY 重建正 Z。每 mip 保留尺寸、格式、源 sha、线性块 hash、RGBA hash；不宣称独立像素 parity。
## 烘焙
TRMTR 原生 IkCharacter, NumMaterialLayer=5, BaseColorMultiply=True, LayerMaskScale1..4=1。参考 vendored gftool IkCharacter.glsl：sRGB 基础纹理转换线性；mask 保持 UNORM，float bilinear resample 至两者最大尺寸；基础项 BaseColor*texel*max(1-sum(w),0)，逐层 mix；饱和度/暗度后转换 sRGB PNG。normal/rare 真实 TRMMT 配置。采用同源纹理坐标域烘焙；base/mask sampler 不一致则拒绝。候选 KHR_texture_transform 使用 (uv-center)*scale+center+offset，body_b scale=(2,1)。参考 Sampling.glsl mode1 repeat、6 mirror，7 近似 clamp；原版边界语义及 V 方向仍未实机确认。NormalMap 独立 UV transform；AO red channel；不实现原版 eye parallax/refraction、阴影、rim、specular、emission 或精确 normal Y 约定。GLB PBR 近似而非原版 shader。
## 输出与验收
两 GLB 内嵌四个 base color、四个 normal、四个 occlusion PNG（每个版本12张引用，重复贴图未去重）；原生 geometry/accessor bytes normal/rare 一致；重新读取 PNG 和 V1 skin 校验；Khronos npm validator 零 error 门槛，Blender headless 导入检查 armature/texture nodes，Cycles CPU 384x384 preview。渲染成功不等于原版外观吻合。脚本仅输出本地模型及预览，CI 按仓库规则仅上传 JSON/JSONL 元数据。V2 全量 CI 待验收，未扩大590模型范围。
```powershell
python -m pip install numpy==2.2.6 Pillow==12.3.0
python scripts/ZANativeModelExporterV2.py --self-test
python scripts/ZANativeModelExporterV2.py
npm install --no-save --ignore-scripts gltf-validator@2.0.0-dev.3.10
node scripts/Validate-ZAGltf.cjs .za-work/ZANativeModelExporterV2
blender -b -t 2 --python-exit-code 1 --python scripts/Validate-ZABlender.py -- .za-work/ZANativeModelExporterV2
```
## 扩展门槛
先检查真实渲染、官方 validator、源 mip parity、normal orientation、body_b UV 与 eye 材质，才扩展多模型；同时定位1个 bind fail、314 shape issues 与50未闭合 declaration。未验证资源保留候选状态。
