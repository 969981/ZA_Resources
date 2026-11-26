---
title: ZA 2.0.2 原版图片资产审计
tags: [ZA, image-resources, BNTX, research]
status: inventory-partial
source_commit: e44a63db22a9f295d43c34db3f67695d31ae8e7a
---
# ZAImageResourceAudit

[研究索引](README.md) · [资源来源规则](../../resource-provenance.md) · [审计脚本](../../../scripts/Audit-ZA-ImageResources.py)

## 证据与范围
基线为 master e44a63db22a9f295d43c34db3f67695d31ae8e7a。源数据只读。原生描述符记录 238546 个 Hash，238521 已命名，25 未命名；13181 个 Pack。历史 full-extract-audit.json 报告 238546 个 Hash 已按记录校验，不等价于本轮图像验证。

原生目录：`Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/`。不得混入 virtual_converted、第三方工具资源和 archive volumes 的重复记录。Git blob SHA 不等于原始 SHA256 或像素 SHA256。

## 本轮已核实的独立 UI 纹理
14 个 ui/tex 子树均返回 truncated=false。以下计数是文件路径，不是 BRTI 数或已解码图片数。

| 子目录 | BNTX 路径 | 子目录内独立 Git blob |
|---|---:|---:|
| chara | 48 | 48 |
| hud_shopping | 356 | 356 |
| hud_spmg | 220 | 191 |
| icon_donut | 82 | 82 |
| icon_item | 379 | 379 |
| icon_knr_big | 15 | 15 |
| icon_pokemon_last | 3 | 3 |
| logo_brand | 54 | 54 |
| map_pic | 67 | 67 |
| onepicture | 16 | 16 |
| photomode_pose | 26 | 26 |
| poke_spmg | 16 | 16 |
| ryl_npc | 37 | 37 |
| tips | 84 | 84 |
| 合计 | 1403 | 不跨目录相加 |

ui/data 有 76 个一级子目录、980 ARC 路径（665 个独立 Git blob，6041936216 字节）和 140 TRUIV 路径。ARC 内部格式和成员未验证。
ik_chara 完整子树含 5143 BNTX 路径，不能当成人物立绘数。
ik_pokemon/data 有 366 个一级目录；整体递归响应截断。样本定位 `pm0001/pm0001_00_00/icon/pm0001_00_00_00_0.bntx`、`..._1.bntx`。完整图标数 UNKNOWN。后缀语义需独立证明，禁止自动认定性别/异色。icon_pokemon_last 不是完整图标库。
icon_item/item_0001/item_0001.bntx 的数字只是候选 ItemID；需原生表/消费者验证。甜甜圈普通与 big 文件也不等价于已确认 41 种甜甜圈。

## 无截断 Git 清单
在本仓库 Git 工作树中运行：
```powershell
python scripts/Audit-ZA-ImageResources.py --self-test
python scripts/Audit-ZA-ImageResources.py --ref e44a63db22a9f295d43c34db3f67695d31ae8e7a --out .za-work/image-audit
```
脚本只读 Git 树元数据，生成 inventory.jsonl、summary.csv、mapping-candidates.jsonl、audit.json。按逻辑路径合并 7z 分卷，标记缺号或混合表示，不宣称原文件已恢复。统计不同 Git blob SHA 与路径数，不能代替像素去重。它不读取容器二进制，也不闭合 TRPFD 238546 Hash；待原生 index 与导出记录对账。合成测试包含重复 blob、分卷、缺号、排除派生目录、宝可梦图标分类。当前尚未执行实际脚本或测试。

## 后续模块与验收
- P0 ZAImageResourceAudit：Git 全树清单、原生索引交叉对账、未知 Hash 分类、BNTX 容器/BRTI 子纹理分开计数。
- P0 BNTXTextureDecoder：以仓库 tools/Switch-Toolbox 为候选，验证 BRTI 名称、格式、尺寸、mip、array、swizzle、色彩空间，记录 DDS 压缩数据及 PNG 解码 RGBA 的独立 hash；PNG 不是压缩源字节无损等价物。保留失败记录。
- P0 PokemonIconMapping：路径候选 → 原生 catalog/trpokecfg 与 UI 选择证据 → Species/Form/Gender/Shiny，未知用 null。
- P0 ItemIconMapping：ItemID→原生选择规则→BRTI；记录占位、共享和缺失。
- P1 UIArchiveExtractor：识别 magic、成员、偏移、语言，去重只作优化并保留路径；布局和 atlas UV 单独恢复。
- P1 DonutImageDatabase：关联真实食谱/效果 ID，普通与 big 作为表示变体。
- P1 TextureDecoderParityAudit：同一原始 payload 双解码器，逐通道 RGBA、alpha、色彩空间和 mip 差分，记录失败。
- P2 NativeModelRenderer：模型/材质/骨骼/姿势/相机；渲染产物与原生图标分开。

## 状态
CONFIRMED：上述完整子树的路径统计。CANDIDATE：文件名用途、数值映射。UNKNOWN：全库图标数、容器内部纹理、格式、像素和真实 ID 映射。禁止将游戏图片批量发布到公开仓库；本阶段只新增脚本和文档，输出留本地或按授权存储。
