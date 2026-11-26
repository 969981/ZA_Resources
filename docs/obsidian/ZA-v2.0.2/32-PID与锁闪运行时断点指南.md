---
title: ZA v2.0.2 PID、IV、训练家ID和rare分支定位指南
aliases: [ZA GDB锁闪断点, ZA PID主程序地址, ZA rare运行时]
tags: [ZA, ARM64, GDB, PID, IV, shiny, evidence]
version: "2.0.2"
status: 外部已发表函数线索-本仓库锁闪实现尚未独立验证
---
# rare → PID → 最终闪光状态：GDB 动态验证路线

> [!warning] 地址的来源与使用边界
> 本篇列出的具体 `main+RVA` 来自公开的 [pokeldn Z-A 2.0.2 静态/实机逆向说明](https://decryptu.github.io/pokeldn/za.html)，是**有来源的外部参考线索**；本次没有用用户的主机/模拟器实测这些 RVA，也**没有找到真正的 rare 分类分支/锁闪过滤函数**。必须先确认用户正在运行的 Build ID 一致，不能当作已经验证的本仓库定位结果。

## 一、明确版本和原始 main 身份

本仓库实际 `Unpack/v2.0.2/exefs/exefs-manifest.json` 记录：
- `main.elf` 大小 **66,579,944 bytes**；
- `main.elf SHA-256 = 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d`；
- Build ID 头 20 字节：`B1F12FD919EAE86AB8A978317677E64BCE443D1F`；
- `main.uncompressed.nso` 大小 66,577,712 bytes，另有专属 SHA-256。

这些身份数值可以证明仓库分析的是同一版本的 main，但**不能仅因为版本号都叫 2.0.2 就保证不同发行构建的 RVA 一致**。实际挂载前要核实 Build ID 和对应模块基址。

## 二、公开研究中可以直接当“候选断点”的实际函数

| 作用 | 外部公开 RVA | 与本次 rare 研究的关系 |
|---|---|---|
| 读取 PKM 物种编号 | `main+0xE49940` | 过滤、确认正在观察的目标是哪一个物种 |
| 读取 TID/SID 组合 | `main+0xE49D50` | 收集闪光 XOR 输入之一 |
| 读取 PID | `main+0xE4DBE0` | 取得 PID 的当前值 |
| 写入 PID | `main+0xE57350` | 优先追踪 PID 在何处被最终写入 |
| 读取形态 | `main+0xE4D190` | 防止把多形态事件混为同一模板 |
| 读取六项 IV | `main+0xE4BCF0..0xE4CB60` | 观察静态 -1/31 是否转成实际 0..31 |
| 写入六项 IV | `main+0xE54F90..0xE55E10` | IV 实际生成与覆盖调用链的候选 |
| 访问 Personal 学习表 | `main+0xE343A0` | 已知是学招式解锁相关；**不是** shiny 锁分支 |

这些函数是 PKM 的读取/写入接口，不是上游的 `encounter.rare` 解析逻辑。调用 PID setter 也不等于执行锁闪；可能发生在正常创建、交易、保存或加载时。必须查看调用者及对应遭遇配置，才能分类。

数据参考：[pokeldn 2.0.2 主程序偏移与 PKM 布局](https://decryptu.github.io/pokeldn/za.html)。

## 三、为什么最后一定要核对 PKM 结构

外部 2.0.2 研究给出的**解密且已恢复区块次序**的核心实体偏移：

| 核心数据偏移 | 长度 | 内容 |
|---|---:|---|
| `+0x08` | 2 | 物种编号 |
| `+0x0C` | 4 | TID/SID 合并值 |
| `+0x1C` | 4 | PID |
| `+0x20` | 1 | 性格 |
| `+0x24` | 2 | 形态 |
| `+0x72..0x79` | 8 | 四个技能编号，每个 u16 |
| `+0x8C` | 4 | 六项 5-bit IV 打包值 |
| `+0x148` | 1 | Party tail 中等级 |

**这些不是原始未解密 .pk9 的绝对文件偏移。** 内存访问对象 `accessor+0x10` 指向 0x148 字节 core，且 core 可能临时处于加密态、区块被重排；直接按未解密的内存地址读 `+0x1C` 可能取到无意义数据。建议先用 getter/解密后的结构确认，再比较最终回读。

## 四、四组最应该一起比较的事件

| 案例 | 原始 Encounter | rare 静态值 | 原始 Spawner |
|---|---|---|---|
| 已报告固定闪光的咩利羊任务 | `ect_a0102_w01_v01_z179_Qst074` | `0x2FFFFFFF` | `id_spn_a0102_w01_v01_Qst074` |
| 蒂安希支线 | `sub_119_diancie` | `0x1FFFFFFF` | `id_sub119_01` |
| 超梦支线 | `sub_120_mewtwo` | `0x1FFFFFFF` | `id_sub120_01` |
| 野生头目候选 | `ect_a0201_w01_v01_z460_Alpha` | `0x3FFFFFFF` | `id_spn_a0201_w01_v01_001_A` |

注意：`id_sub119_01` 有**三条真实的** `encountDataId` 引用：蒂安希（719、70 级），以及两条小碎钻（703、66 级）的伴随配置 `sub_119_melecie_01` / `sub_119_melecie_02`，三者 `rare=0x1FFFFFFF`。研究该支线时不能仅追踪主 Boss 忽略伴随实体；详见 [[31-rare分组与事件生成器对账]] 的完整候选 CSV。

## 五、断点顺序：先最终结果、再倒追 rare 的读取

建议在**独立测试存档、正确 Build ID** 下：

1. 先定位运行中的 `main` 实际模块基址；将其记为 `BASE`。**不得用文件的装载地址代替运行时实际地址**。
2. 选择触发一次具体事件（A/B/C/D），记录场景、剧情 flag、Encounter ID 与 Spawner ID。
3. 在 PID getter、PID setter 及物种 getter 设置断点；观察参数寄存器、返回寄存器和回溯栈，以便把实体生成对象与物种 ID 关联。
4. 捕获写入 PID 的实际调用者 `LR` 和上游返回链；比较咩利羊 `0x2`、剧情 `0x1`、普通野生 `0x3` 三种 **high nibble** 在**生成之前**的调用路径差异。
5. 进一步在 Encounter 表解码/加载器附近寻找读取 `rare` 的结构字段和位操作（逻辑右移 28 位/按掩码提取等**只是候选特征**），逐个确认真实寄存器和值。
6. 追踪真实的 `PID/TID/SID` 与可能的重抽/强制非闪/强制闪光操作，最后比较生成前后和保存后的实体。
7. 若找到差异的第一个 ARM64 分支，在相同 Build ID 下对三种值都走一遍；记录函数起点、分支偏移、寄存器、内存/反汇编截图、来源和复测次数。

## 六、GDB 只读调试模板

下面的指令只是如何对**已知的外部候选 RVA**进行调试；`$main` 必须由连接到当前模拟器/主机的调试器读取真实基址后赋值。切勿在不了解其用途时改写任意 Pokémon 的 PID 或存档。

```gdb
# 先在 GDB 中设置本次 main 模块的真实加载基址
# set $main = <actual_runtime_module_base>

x/6i $main+0xE49940
x/6i $main+0xE49D50
x/6i $main+0xE4DBE0
x/6i $main+0xE57350

# 仅在事件即将触发前加断点，避免高频路径过多命中
b *($main+0xE57350)

# 断点命中后
info registers x0 x1 x2 x3 x30 pc
x/12i $pc
bt 12
# 再与 eventId / spawnerId 对应记录人工核对
```

如果这些 RVA 的指令反汇编、调用约定或 Build ID 与外部来源不一致，应停止本方案并重新定位，不得把这段指令称为“已确认锁闪分支”。

## 七、记录表的字段和成功门槛

推荐新增的运行时日志字段：

```csv
gameVersion,buildId,encounterId,spawnerId,rareHex,case,mainBase,callerRva,pidGetterRva,pidSetterRva,trainerId32,pidBefore,pidAfter,ivBefore,ivAfter,shinyResult,branchRva,assemblyEvidence,replications,confidence
```

其中 `branchRva` 保持**空白**直到在同一 Build ID 下用三种 rare 类别实测证明。和 `rareRaw` 的静态对账行不同，只有真实读取/生成日志才可以从 E3（外键）升级为 E4（运行时链）；多个不同剧情状态和正反例复测才能达到 E5。

**这次已实现：** 从 1,966 条 Encounter 分组到 7 个剧情与特殊 case，再查真实 Spawner ID／同组候选；带版本来源的 PID/IV getter 和 setter 地址已作为外部参考记录。

**这次未实现：** 在本仓库的 `main.elf` 中独立恢复 rare 读取者、第一处分支及锁闪实际判定指令。不要向用户宣称已发现这些 `main+offset`。
