# ZA v2.0.2 全量资源目录研究

## 入口
- [图片映射](ImageResourceMapping.md) · [模型映射](ModelResourceMapping.md) · [地图映射](MapResourceMapping.md)
- [格式说明](ResourceFormatGuide.md) · [提取指南](ExtractionGuide.md) · [开发任务](Roadmap.md)
- [此前图片审计](../research/v2.0.2/za-image-resource-audit.md) · [UI ARC](../research/v2.0.2/za-image-resource-pack.md) · [材质解析](../research/v2.0.2/za-native-material-texture-resolver.md)
- [原生绑定](../research/v2.0.2/za-native-bind-layout-material.md) · [资源 Key](../research/v2.0.2/za-resource-key-scanner.md)

基线：UI ARC 341237c237735e62ccf1359642633d98addae6ac；Image audit 0d5b08ab453d02f946dcfc416d37c6e014b6962f。统一分支保留两条提交历史。
原始路径和像素映射分开；全量 Git 树普查不是二进制解码。原始数据只读，实际素材输出本地 .za-work/，不上传原版 PNG/GLB/纹理。
数据库 catalog.sqlite 为主索引，images/models/maps/pokemon/localization.sqlite 是可重复构建、范围可能重叠的投影，不是五套互相独立的 ID 系统。
ResourceID 为 SHA256(version + NUL + native relative path)。Git blob SHA 不冒充原文件 SHA256。

- [四大核心模块 V1 与原生 ID 证据](ResourceCores.md)

- [原生宝可梦模型结构与 normal/rare 外观审计](NativePokemonModelAudit.md)

- [网格、骨骼绑定与 LayerMask 验证](GeometrySkinLayerMask.md)

- [ZANativeModelExporter V1 与 Bind Pose 数值验证](NativeModelExporterV1.md)

- [ZANativeModelExporter V2 — BNTX Mipmap 与纹理烘焙](NativeModelExporterV2.md)

- [ZANativeModelExporter V2.1 — 代表样本与批量导出](NativeModelExporterV21.md)

- [V2.2 材质适配、切线与 Shader 证据](NativeModelExporterV22.md)

- [V2.3 多 UV、原生切线与特殊 Shader](NativeModelExporterV23.md)

- [V2.4 顶点位移与蒙皮 Resolver](NativeModelExporterV24.md)

- [V2.5 Native Shader Core 与透明材质](NativeModelExporterV25.md)
