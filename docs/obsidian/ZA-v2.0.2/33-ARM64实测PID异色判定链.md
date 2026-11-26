---
title: ZA v2.0.2 ARM64 独立实测 PID 异色计算链
aliases: [Z-A 2.0.2 闪光判定汇编, ZA Shiny PID 0 1 2]
tags: [ZA, ARM64, shiny, PID, GDB, reverse-engineering]
version: "2.0.2"
status: ELF汇编已独立校验-rare上游与运行时未闭合
---
# Z-A v2.0.2：已经找到的 PID 异色计算与写回函数

> [!success] 与此前的差别
> 这次**实际在仓库的 v2.0.2 main.elf 二进制中扫描并解码**下列指令，而不再单纯照抄外部地址。已验证 ELF SHA-256、实际 BFBS 的 EncountData.rare 字段，以及到 PID Getter/Setter 的直接 BL/B。**但尚未证明 Encounter.rare 的值从哪一条上游调用链传入这些函数，也没有在主机上执行动态日志。**

源证据：[完整 AArch64 反汇编窗口](https://github.com/969981/ZA_Resources/blob/docs/za-v2.0.2-obsidian-extraction/docs/research/ZA-v2.0.2/rare-arm64/pid-shiny-function-windows.md) · [PID Getter/Setter 引用 CSV](https://github.com/969981/ZA_Resources/blob/docs/za-v2.0.2-obsidian-extraction/docs/research/ZA-v2.0.2/rare-arm64/pid-direct-callers.csv) · [SHA 验证清单](https://github.com/969981/ZA_Resources/blob/docs/za-v2.0.2-obsidian-extraction/docs/research/ZA-v2.0.2/rare-arm64/static-audit.json)。

## 1. ELF 版本证据

- 游戏：Pokémon Legends: Z-A v2.0.2。
- Build ID 头 20 字节：B1F12FD919EAE86AB8A978317677E64BCE443D1F。
- main.elf SHA-256：470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d。
- 实测 ARM64 .text RVA：0xE1D664–0x31605E0（36,974,460 字节）。
- 源 Encounter BFBS 真实字段：ik.fb.wild_pokemon.EncountData.rare，field ID=6，FlatBuffers vtable 偏移=0x10，类型 Int。**vtable 0x10 不等于内存里 rare 成员 RVA。**

## 2. 真正的异色判定：main+0xE5D1E8

实际反汇编片段：

~~~asm
main+0xE5D1E8: eor  w8, w1, w0
main+0xE5D1EC: and  w9, w8, #0xfff0
main+0xE5D1F0: eor  w8, w9, w8, lsr #16
main+0xE5D1F4: cmp  w8, #0x10
main+0xE5D1F8: cset w0, lo
main+0xE5D1FC: ret
~~~

结合调用者 main+0xE45FC0..0xE45FDC，可以确认 w0/w1 实际来自 **TID/SID 合并整数与 PID** 的 Getter；高低各 16 位的 XOR 决定是否小于 16。这个函数的返回 0/1 是 *PID 对当前训练家 ID 是否构成异色* 的布尔判断，不是 Encounter.rare 的 enum 返回。

简化计算：

~~~python
def is_shiny(trainer_id32, pid):
    x = trainer_id32 ^ pid
    return (((x & 0xFFF0) ^ (x >> 16)) < 16)
~~~

注意与普通定义的 16-bit Shiny XOR 小于 16 在逻辑上等价，但游戏这里用不同位运算完成。

## 3. PID 异色类别：main+0xE5D244

~~~asm
main+0xE5D244: eor  w8, w1, w0
main+0xE5D248: lsr  w9, w8, #16
main+0xE5D24C: and  w10, w8, #0xfff0
main+0xE5D250: cmp  w9, w8, uxth
main+0xE5D254: eor  w10, w10, w9
main+0xE5D258: cset w8, eq
main+0xE5D25C: cmp  w2, #0x22
main+0xE5D260: cset w9, eq
main+0xE5D264: orr  w9, w9, w3
main+0xE5D268: orr  w8, w9, w8
main+0xE5D26C: tst  w8, #1
main+0xE5D270: mov  w8, #1
main+0xE5D274: cinc w8, w8, ne
main+0xE5D278: cmp  w10, #0x10
main+0xE5D27C: csel w0, w8, wzr, lo
main+0xE5D280: ret
~~~

可以严格证明返回模式 **0（不符合异色阈值）**或 **1/2（符合异色阈值、按附加信息细分）**。其中 w2==0x22 及 w3 的额外条件来自调用者提供的版本/事件标志；**不能在没有更多场景证明时把 1/2 无条件对应某个外观类别**。

## 4. 状态调节：main+0xE46024

实测 main+0xE46024：
- 入口 w1 作为目标模式，存入 w20；
- main+0xE4605C：and w9,w20,#0xff；
- main+0xE46060：cmp w9,#2；不属于 0..2 的模式分支不进入通常处理；
- main+0xE46070、main+0xE4607C：分别取 TID/SID 与 PID；
- main+0xE460A8：BL main+0xE5D244 读取当前异色类别；
- main+0xE460B0：cmp w8,w20,uxtb 比较当前类别与目标；
- 不相等时：main+0xE460EC BL main+0xE5D284 调整 PID；
- main+0xE46108：B main+0xE57350，通过**尾调用**进入 PID Setter。

另一个相关函数 main+0xE45F7C 在 main+0xE45FDC 调用异色判断 main+0xE5D1E8，在部分分支 main+0xE4600C 调用 main+0xE5D21C 调整 PID，再通过 main+0xE46020 的尾调用进入 setter。

这两段已经形成独立的**PID/异色状态读取、比较、修正、写回**下游链。它们的目标模式**还没有证明来自 Encounter.rare**。

## 5. 为什么早期统计只有一处 PID setter BL？

AArch64 编译器用两种指令调用同一个函数：
- BL：保存返回地址，作为常规调用；
- B：无链接跳转，可用于尾调用。

本轮对 main+0xE57350 确认 **1 处 BL（main+0xE3EBA8）**与 **2 处 B 尾调用（main+0xE46020、main+0xE46108）**。只查 BL 会漏掉真实的 PID 修正写入分支。

此外，main+0xE46024 被两段包装器直接 B 跳转：
- main+0x2D7008C；
- main+0x2D755E4。

main+0xE45F7C 对应包装器：
- main+0x2D70084；
- main+0x2D755D4。

包装器从对象 +0x50 取真正的 PokemonParam 指针，再转发到计算函数。这些**只是接口入口**，并没有确认最终哪个 Encounter 的生成器进行了间接 BLR 调用。

## 6. 后续必须寻找的 rare → mode 交接点

从 actual BFBS 可以确认 field ID=6 / vtable slot=0x10，但尚未定位主程序哪条指令在读取它。下一阶段按以下顺序：

1. 在同 Build ID 的生成器加载过程中追踪 Encounter 的 EncountData 对象及其 rare 字段；证明寄存器实际取到 0x1FFFFFFF / 0x2FFFFFFF / 0x3FFFFFFF。
2. 找到将该值**解码成 0/1/2 模式或 RNG 策略**的第一处分支，记录 main+RVA 和反汇编前后 20 条指令。
3. 追踪其后是否调用上述 main+0xE45F7C / main+0xE46024，还是通过另一条创建路径直接设置 PID。
4. 用 Qst074 咩利羊、蒂安希、超梦与普通野生头目形成 0x2/0x1/0x3 的样本对照。**同一个 spawner 还可能包含伴随小碎钻**，需核对实体物种。
5. 记录 PID/训练家 ID、真实 XOR、最终形态/IV/闪光状态与存档后结果；任何入口不一致时不得把全物种统一标为锁闪。

当前**没有**完成 step 1–4 的动态 E4/E5 验证。路径与研究标准见 [[31-rare分组与事件生成器对账]]、[[32-PID与锁闪运行时断点指南]]。可使用仓库中的 GDB 采集模板 scripts/gdb/za_v202_pid_shiny_trace.gdb。

## 7. 复现扫描

~~~bash
python -m pip install capstone==5.0.6
python scripts/Trace-ZA-Rare-ARM64.py --repo .
~~~

扫描器使用 SHA-256 对账，不更改 ELF，输出 docs/research/ZA-v2.0.2/rare-arm64/ 下的 CSV、JSON、ASM 窗口。GitHub Actions 工作流 za-rare-arm64-audit.yml 会自动执行并发布结果。**没有独立复核的 RVA 不会被标为已确定的 rare 锁闪分支**。
