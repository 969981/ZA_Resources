---
title: ZA v9 BFLYT BFLAN 与 Combined BNTX 原生引用研究
tags: [ZA, BFLYT, BFLAN, BNTX, UI, Obsidian]
status: native-four-arc-samples-confirmed-full-ci-pending
---
# ZA UI Layout / Material / Animation
[[za-image-resource-pack]] · [[za-native-pokemon-icon-selector]]
原版读取基线 7f973a728f562ded5adc0df1aec9b191f1e306f5。原始路径前缀 Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/ui/data/。实际 SARC 成员字节解析，非文件名猜测。
| ARC | FLYT | FLAN | Combined BRTI | txl refs | 同 ARC BRTI 名称命中 | mat1 | pic1 | 完整 0–1 UV |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dummy/dummy_icon_type.arc | 1 | 0 | 54 | 54 | 54 | 54 | 54 | 54 |
| btl_app/btl_app_hit_marker_00.arc | 2 | 4 | 8 | 8 | 8 | 32 | 32 | 32 |
| btl_app/btl_app_trainer_ball_00.arc | 3 | 14 | 4 | 3 | 3 | 27 | 27 | 26 |
| hud_ball/hud_ball_00.arc | 3 | 16 | 7 | 10 | 8 | 21 | 14 | 12 |
| 合计 | 9 | 34 | 73 | 75 | 73 | 134 | 127 | 124 |

原版头 FLYT/FLAN little endian, header 0x14, version 0x09000000。直接确认：
- txl1: count +0x08 u16，offset table +0x0C，字符串偏移以表起点为基准。
- mat1: count +0x08，record offset table +0x0C，偏移相对 section。样本 record name 28 bytes，flags +0x1C，低2位为纹理 map 数的候选，首 map +0x2C，u16 texture index +2 sampler bytes。颜色 raw words +0x24/+0x28。未完成 shader/材质全字段。
- pic1: pane name +0x0C，alpha +0x0A，10 floats from +0x2C，vertex colors +0x54，mat index +0x64，UV count byte +0x66，8 floats each from +0x68。完整 UV = TL(0,0), TR(1,0), BL(0,1), BR(1,1)。
- 属性布局 P_00 → mat[0] P_00 → txl[36] → grptxt_icon_type_text_00_normal_00^q。54/54 引用命中，54/54 完整 UV，说明此布局使用独立 BRTI，不需要从大图切出54格。显示尺寸不等于纹理尺寸。
- 球 UI P_ball_ds_00 → mat[2] → txl[0] → btl_app_icon_ball_00^t；是 UI 状态图标，非已证实 BallID。
- 127 个 pic1 中 124 为完整单组 UV，3 为其他 UV（需逐项研究，不能自动当作可裁矩形）。HUD 2 个未命中 texture reference 保留，不推断缺失原因。
- FLAN pai1 +0x08 frame count, +0x0C texture count, +0x0E entry count, +0x10 target offset-table pointer. Target name 28 bytes, tag count +28, type +29, tag-offset table +32. 观察 FLPA/FLVI/FLVC/FLMC/FLTP。
- 真实 FLTP 证据：anim/btl_app_ball_set_00_passive_to_active_A_00.bflan、..._B_00.bflan，各2个 target P_focus_A_00/01、P_focus_B_00/01；data type=1，每条2帧，frame 0 value=0 → btl_app_focus_01^t；frame 5 value=1 → btl_app_focus_2v2_00^t。该静态纹理表索引关系不等同于运行时触发条件，也不代表球种选择。

## 复现与边界
参考格式资料（旧版本不能直接套用）：https://nintendo-formats.com/libs/nw/bflyt.html 与 https://github.com/Tyulis/3DSkit/blob/master/doc/BFLAN.md。
```powershell
python scripts/Audit-ZA-UILayout.py --self-test
python scripts/Audit-ZA-UILayout.py --out .za-work/ui-layout
```
新增 sources/layouts/animations/combined-textures/errors.jsonl 与 summary.json，保留 ARC 别名与原始 SHA、section offsets、UV、纹理表候选连接、FLTP raw key。只扫描跟踪的 ui/data ARC，按 blob 去重；分卷未恢复，其他 BNTX 不混入 Combined 计数。v9 之外、特殊 target 类型、跨 ARC 纹理、非单一矩形、材质 SRT/混合/shader、运行时 selector 保留未验证。合成测试和全量 Actions 以实际执行结果为准。原始素材不修改、不公开上传 PNG。
## 下一步
1. 全量 980 ARC 对账，统计所有 Combined、FLYT/FLAN、未关联纹理和失败。
2. 恢复其他 UV 的矩形/翻转/重复/材质 SRT，禁止直接以 pane 尺寸裁切。
3. FLTP 与 FLTS/FLMC/FLVC 关键帧及材质合成，查明奖章、招式、球、状态 UI 的真实资源消费者。
4. 双解码器 RGBA 对账及 SQLite 原生 ID resolver。
