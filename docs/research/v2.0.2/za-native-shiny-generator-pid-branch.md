---
title: ZA v2.0.2 原生三态异色生成分支与 PID 防闪证据
aliases: [ZA Rare Native Generator Branch, ZA Shiny PID ARM64]
tags: [pokemon/za, reverse-engineering, arm64, shiny-lock, PID, RNG]
version: v2.0.2
status: NATIVE_STATIC_SHINY_MODE_CONFIRMED_RARE_CONSUMER_UNKNOWN
updated: 2026-11-06
---

# Z-A v2.0.2 原生异色模式分发与 PID 防闪：实际 ARM64 证据

> [!IMPORTANT] 研究结论
> 这是**真实游戏原生主程序的静态反汇编**，不是仅参考 PKHeX 写出的伪代码。已找到完整的三态 PID 异色生成路径，含随机重掷、条件防闪、强制异色辅助函数和写回内存；且找到另一条从 Pokémon TID/PID getter 直接读取并防闪后交给 PID setter 的路径。
>
> **未验证** EX1 蒂安希 / EX2 超梦在运行时实际执行上述分支；尚未追踪到 `EncountData.Rare` 32 位字段读取后如何变为内部 64 位模式；没有 GDB 单步记录。不应把这里所有 ELF VA 自动当作已验证可使用的 `main+offset` Hook。

## 1. 数据、二进制来源和可复现运行

- 原生 ELF：`Unpack/v2.0.2/exefs/main/main.elf`（66,579,944 B）
- ELF SHA-256：`470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d`
- ExeFS manifest Build ID：`b1f12fd919eae86ab8a978317677e64bce443d1f000000000000000000000000`
- [原生 AntiShiny 和候选 EOR 反汇编](za-rare-arm64-anti-shiny-xor-sites.md)
- [三态分发函数及调用者的实际反汇编](za-pid-antishiny-caller-contexts.md)
- [B/BL 原生直接调用证据 JSON](za-pid-accessor-callsite-xrefs.json)
- [SHA 钉住的完整 ARM64 掩码扫描 JSON](za-rare-arm64-static-candidates.json)
- [GitHub Actions 成功记录：原生 EOR](https://github.com/969981/ZA_Resources/actions/runs/42205788050)
- [GitHub Actions 成功记录：关联原生 PID 分支](https://github.com/969981/ZA_Resources/actions/runs/42206252176)

所有十六进制 PC 是本版本**静态 ELF 虚拟地址**。文件偏移、ELF VA、运行时模块偏移必须区分。

## 2. 实际发现的 Native 异色判断与防闪函数

### 2.1 异色 XOR 判断：ELF VA 0xE5D1E8

~~~asm
E5D1E8  EOR  W8,W1,W0
E5D1EC  AND  W9,W8,#0xFFF0
E5D1F0  EOR  W8,W9,W8,LSR #16
E5D1F4  CMP  W8,#0x10
E5D1F8  CSET W0,LO
E5D1FC  RET
~~~

根据输入形式，此处按两个 32 位值计算 XOR 并返回是否低于 16，匹配 PID 与 Trainer ID 的异色判定。函数用途由位运算直接支持，但入口参数的语义仍需由全部调用者做实证核查。

### 2.2 条件防闪：ELF VA 0xE5D200

~~~asm
E5D200  EOR  W8,W1,W0
E5D204  AND  W9,W8,#0xFFF0
E5D208  EOR  W8,W9,W8,LSR #16
E5D20C  EOR  W9,W1,#0x10000000
E5D210  CMP  W8,#0x10
E5D214  CSEL W0,W9,W1,LO
E5D218  RET
~~~

对 XOR 满足异色阈值的输入，返回 PID XOR 0x10000000；不满足则返回原始 PID。这里有明确的 EOR、阈值比较、CSEL、RET，因此**可确认原生条件式 PID AntiShiny 算法**，而非只因看到常量就推断其含义。

### 2.3 另一个同功能函数：0xE5D2B0

从 0xE5D2B0 到 0xE5D2C8 的另一组相同条件防闪逻辑同样使用 0x10000000。直接调用扫描暂未找到指向其入口的 B/BL；可能有间接调用/内联逻辑，不作推断。

### 2.4 异色调整：0xE5D21C

含异色 XOR 比较、PID 高 16 位替换（BFI），调用者存在 0x657198。符合保持/强制异色的 PID 修正方向，但应区分它与单纯的 Never 防闪函数。

### 2.5 排除的误报：0x2138DC0

第三个 EOR #0x10000000 命中在大量旋转、查表、EOR 与批量数据输出的计算循环中，并没有本次追踪中的 TID/PID getter/setter 引用。**不可将此地址当作锁闪函数。**

## 3. 同一原生生成函数中的三态分支

当前证据最强的区域为**0x657078–0x6571A0**：

| 原生 PC | 指令行为 | 直接证据 |
|---|---|---|
| 0x657078 | LDR X9,[X19,#0x20] | 读取 64 位内部状态/模式 |
| 0x65707C–0x657090 | 识别特殊值 0x4FFFFFFFF，按状态条件重设内部模式 | 特殊重设逻辑已存在，业务解释未确认 |
| 0x6570C4–0x6570CC | 与 0x1FFFFFFFF 比较，相等跳到 0x657140 | Never 行为分支 |
| 0x6570D0–0x6570D4 | 与内部 0x2FFFFFFFF 比较，相等跳到 0x657170 | Always 行为分支 |
| 0x6570D8–0x6570E0 | 与 0x3FFFFFFFF 比较，不相等跳过 | Random 行为分支 |
| 0x6570E4 | LDRB W8,[X19,#0x28] | 读取重掷次数上限/计数候选 |
| 0x657114–0x657124 | 读取 [X19+0x18]，更新生成值并 BL 0xE5D1E8 | 异色检查 |
| 0x657128–0x657138 | 成功退出，失败则按 [X19+0x28] 重掷 | Random roll loop |
| 0x657168 | BL 0xE5D200 | 调用条件式防闪 |
| 0x657198 | BL 0xE5D21C | 调用异色调整 |
| 0x65719C–0x6571A0 | MOV W8,W0；STR X8,[X19,#0x20] | 保存最终生成的 PID 候选 |

注意 0x657078 的模式输入与 0x6571A0 的输出复用同一个 [X19+0x20] **偏移**：这是由状态在生成过程中的不同阶段重复利用这一位置而产生的观察，不能把输入永远解释为 PKM.PID 或把输出永远当成 Rare 配置。

核心 Native 分发（将实际控制流整理成伪代码；不是逐句原始 C 源码）：

~~~c
uint64_t mode = state->mode_or_result_20;
if (mode == SPECIAL_4FFFFFFFF) {
    // 原生代码经随机条件改为 1FFFFFFFF 或 2FFFFFFFF；
    // 详细条件参见原始反汇编
}
if (mode == 0x1FFFFFFFF) {
    pid = generate_pid();
    pid = anti_shiny_if_needed(trainer_id, pid); // BL 0xE5D200
} else if (mode == 0x2FFFFFFFF) {
    pid = generate_pid();
    pid = adjust_shiny_pid(trainer_id, pid); // BL 0xE5D21C
} else if (mode == 0x3FFFFFFFF) {
    for (...) {
        pid = generate_pid();
        if (is_shiny(trainer_id, pid)) break; // BL 0xE5D1E8
        if (exceeded_roll_limit) break;
    }
}
state->result_pid_or_word_20 = pid;
~~~

伪代码说明流程而不声称精确恢复了所有调用实参、 RNG 初始状态及边界。

## 4. 重要的两套编码区别

| 层级 | Never | Always | Random | 来源 |
|---|---|---|---|---|
| EncountData.FlatBuffers 32 位 Rare | 0x1FFFFFFF | 0x2FFFFFFF | 0x3FFFFFFF | 原生遭遇表 + pkNX 解释 |
| Native 生成器内部 64 位模式 | 0x1FFFFFFFF | 0x2FFFFFFFF | 0x3FFFFFFFF | ELF 静态分支 |

**后续已发现原生转换指令**：0x656144–0x65614C 从原生描述对象 +0x68 读取 32 位模式，并计算 ((int64_t)(int32_t)raw << 4) | 0xF，产生 0x1FFFFFFFF / 0x2FFFFFFFF / 0x3FFFFFFFF。0x656170 写入局部状态，0x656298 进入 0x656F80，内部在 +0x20 读取它。原始 FlatBuffers 字段到该描述对象的赋值路径仍待复核，见第九节。

### 4.1 模式对应关系的证据等级

- 原生 0x1FFFFFFFF → AntiShiny：**CONFIRMED 静态控制流**。
- 原生 0x2FFFFFFFF → 0xE5D21C PID adjustment：**CONFIRMED 静态控制流**，倾向强制异色，但业务场景未知。
- 原生 0x3FFFFFFFF → 按 [X19+0x28] 重掷并检查异色：**CONFIRMED 静态控制流**。
- 描述对象 +0x68 的三态 32 位值 → 内部 64 位模式：**CONFIRMED 静态原生转换**，含输入、移位、OR、局部状态与 BL 传递。
- FlatBuffers 原始 EncountData.Rare → 描述结构 +0x68：**CANDIDATE**，转换原始数据的反序列化/复制函数待查。
- 蒂安希/超梦实际触发的模式和 PID 修改：**UNKNOWN，需运行时日志**。

## 5. PKM 现有对象上执行的防闪后写回

另一条真实原生控制流位于 0x55BD80–0x55BDD4：

1. 从同一 [X19+0x70] 指针读取 TID32：BL 0xE49D50。
2. 读取 PID：BL 0xE4DBE0。
3. 把两个 32 位值送给 BL 0xE5D1E8 检查异色。
4. 满足条件重新读取 TID/PID，调用 BL 0xE5D200 防闪。
5. 将返回 PID 传给 BL 0xE57350 setter（直接尾分支 0x55BDD4）。

这条链在指令上已连续闭合，确实实现**对已有 Pokémon 对象的条件式非闪纠正后写回**。但尚不知调用者触发它的业务场景（生成、赠礼、保存、系统清洗等），不可直接归因为 EX1/EX2。

## 6. 为什么这还不是「EX1/EX2 实机锁闪地址」？

旧有资源链已经静态闭合：

~~~text
trigger_sub_0119/0120
    Command53 btl_sub_119/120
    -> wild_btl_data_global.bin Battle.Field0
    -> id_sub119_01 / id_sub120_01
    -> pokemon_spawner_data_array.bin Spawner.Id
    -> sub_119_diancie / sub_120_mewtwo EncountDataId
    -> encount_data_array.bin Rare=0x1FFFFFFF
~~~

新原生代码链也可静态识别：

~~~text
mode 0x1FFFFFFFF / 0x2FFFFFFFF / 0x3FFFFFFFF
    -> native 0x6570C4..0x6571A0
    -> RNG/PID generated
    -> 0xE5D1E8 / 0xE5D200 / 0xE5D21C
~~~

已经确认描述对象 +0x68 → 内部模式变换 → 0x656F80 PID 生成 → Pokémon setter 的连续静态代码证据；仍缺原始 EncountData.Rare → 该描述对象的赋值来源、EX1/EX2 实际调度此函数的运行时执行日志。

## 7. 下一阶段精确任务

1. 已确认 0x656F80 函数入口从 0x656294 的 SP+0x18 接收状态；+0x20 用于内部三态模式并最终复用为 PID 结果，+0x28 是 roll 次数。需继续确认 Trainer ID/RNG 的上游来源。
2. 已找到 0x656060 描述对象 +0x68 的编码转换；下步追踪 FlatBuffers EncountData 字段 6 到 +0x68 的赋值来源并反查五组外部调用者。
3. 追 battle/spawner 入口到上述状态结构的设置操作，包括 0x4FFFFFFFF 特殊随机模式如何处理。
4. 用 SHA/Build ID 一致的实验环境断点记录 PC/LR、mode、raw Rare、TID32、PID、rollCount、分支与结果；分别对 Never / Always / Random 和 EX1 / EX2 做无修改的只读实测。
5. 根据实测建前后值对照（尤其两次防闪检查 fakeTID 与玩家训练家 ID），再确认游戏对不同场景如何使用辅助函数。

## 8. 复现命令

~~~powershell
python -m unittest discover -s tests -p test_za_rare_arm64.py -v
python scripts/Scan-ZA-Rare-ARM64.py
python -m pip install capstone==5.0.6
python scripts/Trace-ZA-Rare-Candidates.py --site-kind anti-shiny-xor --output docs/research/v2.0.2/za-rare-arm64-anti-shiny-xor-sites.md --before 0xC0 --after 0xC0
python scripts/Trace-ZA-Rare-Candidates.py --site-kind pid-shiny-callers --output docs/research/v2.0.2/za-pid-antishiny-caller-contexts.md --before 0x280 --after 0x120
python scripts/Trace-ZA-Rare-Candidates.py --site-kind native-state-builder-callers --output docs/research/v2.0.2/za-native-rare-builder-callers.md --before 0x200 --after 0x80
python scripts/Trace-ZA-PID-Accessor-Callers.py
~~~

配套：[[za-rare-arm64-runtime-chain-audit]]、[[za-pid-accessor-native-xrefs]]、[[za-legendary-shiny-lock-diancie-mewtwo-events]]。


## 9. 新实证：32 位模式转换、生成器入口与字段写回

### 9.1 0x656060 的真实转换指令

~~~asm
6560B4  MOV  X20,X0
6560DC  MOV  W9,#0xF
656144  LDP  W8,W10,[X20,#0x68]
656148  SXTW X8,W8
65614C  ORR  X8,X9,X8,LSL #4
656150  LDRB W9,[X21,#0x14]
656158  MOV  X9,#0x2FFFFFFFF
656160  CSEL X8,X8,X9,EQ
656170  STR  X8,[SP,#0x38]
65627C  ADD  W8,W23,#1
656280  STRB W8,[SP,#0x40]
656294  ADD  X0,SP,#0x18
656298  BL   #0x656F80
656FC0  MOV  X19,X0
657078  LDR  X9,[X19,#0x20]
~~~

这是经过 SHA-256 校验的真正游戏主程序反汇编。x20 由函数入参 x0 赋值，x20+0x68 是输入描述对象中的 32 位模式。ORR 计算的 64 位值为 ((signed32(raw) << 4) | 0xF)，所以 Never/Always/Random 的数值逐一精确匹配：

| 32 位源值 | 64 位计算值 | 原生处理 |
|---|---|---|
| 0x1FFFFFFF | 0x1FFFFFFFF | AntiShiny |
| 0x2FFFFFFF | 0x2FFFFFFFF | Shiny adjustment |
| 0x3FFFFFFF | 0x3FFFFFFFF | Random rolls |

X21+0x14 的条件检查后，还可能在 0x656160 覆盖内部模式为 0x2FFFFFFFF；不能认为每种情况下都会无条件沿用输入值。

从 SP+0x18 作为 state 起点，可验证 SP+0x38 即 state+0x20，恰是生成器的 0x657078 读取的模式。SP+0x40 即 state+0x28，在 0x6570E4、0x65712C 被作为随机重掷次数读取。因此上下游不仅有直接 BL，连栈内字段也闭合了。

### 9.2 0x653F24 的原始 Rare.Always 交叉验证

~~~asm
653F24  BL   #0x656060
653F2C  MOV  W9,#0x2FFFFFFF
653F34  LDR  W8,[X24,#0x68]
653F38  CMP  W8,W9
653F3C  B.EQ #0x654970
~~~

这里也读取同类型描述对象的 +0x68，并与原始 Rare.Always 32 位编码完全相同的常量比较。该指令与 0x656144 的输入/变换构成两个独立交叉证据。剩余问题是源 FlatBuffers 记录的字段 6 究竟通过哪一条反序列化/复制路径进入内存描述对象。

### 9.3 0xE3EB34 的生成器调用与 Pokémon 属性赋值

~~~asm
E3EB58  ADD X0,SP,#8
E3EB5C  BL  #0xBEF804
E3EB60  ADD X0,SP,#8
E3EB64  BL  #0x656F80
E3EB9C  BL  #0xE52EE0  ; TID/SID setter
E3EBA8  BL  #0xE57350  ; PID setter
E3EBB4  BL  #0xE52AA0  ; Species setter
E3EBC0  BL  #0xE56470  ; Form setter
E3EBE4  BL  #0xE56690  ; Nature setter
~~~

0xE3EB98 及 0xE3EBA4 从局部生成状态的字段读取值并交给属性 setter。这是“生成器输出 → Pokémon 个体字段写入”的原生静态调用证据，不是单纯函数距离接近。

### 9.4 五个原生描述状态生成函数的直接调用者

已在本版 ELF 中找到指向 0x656060 的全部五条直接 BL：

| Caller ELF VA | → | 观察 |
|---|---|---|
| 0x49CCA4 | 0x656060 | 上游持有原生对象和局部描述结构 |
| 0x5E6DC0 | 0x656060 | 原生结构与状态条件 |
| 0x653F24 | 0x656060 | 后续直接比较 +0x68 与 Rare.Always |
| 0x9CE758 | 0x656060 | 创建局部描述结构后调用 |
| 0x294F57C | 0x656060 | 数据准备与生成路径 |

参见 [完整调用者 Capstone 反汇编](za-native-rare-builder-callers.md) 和 [精确 BL 交叉引用](za-pid-accessor-callsite-xrefs.json)。

### 9.5 证据边界

- CONFIRMED 静态：+0x68 → 32/64 位模式转换 → 栈中状态 → 0x656F80 三态 PID 生成 → 原生判闪/防闪和属性写入。
- SUPPORTED 静态：此描述对象 +0x68 属于 Rare 模式字段，因为两处原生代码分别做数值转换与直接比较 Rare.Always 编码。
- UNKNOWN：FlatBuffers.EncountData.Rare 到描述对象字段的反序列化/内存复制链；EX1、EX2 对这些入口的实际运行时到达情况及 GDB 验证。
