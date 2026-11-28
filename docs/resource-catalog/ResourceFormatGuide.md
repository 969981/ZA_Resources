# 原版格式及转换工具

[返回总览](README.md) · [提取](ExtractionGuide.md)

| 格式 | 用途 | 转换目标 |
|---|---|---|
| BNTX/BRTI | 纹理容器与纹理记录 | DDS/PNG；BCn、swizzle、通道、mip、array 分别验收 |
| ARC/SARC | UI 封装 | 成员索引，不把容器当单张图 |
| BFLYT/BFLAN/TRUIV | 布局、动画、UI 配置 | 材质/UV/帧元数据 |
| TRMDL/TRMSH/TRMBF | 模型、网格、缓冲候选 | GLB |
| TRMTR/TRMMT/TRSKL | 材质与骨骼候选 | GLB 材质/骨骼 |
| TRANM/TRACM/TRAEF | 动画及特效候选 | GLB 动画或独立元数据 |
| TRPMCATALOG/TRPOKECFG | Catalog 与模型配置 | SQLite 映射 |
| HKX | Havok 相关数据 | 按具体格式研究 |

工具：仓库 tools/ZA.TrinityDump、tools/pkNX、tools/Switch-Toolbox、tools/SCVI_Extract、tools/gftool；BNTX-Extractor 格式参考；Pillow 解码；Blender/Three.js 为规划中的模型输出/预览工具，并不表示已支持 ZA 全部格式。
