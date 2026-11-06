---
title: Z-A v2.0.2 原生 PID 访问函数交叉引用与锁闪候选路径
tags: [pokemon/za, research/arm64, flatbuffers, pid, shiny-lock]
version: v2.0.2
updated: 2026-11-06
status: NATIVE_PID_HELPERS_STATIC_CONFIRMED_RARE_CONSUMER_UNKNOWN
---

# Z-A v2.0.2：通过 PID getter/setter 反查锁闪路径

> [!IMPORTANT] 证据等级
> 已从本仓库真实、经 SHA-256 校验的 main.elf 解码对 Pokémon 字段访问器的直接 ARM64 B/BL 分支。调用指令与分支目标是真实数据。初轮仅找到 getter/setter 静态调用者；**后续已在游戏原生指令中证实判闪 0xE5D1E8、条件防闪 0xE5D200 和三态 PID 生成分发 0x6570C4–0x6571A0**。参见 [最新研究](za-native-shiny-generator-pid-branch.md)。仍未闭合 Rare 原始字段消费、EX1/EX2 具体动态入口和 GDB 校验。

## 一、来源与可复现性

- 游戏：Pokémon Legends: Z-A v2.0.2
- NSO Build ID（本仓库 manifest）：b1f12fd919eae86ab8a978317677e64bce443d1f000000000000000000000000
- 主程序 ELF SHA256：470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d
- 字段 getter/setter 外部逆向来源：[pokeldn Z-A 2.0.2](https://decryptu.github.io/pokeldn/za.html)
- [本仓库直接 B/BL 指令和分支目标完整 JSON](za-pid-accessor-callsite-xrefs.json)
- [扫描脚本](../../../scripts/Trace-ZA-PID-Accessor-Callers.py)
- [本轮 5 项合成测试与真实 ELF 扫描通过的 Actions 记录](https://github.com/969981/ZA_Resources/actions/runs/42204522442)

注意这些 PC 是 ELF 内的静态虚拟地址；作为运行时 main+offset 使用之前，必须通过 NSO 映射和运行时 GDB 确认。

## 二、目标函数和真实直接调用数

| 字段 | 目标 VA | 原生 B/BL 数 |
|---|---|---:|
| Species getter | 0xE49940 | 98 |
| TID/SID getter | 0xE49D50 | 15 |
| PID getter | 0xE4DBE0 | 11 |
| PID setter | 0xE57350 | 4 |
| TID/SID setter | 0xE52EE0 | 2 |
| Species setter | 0xE52AA0 | 2 |
| Exp setter | 0xE53100 | 2 |
| Form setter | 0xE56470 | 3 |
| Nature setter | 0xE56690 | 2 |
| Ability setter | 0xE535B0 | 2 |

合计 141 条。这些均从匹配 SHA 的主程序指令中按 B/BL 的 26 位相对位移计算目标后精确匹配；不包含 BLR 间接调用、虚表调用或不直接命中的包装器。

## 三、多字段写入：0xE3EB9C–0xE3EDE0

| 调用点 PC | 原生指令字 | 目标 VA | 关联字段 |
|---|---|---|---|
| 0xE3EB9C | 0x940050D1 | 0xE52EE0 | TID/SID |
| 0xE3EBA8 | 0x940061EA | 0xE57350 | PID |
| 0xE3EBB4 | 0x94004FBB | 0xE52AA0 | 种族 |
| 0xE3EBC0 | 0x94005E2C | 0xE56470 | 形态 |
| 0xE3EBE4 | 0x94005EAB | 0xE56690 | 性格 |
| 0xE3ED70 | 0x94005210 | 0xE535B0 | 特性 |
| 0xE3EDE0 | 0x940050C8 | 0xE53100 | 经验 |

这段很像个体数据创建、复制或初始化路径；**只能作为候选**。下一步追 PID 的参数来源、同一对象 x0 指针的保持方式、调用方是否为 Spawner/Encounter 消费者，而不能直接命名「锁闪函数」。

## 四、TID/SID 与 PID 成对读取的更强候选

### 4.1 静态 PC 0x55BD84–0x55BDD4

| PC | 已证实的直接分支 |
|---|---|
| 0x55BD84 | BL TID/SID getter |
| 0x55BD90 | BL PID getter |
| 0x55BDA8 | BL TID/SID getter |
| 0x55BDB4 | BL PID getter |
| 0x55BDD4 | B PID setter |

这组包含两轮紧邻的 TID/PID getter 和一次向 PID setter 的尾分支。可能涉及 Shiny XOR、PID 调整，也可能是其他数据处理。必须恢复函数边界、位移/EOR/比较与执行条件后才能判定。

### 4.2 静态 PC 0xE45FC4–0xE46108

| PC | 已证实的直接分支 |
|---|---|
| 0xE45FC4 | BL TID/SID getter |
| 0xE45FD0 | BL PID getter |
| 0xE45FF4 | BL TID/SID getter |
| 0xE46000 | BL PID getter |
| 0xE46020 | B PID setter |
| 0xE46070 | BL TID/SID getter |
| 0xE4607C | BL PID getter |
| 0xE460D0 | BL TID/SID getter |
| 0xE460DC | BL PID getter |
| 0xE46108 | B PID setter |

其余可对照读取点还有 0xF478/0xF484、0xB8DCC4/0xB8DCD0、0xB8DD18/0xB8DD24、0xC32CD4/0xC32CE0。

上述成对出现代表「应该重点检查的候选」，不是已经确认的同一函数数据流。

## 五、需要完成的连续证据链

1. 手工反汇编 0x55BD80 和 0xE45FC0 两组的前后控制流，识别不同函数边界及 x0/x1 参数。优先核对 PID 与 TID/SID 是否从相同 PKM 对象取得。
2. 查看是否执行 TID、SID、PID 高低 16 位 XOR，是否存在游戏自己的阈值比较与 PID 改写；不要把旧世代算法硬套到 Z-A。
3. 将实际读取 Rare 的 FlatBuffers 消费者/高位枚举解析，与 Spawner 的具体 Encounters[].EncountDataId 关联。
4. 向上证明 btl_sub_119 / btl_sub_120 的运行时入口真的调用该数据读取与实例生成函数。
5. 在本版本同一 Build ID 下只读断点复核 PC/LR、Rare 原值、PID Before/After、TID/SID、RNG、指令分支；对 Never/Always/Random 样本各做对照。
6. 只有实机日志闭合执行路径后，才可标注 CONFIRMED main+offset 或具体游戏原生锁闪判断地址。

## 六、复现

~~~powershell
python -m unittest discover -s tests -p test_za_pid_accessor_callers.py -v
python scripts/Trace-ZA-PID-Accessor-Callers.py --span 0x800 --limit 70
~~~

本阶段不会修改 ROM、打补丁、修改存档或虚构可用地址。

关联：[[za-rare-arm64-runtime-chain-audit]]、[[za-legendary-shiny-lock-diancie-mewtwo-events]]。

## 七、后续已查实的调用链（2026-11-06）

原生 `0x55BD80–0x55BDD4` 的确在同一对象指针 `[x19+0x70]` 下完成 TID/PID 读取 → `BL 0xE5D1E8` 异色判定 → 必要时 `BL 0xE5D200` 条件防闪 → `B 0xE57350` PID setter。因此此前「可能是 Shiny XOR」现在可升级为**静态确认**。

此外 `0x6570C4–0x6571A0` 直接比较 64 位内部三态模式并分别进入 `0xE5D200`、`0xE5D21C` 或随机判定和重掷逻辑。详见 [[za-native-shiny-generator-pid-branch]]、[Capstone 完整上下文](za-pid-antishiny-caller-contexts.md)。尚不能将这段地址标注为 EX1/EX2 已执行的运行时偏移。
