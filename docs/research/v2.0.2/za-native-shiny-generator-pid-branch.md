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

**目前仅确认两套编码呈现对应的行为与数值序列，不确认实际转换函数或字段消费者。** 禁止直接认为原始 0x1FFFFFFF 会在内存里原样以 64 位出现；要追溯所用字段、映射关系、调用参数。

### 4.1 模式对应关系的证据等级

- 原生 0x1FFFFFFFF → AntiShiny：**CONFIRMED 静态控制流**。
- 原生 0x2FFFFFFFF → 0xE5D21C PID adjustment：**CONFIRMED 静态控制流**，倾向强制异色，但业务场景未知。
- 原生 0x3FFFFFFFF → 按 [X19+0x28] 重掷并检查异色：**CONFIRMED 静态控制流**。
- FlatBuffers Rare 32 位三种值 → 生成器内部 64 位模式：**CANDIDATE，尚未定位转换函数**。
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

但**两链之间的 EncountData.Rare 消费→内部 mode 构造→实际实例化入口还没有闭合**；这一连接最值得继续。

## 7. 下一阶段精确任务

1. 在 0x6570xx 的上游真实调用者中追 x19 的建立点；确认 [x19+0x18] 的身份（trainer ID 候选）、[x19+0x20] 输入时的原生模式，以及 [x19+0x28] roll 次数。
2. 对照 FlatBuffers EncountData.Rare 的字段号 6 与实际 getter/反序列化代码。搜索高位指示/变换，而非只搜低 32 位常量。
3. 追 battle/spawner 入口到上述状态结构的设置操作，包括 0x4FFFFFFFF 特殊随机模式如何处理。
4. 用 SHA/Build ID 一致的实验环境断点记录 PC/LR、mode、raw Rare、TID32、PID、rollCount、分支与结果；分别对 Never / Always / Random 和 EX1 / EX2 做无修改的只读实测。
5. 根据实测建前后值对照（尤其两次防闪检查 fakeTID 与玩家训练家 ID），再确认游戏对不同场景如何使用辅助函数。

## 8. 复现命令

~~~powershell
python -m unittest discover -s tests -p test_za_rare_arm64.py -v
python scripts/Scan-ZA-Rare-ARM64.py
python -m pip install capstone==5.0.6
python scripts/Trace-ZA-Rare-Candidates.py --site-kind anti-shiny-xor --output docs/research/v2.0.2/za-rare-arm64-anti-shiny-xor-sites.md --before 0xC0 --after 0xC0
python scripts/Trace-ZA-Rare-Candidates.py --site-kind pid-shiny-callers --output docs/research/v2.0.2/za-pid-antishiny-caller-contexts.md --before 0x120 --after 0x120
python scripts/Trace-ZA-PID-Accessor-Callers.py
~~~

配套：[[za-rare-arm64-runtime-chain-audit]]、[[za-pid-accessor-native-xrefs]]、[[za-legendary-shiny-lock-diancie-mewtwo-events]]。
