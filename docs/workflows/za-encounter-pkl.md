---
title: "Z-A v2.0.2 野生遭遇 PKL 打包与验证"
tags: [pokemon/za, pkhex, encounter, flatbuffers]
version: "2.0.2"
status: "PACKER_TESTED_SYNTHETIC_FULL_DUMP_PENDING"
---

# Z-A 遭遇 PKL 构建与校验

> [!important] 范围
> 本工具是 pkNX 导出 `*_slot_sets.json` 之后的**打包器/结构校验器**，不是 RomFS 原始文件解析器。它只生成 `encounter_za.pkl`。异次元 `encounter_hyperspace_za.pkl` 仍由 pkNX 导出，本工具负责校验。不可用 Python pickle 加载。

## 入口

- 打包器：[`scripts/encounters/za_pkl_tool.py`](../../scripts/encounters/za_pkl_tool.py)
- 合成测试：[`tests/test_za_pkl_tool.py`](../../tests/test_za_pkl_tool.py)
- 原始资源格式与实读结果：[[../research/v2.0.2/za-encounter-resource-formats|Z-A 五类原始资源结构]]
- pkNX 导出器：[`SpawnRipper9a.cs`](../../tools/pkNX/pkNX.WinForms/Subforms/Gen9a/Map/SpawnRipper9a.cs)
- PKHeX 读取实现：<https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Templates/Gen9a/EncounterArea9a.cs>

## 从仓库根目录运行（PowerShell / Windows）

先用 pkNX 的 Z-A Game Dumper（`DumpSpawners`）从完整的、合法取得的 v2.0.2 资源导出 `spawner/t1_slot_sets.json`、`t2_slot_sets.json`、`t3_slot_sets.json`。pkNX 还负责独立输出 `spawner/encounter_hyperspace_za.pkl`。

```powershell
py -3 scripts/encounters/za_pkl_tool.py --build .\spawner\t1_slot_sets.json .\spawner\t2_slot_sets.json .\spawner\t3_slot_sets.json --out .\.za-work\encounters\encounter_za.pkl
py -3 scripts/encounters/za_pkl_tool.py --inspect .\.za-work\encounters\encounter_za.pkl
py -3 scripts/encounters/za_pkl_tool.py --inspect .\spawner\encounter_hyperspace_za.pkl
py -3 -m unittest discover -s tests -p test_za_pkl_tool.py -v
```

全部是 Python 标准库，不需要 pip 依赖。输出放在被忽略的 `.za-work`，**不要自动替换** PKHeX 上游的资源。

## PKL 真实二进制布局

`BinLinker16`：开头 `za` 两字节标识，`u16` 区域数量、`u16[count+1]` 绝对偏移表。每个区域先写 `u16 Location`、`u16 Reserved=0`，之后连续写 8 字节遭遇槽：

| 偏移 | 类型 | 字段 |
|---|---|---|
| 0 | uint16 LE | National Species（pkNX `SpeciesConverterZA.GetNational9`） |
| 2 | uint8 | Form |
| 3 | byte | Gender（`-1` 写入 `0xFF`） |
| 4 | uint8 | LevelMin |
| 5 | uint8 | LevelMax |
| 6 | uint8 | IsAlpha（0/1） |
| 7 | uint8 | Shiny（Random=0、Never=1、Always=2） |

**容易混淆：** `pkNX.Shiny` enum 为 Random=0、Always=1、Never=2，导出 PKL 时必须重新编码，不能直接复制 JSON 中的整数。普通与异次元 PKL 均使用标识 `za`，以文件名和 PKHeX 调用时的 `SlotType9a` 区分。

## 安全门禁、去重与已验证范围

- 只接收 Location 名称末尾带 `(数字)` 的 pkNX slot sets JSON。
- 拒绝超过 `u16` 的地点、非法等级、非法性别、固定性格（需 Static 模型）及 16-bit BinLinker 偏移溢出。
- 相同地点、种族、形态、性别、头目和异色限制按**相交的等级区间**合并，不合并仅相邻区间。
- 已运行 6 项合成测试；尚未在本轮完成完整 v2.0.2 pkNX 导出、官方资源二进制对比或 PKHeX 合法性回归。
- PKL 不能保留时间、天气、权重、Spawner ID、任务条件、固定招式/IV、赠送与交换信息；请同步保存上游详细 JSON。

## 复核顺序

1. 核对原始资源路径、大小、SHA，详见原始格式研究文档。
2. 核对 pkNX `SceneInfo9a` 地图清单及未命中 Spawner、缺失 Location ID。
3. 导出完整 JSON 与两份 PKL，分别校验结构、SHA 和地点数量。
4. 对比当前 PKHeX 的 `encounter_za.pkl` 与 `encounter_hyperspace_za.pkl`；不仅比较字节，还要比较按地点排序后的槽位集合。
5. 固定剧情、头目战、赠送、交换分别检查 `EncounterStatic9a`、`EncounterGift9a`、`EncounterTrade9a`，不能错归野生 PKL。
6. 使用真实合法 Z-A 存档样本做 PKHeX 判定回归，未验证部分明确标记 UNKNOWN。
