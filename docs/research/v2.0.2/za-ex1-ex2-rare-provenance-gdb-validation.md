---
title: ZA 2.0.2 EX1／EX2 Rare 来源和 GDB 验证指南
aliases: [ZA EX1 EX2 Rare GDB, ZA Shiny Lock Native Source]
tags: [pokemon/za, reverse-engineering, shiny-lock, flatbuffers, gdb]
version: v2.0.2
updated: 2026-11-06
status: NATIVE_STATIC_PARTIAL_GDB_UNEXECUTED
---

# EX1 蒂安希／EX2 超梦：Rare 赋值来源和实机 PID 防闪验证

> [!IMPORTANT] 当前证据等级
> **已完成（原生静态）**：资源表的 EX1/EX2 任务→战斗→Spawner→遭遇条目；Rare 编码→原生描述对象 +0x68→64 位模式→0x656F80 PID 生成器→Never/Always/Random 分支、AntiShiny 及 Pokémon 字段写回。
>
> **未完成**：原始 FlatBuffers EncountData.Rare 到原生描述对象 +0x68 的真实反序列化/赋值链，以及真正运行 EX1/EX2 时的 GDB 分支与 PID 前后日志。本次提供**可运行的只读取证工具，但没有实际连接用户的模拟器**，绝不把合成测试当作实机验证。

## 1. 源数据结构

原生 Schema：[EncountDataDBArray.fbs](../../../tools/pkNX/FlatBuffers/ZA/World/Schemas/Encount/EncountDataDBArray.fbs)。`EncountData` 中 `Rare:int` 是字段索引 **6**（第七个字段）。FlatBuffers table 的实际内存位移由 vtable 决定，并非固定 `+0x68`。

| EncountData.Id | 物种 ID | 等级 | Rare 原值 | pkNX 解释 |
|---|---:|---:|---|---|
| `sub_119_diancie` | 719 | 70 | `0x1FFFFFFF` | Shiny.Never |
| `sub_120_mewtwo` | 150 | 70 | `0x1FFFFFFF` | Shiny.Never |

[FlatBuffers 原始证据](za-ex1-ex2-flatbuffers-evidence.json)、[原生 Spawner 精确关联](za-ex1-ex2-spawner-crosswalk.json)。

## 2. 当前已闭合的原生代码段

~~~asm
6560B4  MOV  X20,X0
656144  LDP  W8,W10,[X20,#0x68]  ; 原生描述对象 +0x68 的 32 位配置
656148  SXTW X8,W8
65614C  ORR  X8,X9,X8,LSL #4     ; X9=0xF
656160  CSEL X8,X8,X9,EQ         ; 某些情况下可能被覆盖
656170  STR  X8,[SP,#0x38]       ; state 起始于 SP+0x18，模式在 +0x20
656294  ADD  X0,SP,#0x18
656298  BL   #0x656F80           ; 真正 PID 生成器
657078  LDR  X9,[X19,#0x20]      ; 生成器内读取同一 mode
657168  BL   #0xE5D200          ; Never 条件防闪分支
657198  BL   #0xE5D21C          ; Always PID 调整分支
~~~

对应转换：

| 32 位描述值 | 64 位模式 | 原生分支 |
|---|---|---|
| `0x1FFFFFFF` | `0x1FFFFFFFF` | Never |
| `0x2FFFFFFF` | `0x2FFFFFFFF` | Always |
| `0x3FFFFFFF` | `0x3FFFFFFFF` | Random |

`0x653F34` 另有 `LDR W8,[X24,#0x68]`，后续在 `0x653F38` 与 `0x2FFFFFFF` 比较，支持该偏移属于 Rare/异色模式配置字段。**但尚未证明原始 FlatBuffers 字段是如何写入这个内存描述对象的。**

另一路 `0xE3EB64 BL 0x656F80` 后实际使用 `0xE3EBA8` PID setter、`0xE3EBB4` 物种 setter，证明生成器返回值和属性填充存在直接静态调用关系。详情见 [[za-native-shiny-generator-pid-branch]]。

## 3. 新增全 ELF 描述字段访问审计

[原始偏移交叉引用 JSON](za-rare-descriptor-offset68-xrefs.json) 来自 SHA-256 钉住的 v2.0.2 `main.elf`，GitHub Actions 通过真实文件扫描。

| 被扫描的 AArch64 unsigned-immediate 指令 | 数量 |
|---|---:|
| STR W +0x68 | 905 |
| LDR W +0x68 | 874 |
| STR X +0x68 | 3,255 |
| LDR X +0x68 | 16,074 |

**不要把任何仅仅同偏移的 STR 当作 Rare setter。** 当前最近的 `0x65610C STR W25,[SP,#0x68]` 是局部栈字段写入，不能证明向 `[X20+0x68]` 赋值。

仍需检查 `STUR`、`STP`、`memcpy`、SIMD 批量复制和反序列化对象构建。 [原生候选函数反汇编](za-rare-native-descriptor-origin-candidates.md) 已显示 `0x5E7AD4` 附近主要是句柄引用管理，`0x655E74` 是容器/哈希查找模式；**它们不能在当前证据下直接命名为 EncountData.Rare 解码器**。

## 4. 用户本地 GDB 的真正验证操作

本轮已提交两个脚本：

- [只读 GDB 记录器](../../../scripts/gdb/za_ex_rare_trace.py)
- [EX1／EX2 JSONL 对账分析器](../../../scripts/Analyze-ZA-EX-Rare-GDB.py)

GDB 记录器采集 `0x656144` 模式输入、`0x65614C` 转换、`0x656298` 生成调用、`0x657078` 模式分发、`0x657168` Never 分支、`0xE5D200` AntiShiny、`0xE3EBA8` PID setter、`0xE3EBB4` Species setter 等。所有写入均限于**本地 JSONL 日志**；它不调用 GDB 的目标内存写入功能、不修改寄存器、不打 IPS 补丁。

### 4.1 建立安全地址映射

本研究的地址是 ELF **静态虚拟地址**，不是已由 GDB 校验的 `main+offset`。必须先从真正的模块映射确定 `0xE5D20C` 对应的*运行时*指令地址，并读到机器字 `0x52040029`。用该运行时地址减去静态虚拟地址得偏差 `$za_bias`。

~~~gdb
set architecture aarch64
target remote YOUR_HOST:YOUR_GDB_PORT

# 先根据模块加载映射找到 E5D20C 的真实运行时 PC
x/wx 0xRUNTIME_E5D20C
# 应显示 0x52040029

set $za_bias = 0xRUNTIME_E5D20C - 0xE5D20C
source scripts/gdb/za_ex_rare_trace.py
~~~

`za_trace_start` 会预先校验 **4 处**原生 ARM64 指令指纹，若运行环境或偏差不匹配则拒绝安装断点。不能跳过这一保护性检查。

### 4.2 EX1 蒂安希（本机操作，尚未执行）

保存游戏至 EX1 战斗触发前，确保与 v2.0.2 ELF 版本一致：

~~~gdb
za_trace_start $za_bias EX1 za_ex1.jsonl
za_trace_mark ex1_before_battle
continue
~~~

此时在游戏中触发蒂安希战斗，然后中断 GDB 会话，再执行：

~~~gdb
za_trace_mark ex1_after_battle
za_trace_stop
~~~

### 4.3 EX2 超梦（独立记录）

在 EX2 超梦战斗前：

~~~gdb
za_trace_start $za_bias EX2 za_ex2.jsonl
za_trace_mark ex2_before_battle
continue
~~~

触发超梦战斗，在 GDB 中中断执行，然后：

~~~gdb
za_trace_mark ex2_after_battle
za_trace_stop
~~~

日志中的标签和人工 marker **不能单独证明是 EX1/EX2**。还要看 Species setter 真正设置了 719/150、该对象是否同时经 PID setter、原生模式是否出现 `0x1FFFFFFFF` 和 Never 调用是否真实命中。由于本次没有用户模拟器连接，本节命令是可复现的实验方法，不是假称已有实机结果。

### 4.4 两份日志自动对账

~~~powershell
python scripts/Analyze-ZA-EX-Rare-GDB.py --ex1 za_ex1.jsonl --ex2 za_ex2.jsonl --output za_runtime_evidence_local.json
~~~

汇总包含：模式 `0x1FFFFFFF` 与 `0x1FFFFFFFF` 的观测情况、Never／Always／Random 分支命中、AntiShiny 入口、EX1=719 / EX2=150 是否经 Species setter 写入、PID 和物种是否属于同一 Pokémon 对象。分析器**不会**把同一场景里看到两种数值直接当成源 FlatBuffers → 描述对象的内存拷贝已经证明。

### 4.5 本轮 CI 只验证脚本，不是 GDB 实测

~~~powershell
python -m unittest discover -s tests -p test_za_rare_descriptor_offset68.py -v
python -m unittest discover -s tests -p test_za_gdb_trace_contract.py -v
python -m unittest discover -s tests -p test_za_ex_gdb_summary.py -v
~~~

脚本合成测试已经由 GitHub Actions 成功执行。它们没有依赖用户 ROM、模拟器或 GDB 远程环境。

## 5. 目前不能勾选完成的证据

| 项目 | 状态 | 通过条件 |
|---|---|---|
| 原始 EX1/EX2 Rare 静态配置 | 已确认 | 原生 FlatBuffers 读取及 ID 精确连接 |
| 描述对象 +0x68 → 内部 PID 模式 | 已确认（静态） | ARM64 读取、转换和直接 BL |
| FlatBuffers Rare → 描述对象 +0x68 赋值 | **待验证** | 找到真正字段拷贝函数并证实相同对象指针 |
| EX1 蒂安希实际走 Never 分支 | **待 GDB** | 真实 EX1 战斗日志、719 物种、mode 与 PID 对照 |
| EX2 超梦实际走 Never 分支 | **待 GDB** | 真实 EX2 战斗日志、150 物种、mode 与 PID 对照 |
| 已验证的运行时 main+offset | **待 GDB** | 本机地址映射、四处指纹及实际命中 |

对源赋值建议从真实的原生描述对象指针进行反向数据流追踪，而不是继续搜单一常量；如果准备使用 GDB watchpoint，必须在赋值**发生之前**拿到同一对象指针，否则在 `0x656060` 入口才设写监视点无法捕获历史写入。

关联：[[za-native-shiny-generator-pid-branch]]、[[za-legendary-shiny-lock-diancie-mewtwo-events]]。
