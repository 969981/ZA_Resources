---
title: ZA BNTX 与宝可梦图标原生映射
tags: [ZA, BNTX, PokemonIconMapping, research]
status: sample-metadata-confirmed
---
# BNTXTextureDecoder 与 PokemonIconMapping
[[za-image-resource-audit]] · [Decoder](../../../scripts/Decode-ZA-BNTX.py) · [Catalog probe](../../../scripts/Probe-ZA-PokemonCatalog.py)

## 原版实证
master 基线 e44a63db22a9f295d43c34db3f67695d31ae8e7a。通过 GitHub 内容接口读取原始字节，不是文件名猜测。
| BRTI name | Git blob SHA | BRTI offset | size | format |
|---|---|---:|---|---|
| pm0001_00_00_00_0 | edce3e3ee53cba36f56e67966baa083f1a4fe8ac | 0x1F8 | 160×160 | 0x2001 BC7 UNORM |
| pm0001_00_00_00_1 | 5ac99a8104aa54faf31233ef05eae05375a720bc | 0x1F8 | 160×160 | 0x2001 BC7 UNORM |
| item_0001 | 21cfafc9db79df1ff8c8a71f90e4d68e3ceef442 | 0x1F0 | 160×160 | 0x2001 BC7 UNORM |

三者均 45160 bytes，RGBA 通道选择 2/3/4/5，单 mip、单 array。首样本 mip 指针表 0x498，payload 0x1000，存储空间 40960 bytes，alignment 512，layout low=2，high=65543，tile mode=0。Alpha 通道存在不等于使用透明像素。布局参考 https://nintendo-formats.com/libs/nw/bntx.html 与 https://github.com/aboood40091/BNTX-Extractor；像素尚待 CI 与第二解码器验收。

## Catalog 证据
`ik_pokemon/catalog/catalog/poke_resource_table.trpmcatalog`，275948 bytes，blob d8facfafebe3de732b5a7fe0071f38e13cd819c5。
FlatBuffers root offset=12，root slot 1 vector=24，637 条记录。实际读取索引 0/1/2/3/4/5/636 对应 pm0000_00_00、pm0001_00_00、pm0002_00_00、pm0003_00_00、pm0003_01_00、pm0003_51_00、pm9999_00_00。
slot 1=.trmdl, 2=.trmmt, 3=.trpokecfg, 6=模型 .bntx（非 UI icon 路径），8=.hkx；slot 0 原始字段留待语义研究。目录匹配不等于运行时选择。物种/形态/性别/异色均保持 null，文件名数字只作为候选。

## 复现
```powershell
python -m pip install Pillow==11.3.0
python scripts/Audit-ZA-ImageResources.py --out .za-work/image-audit
python scripts/Decode-ZA-BNTX.py --self-test
python scripts/Decode-ZA-BNTX.py --inventory .za-work/image-audit/inventory.jsonl --out .za-work/bntx
python scripts/Probe-ZA-PokemonCatalog.py --candidates .za-work/bntx/pokemon-candidates.jsonl --out .za-work/bntx
```
可选本地 --export .za-work/local-images 导出支持的 DDS/PNG。不要提交游戏素材。CI 仅归档 JSONL 与摘要，保留失败、非 raw 分卷和不支持格式。解码器仅支持 swizzled BC7 2D single mip identity RGBA，其他格式仅元数据；不等于全格式 decoder，且未经双解码器像素对账。

## 验收
- textures.jsonl: BRTI 指针、名称、格式、尺寸、mip、channel、源/压缩/像素 SHA256 与 Alpha 分布。
- failures.jsonl: 读取/结构/分卷失败；textures.jsonl decode_status 表示不支持与解码失败。
- pokemon-candidates.jsonl: 文件名候选；pokemon-catalog-join.jsonl: 原生 catalog 目录连接，不推断 Form/Gender/Shiny。
- catalog-records.jsonl 与 catalog-summary.json: 637 原生配置的可复现枚举及连接统计。
- summary.json: 路径、BRTI、格式与解码分别计数；不得将 CI 成功等同于零失败/全图像完整。
- 下一步恢复 trpokecfg 字段及 UI selector 的消费者，验证普通/异色、雌雄差异、特殊形态、占位与缺失；双解码器对比像素，扩展 ASTC/BCn、多 mip、array 与 ARC。
