---
title: Z-A v2.0.2 Rare ARM64 静态扫描与事件运行时证据审计
tags: [ZA, ARM64, Rare, shiny-lock, FlatBuffers]
version: v2.0.2
status: STATIC_TRIAGE_COMPLETE_RUNTIME_UNKNOWN
updated: 2026-11-06
---

# Z-A v2.0.2 Rare 与神兽锁闪：原生 ARM64 排查记录

> [!WARNING] 核心结论
> 已验证事件触发器到战斗配置的中间资源，已通过 SHA-256 核实主程序 ELF 并真实执行 ARM64 常量扫描和 Capstone 反汇编。**尚无一个能确证为真正 Rare 消费者、PID 异色判定或锁闪分支的 main+offset。** 与 Rare 值相同的立即数不代表代码正在处理 Rare。

## 一、固定版本、原生输入与证据

- 游戏：Pokémon Legends: Z-A v2.0.2
- 源 ELF：Unpack/v2.0.2/exefs/main/main.elf
- SHA256：470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d
- manifest NSO Build ID：b1f12fd919eae86ab8a978317677e64bce443d1f000000000000000000000000
- 原始战斗表：Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/ik_event/bin/event_wild_battle_data/wild_btl_data_global.bin
- [静态扫描 JSON](za-rare-arm64-static-candidates.json)
- [实际五处反汇编](za-rare-arm64-exact-sites.md)
- [原支线与锁闪数据分析](za-legendary-shiny-lock-diancie-mewtwo-events.md)

## 二、完成的中间资源闭合

trigger_sub_0119.bin / trigger_sub_0120.bin 内的 Command 53 原生参数分别为 btl_sub_119、btl_sub_120。

wild_btl_data_global.bin 是确实存在的另一份独立原始 FlatBuffers。根向量共有 **68** 条记录：

| 原生索引 | table 文件偏移 | Field 0 战斗名 | Field 1 字符串 | Field 9 字符串 | Field 14 字符串 |
|---:|---|---|---|---|---|
| 42 | 0xBE8 | btl_sub_119 | id_sub119_01 | bae_Ev_sub_119_010 | wild_common_3 |
| 43 | 0xB9C | btl_sub_120 | id_sub120_01 | bae_Ev_sub_120_010 | 无 |

已静态证实：trigger Command 53 关联到上表 Field 0 具体记录。未从游戏实现确认 Field 1/9/14 的正式业务语义。

需要继续证实：id_sub119_01 如何关联到遭遇表 sub_119_diancie、id_sub120_01 如何关联到 sub_120_mewtwo；以及由哪一个原生函数实例化 Pokémon。

## 三、已确认的数据层 Shiny 配置

遭遇表 sub_119_diancie（719 / Lv70）与 sub_120_mewtwo（150 / Lv70）的 Rare 都为 0x1FFFFFFF。本仓库 pkNX 的 EncounterSlot9a.GetShiny 映射如下：

| Rare 原值 | pkNX 解释 |
|---|---|
| 0x1FFFFFFF | Shiny.Never |
| 0x2FFFFFFF | Shiny.Always |
| 0x3FFFFFFF | Shiny.Random |

这属于静态数据配置和源码映射的确认，不是主程序 ARM64 原生判断已验证。

## 四、真实主程序 SHA 校验与常量扫描

在 GitHub Actions 完整运行 6 项合成测试、ELF SHA 校验、原生战斗表解析、AArch64 指令扫描和 Capstone 反汇编，均已通过。

- 立即数精确值 0x1FFFFFFF：5 个可执行指令点。
- 立即数精确值 0x3FFFFFFF：111 个点。
- 被监控掩码聚合成启发式候选分组：74 组。
- 0x1FFFFFFF 的 5 个点均已在真实 ELF 上导出前后 0x100 字节的反汇编。
- **能据此确认属于 Rare 实例生成 / 异色判断的地址：0 个。**

### 五处精确掩码的人工复核

| ELF 静态地址 | 指令 | 观察到的邻域 | 对锁闪研究的判定 |
|---|---|---|---|
| 0xE28C54 | AND W9,W9,#0x1FFFFFFF | 浮点/向量几何计算、索引循环、跳转表 | 与直接 Rare 判断无已知关联；排除作为直接锁闪证据 |
| 0xE28CE0 | AND W9,W9,#0x1FFFFFFF | 与上一条同一向量路径 | 同上 |
| 0x1F01278 | AND W10,W10,#0x1FFFFFFF | 缓冲区索引/计数、0x40 边界运算 | 与直接 Rare 判断无已知关联；排除作为直接锁闪证据 |
| 0x2E36644 | AND W28,W9,#0x1FFFFFFF | 宽整数位操作、移位、存储复制 | 与直接 Rare 判断无已知关联；排除作为直接锁闪证据 |
| 0x2E3672C | AND W28,W8,#0x1FFFFFFF | 相同位段操作，随后使用 0x0FFFFFFF | 同上 |

> [!IMPORTANT] 地址性质
> 这些均为静态 ELF 指令虚拟地址，尚未按模块加载映射和运行时指令寄存器状态确认。不可把这些位置当作已证实的锁闪补丁、GDB Hook 或 main+offset。周围函数是否在全局调用图与 Pokémon 有关联也尚未完全排除。

重要遗漏情况：Rare 编码可能通过 MOVZ/MOVK、常量池、LSR/UBFX 高位抽取、间接函数调用或解码阶段转换；只搜完整 0x1FFFFFFF 常量是有限的第一层排查。

## 五、下一层真正要解决的研究问题

1. **跨表引用**：查找两个 id_sub... 条目的资源消费者，证明战斗对象到具体 encounter Id 的真实指针链/名称映射，而不根据命名直接推断。
2. **字段来源追踪**：跟踪 EncountData.Rare 的原生解码读取点，特别是高位标志 (bit 28..29 等) 的位域提取及相关分支。
3. **生成过程**：由实例生成函数追踪 Pokémon PID、随机种子、TID/SID、异色判定、保护性改写，以及最终对象落盘。
4. **运行时确证**：在具备本版本 NSO Build ID 的测试环境，记录 PC、LR、指针、Rare 值、PID 前后、是否触发分支，并用随机异色和固定异色条目做对照。
5. **升级证据等级**：只有上述连续执行链路复现后才把 UNKNOWN 改成 CONFIRMED / main+offset。

## 六、复现方法

~~~powershell
python -m unittest discover -s tests -p test_za_rare_arm64.py -v
python scripts/Scan-ZA-Rare-ARM64.py --limit 60
python -m pip install capstone==5.0.6
python scripts/Trace-ZA-Rare-Candidates.py
~~~

- [扫描脚本](../../../scripts/Scan-ZA-Rare-ARM64.py)
- [反汇编脚本](../../../scripts/Trace-ZA-Rare-Candidates.py)
- [GitHub Actions 工作流](../../../.github/workflows/za-rare-arm64-static.yml)

## 七、证据等级

- CONFIRMED（静态）：原始 Rare 值、pkNX Never/Always/Random 映射、两条 Battle 记录、ELF SHA、5 个直接常量位点的实际反汇编。
- CANDIDATE：未来对数据结构消费函数和高位提取指令的交叉引用路径。
- UNKNOWN：游戏本体实际 Rare 消费者、EX1/EX2 触发到实例生成器的完整调用图、最终 PID/锁闪分支、已验证的 main+offset。
