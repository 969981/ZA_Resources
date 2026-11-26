---
title: ZA NativeMaterialParser 与 NativeTexturePatternResolver
tags: [ZA, BFLYT, BFLAN, material, texture, Obsidian]
status: native-samples-confirmed-full-resolver-ci-pending
---
# ZA 原生材质与纹理选择
[[za-ui-layout-material-animation]] · [[za-image-resource-pack]]
## 已通过的全量基线（2026-11-26）
[Actions 45771214568](https://github.com/969981/ZA_Resources/actions/runs/45771214568)，commit 60bcf71e61eba9947aad4b4fb6e69ddd0e2fe289，artifact 15094562074 (SHA256 ee6f58611ad5fe068e591fd843239a64642791a0a06ac0ae8ddc1191e82bb5f1)。980 ARC 路径 / 665 unique blob / 315 aliases；664 Combined BNTX / 32640 BRTI；3352 FLYT（3342 成功、10 失败）；20798 FLAN 成功；53918 material、21885 txl refs（20973 local exact、912 missing），37379 pic1（33550 FULL、3829 OTHER），130276 animation targets、8511 FLTP tracks、4796 FLTS tags。无 FLAN partial errors。独立 BNTX 2597 路径 / 2568 blobs，与 Combined 合计 35208 条成功解码候选。PNG 未上传，双解码器与 runtime 未确认。
## 新增原版材质证据
直接读取原始 ARC 字节，基线 7f75e42176c8c3a114399f113a21aca2c0eea205，源目录 ui/data/。
| 原始 ARC | flags | size | 样本 / 证据 |
|---|---|---:|---|
| dummy/dummy_icon_type.arc | 0x15 | 84 | P_00；54 条材质同布局，颜色头 00 02 04 08 |
| btl_app/btl_app_trainer_ball_00.arc | 0x400 | 48 | P_bg_06；44 byte 基础之后 01 04 01 00 |
| hud_ball/hud_ball_00.arc | 0x415 | 88 | P_shadow_00；map index=3，sampler 06/06；SRT (0.5,0.5,0,2,2)，尾 01 04 01 00 |
| btl_app/btl_app_waza_last_01.arc | 0x20000 | 52 | T_01，额外8 bytes |
| 同上 | 0x8415 | 108 | P_type_icon_00 |
| 同上 | 0x46A | 132 | P_btn_ef_00，双 map 与双 SRT |
| 同上 | 0x446A | 144 | P_type_base_21 |
| quest_info/resident_ui.arc | 0x0 / 0x15 | 44 / 84 | 19 条无纹理材质，4 条基础纹理材质 |

公开参考：https://epd.zeldamods.org/wiki/Bflyt 与 https://github.com/Tyulis/3DSkit/blob/master/doc/BFLYT.md 。参考不同版本，位域语义不能直接等同 ZA 原生证据。
材料模型：flags bits 0–1 map count、2–3 SRT、4–5 coord gen、6–8 combiner、9 alpha、10 blend、12 combined blend、14 rotate、15–16 projection、17 font color；扩展字段保留候选。原始颜色头 00 02 04 08 支持两个 RGBA（+36/+40），其他颜色头拒绝猜测。map 4 bytes、SRT 20、coord 16、combiner 4、alpha 8、blend 4、rotate 12、projection 20、font color 8 为待全量核验的尺寸模型。0x15 的边界 44+4+20+16=84；0x415 再加4=88；0x46A 44+8+40+32+4+4=132。边界闭合不证明 shader 语义。所有未知尾字节和失败保留。
## NativeTexturePatternResolver
读取已通过的固定 Actions metadata；保留同 ARC 原名匹配、全局唯一名称候选、全局同像素候选、全局歧义、缺失；同名不等于同图。FLTP 每个关键帧静态索引、material/pane target 候选、纹理源记录入 SQLite/JSONL。多个同名目标不能自动挑选，跨容器选择未证明；不实现运行时触发条件。UV 细分完整、局部轴对齐、翻转、超范围、多组、退化、非轴对齐；不自动裁切。像素去重键=(width,height,RGBA SHA256)，保留源路径、语言别名及材质差异。
扩大名称候选域 types/balls/badges/ribbons/moves/status/items/donuts/hidden_ui，重叠计数，不能直接作为 TypeID/ItemID/RibbonID。特别注意 rank、ryl、waza 等宽关键词包含背景和状态 UI，不能当成真实奖章/招式分类图标。
## 复现
```powershell
python scripts/Audit-ZA-NativeMaterials.py --self-test
python scripts/Audit-ZA-NativeMaterials.py
python scripts/Resolve-ZA-UITextures.py --self-test
# 先恢复上一轮 ui-layout 与 ZAImageResources/manifests
python scripts/Resolve-ZA-UITextures.py
```
CI [za-native-ui-resolver.yml](../../../.github/workflows/za-native-ui-resolver.yml) 分两 job：从原始 ARC 重新审计 material；下载固定 run 的 metadata 做 resolver。输出 ui-material/materials.jsonl, errors.jsonl, summary.json；ui-resolver/semantic-candidates.jsonl, layout-refs.jsonl, uv-audit.jsonl, pattern-resolutions.jsonl, ui-index.sqlite, summary.json。仅元数据。新 CI 尚未验收。
## 后续
处理10 FLYT失败、完整材质扩展与 FLTS key、跨 ARC 实际消费者与语言选择；依据原生表/ELF/runtime 证明奖章、精灵球、属性、招式分类 ID。实现像素差分及图集裁切前不声称 UI 渲染等价。

## 2026-11-26 texture-index 实际验收
[Run 45772417428](https://github.com/969981/ZA_Resources/actions/runs/45772417428) texture-index job success，artifact [15094646939](https://github.com/969981/ZA_Resources/actions/runs/45772417428/artifacts/15094646939)，SHA256 b0d3e0cde86df208c493e7455108577f13d5859f6b3932db4963e4a8cf5293fe。
- 35208 texture rows / 5549 distinct names / 7401 distinct (width,height,RGBA hash) / 27807 duplicate pixel rows. Pixel parity still not independently verified.
- FLTP 8511 tracks, 29838 keys local exact; target 5791 unique candidates, 2710 ambiguous, 10 missing. Static frame table names only.
- 20973 layout refs local exact, 912 missing even in global exact-name index. No global hit; not proven nonexistent.
- UV 33550 full, 2614 outside range, 1177 flipped rectangle, 34 multi UV, 4 non-axis-aligned; no plain subrect in this scan.
| Domain candidate | Rows | Distinct names | Pixel groups |
|---|---:|---:|---:|
| types | 1636 | 112 | 254 |
| balls | 57 | 8 | 8 |
| badges (broad rank/ryl) | 5535 | 605 | 901 |
| ribbons | 168 | 18 | 17 |
| moves | 242 | 24 | 29 |
| status | 181 | 17 | 73 |
| items | 790 | 399 | 398 |
| donuts | 2350 | 261 | 326 |
| hidden_ui | 597 | 45 | 38 |
Overlaps and keyword candidates only. Native-material job pending. New [name family report](../../../scripts/Report-ZA-UINameFamilies.py) and [CI run 45772556054](https://github.com/969981/ZA_Resources/actions/runs/45772556054) preserve exact names, narrower keyword candidates, missing reference frequencies, original FLYT errors. Pending results.
