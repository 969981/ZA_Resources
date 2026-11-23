---
title: "Z-A v2.0.2 EncountData ActivationCondition 真实 FlatBuffers 条件统计"
tags: [pokemon/za, encounters, conditions, flatbuffers]
version: "2.0.2"
status: "CONFIRMED_SOURCE_BYTES_SEMANTICS_UNKNOWN"
updated: "2026-11-23"
---

# EncountData 原始条件（逐层解码）

> [!important] 本轮证据
> 已从仓库原始 v2.0.2 的 encount_data_array.bin（503,348 bytes）直接读取 13 组、1,966 条 Encounter 的 ActivationConditionArray；再逐层走 ActivationCondition → Element[] → ActivationConditionParam[]，提取 Condition、Op、Param。**下列是字段原始值，不代表实机已满足条件，不推断 Op 的布尔逻辑。**

## 分组统计

- Encounter 记录总数：1,966。
- 拥有非空 ActivationConditionArray 的 Encounter：**878**。
- 实际解出的 ActivationConditionParam：**934**。

| 原始 Condition 字符串 | 参数记录数 | 原始 Op |
|---|---:|---:|
| phase_condition | 759 | 5 |
| momiji_wild_zone_condition | 170 | 1 |
| force_condition | 5 | 0 |

这些是参数记录数量，不能当作独立 Encounter 数或稀有概率。多条 Param 可以出自同一个 Encounter。

## 实际样本

| Encounter ID | Condition | Op | Param 原始字符串 |
|---|---|---:|---|
| ect_a0201_w01_v01_z225 | momiji_wild_zone_condition | 1 | ["12"] |
| ect_a0202_w01_v01_z079 | momiji_wild_zone_condition | 1 | ["10"] |
| ect_a0202_w02_v01_z016 | momiji_wild_zone_condition | 1 | ["5"] |
| ect_a0202_w02_v01_z016 | phase_condition | 5 | ["30900"] |
| ect_d01_01_z023 | phase_condition | 5 | ["87000"] |
| ect_d02_01_z559 | phase_condition | 5 | ["53000"] |
| ect_zdm406_sp01_067 | phase_condition | 5 | ["0"] |
| ect_subq147_p1 | force_condition | 0 | [] |

原始 schema：

- [ActivationCondition.fbs](../../../tools/pkNX/FlatBuffers/ZA/Shared/Schemas/Shared/ActivationCondition.fbs)
- [ActivationConditionElement.fbs](../../../tools/pkNX/FlatBuffers/ZA/Shared/Schemas/Shared/ActivationConditionElement.fbs)
- [ActivationConditionParam.fbs](../../../tools/pkNX/FlatBuffers/ZA/Shared/Schemas/Shared/ActivationConditionParam.fbs)
- [EncountDataDBArray.fbs](../../../tools/pkNX/FlatBuffers/ZA/World/Schemas/Encount/EncountDataDBArray.fbs)

## 下一阶段

1. 将 Condition、Op、Param 与真实 ARM64 判定函数或 Lua 条件求值关联，确认 Op=0/1/5 代表的真实逻辑，不直接以数值推断。
2. 交叉核对任务阶段、野生区解锁、天气/时间和 DLC 异次元条件。
3. 对 2,211 个 Spawner 与各目标 EncountDataInfoList 同样导出 ActivationConditionList；自动化解析代码位于 [za_condition_audit.py](../../../scripts/encounters/za_condition_audit.py)，全量结果应以 CI 的 za_condition_summary.json 为准。
4. 用实机抓取完整生成调用栈、条件输入和 PID/IV 生成结果，才能把 CONFIGURED 升级为 CONFIRMED_RUNTIME。

关联入口：[全量 Spawner→Encounter→PKHeX 账本](za-encounter-crosswalk-v2.0.2.md) · [运行复现指南](../../workflows/za-encounter-crosswalk.md)。
