---
title: ZA v2.0.2 联机交换限制 — 原生静态深挖与验证边界
aliases:
  - ZA LinkTrade HeldItem 静态分析
  - Mega 石及宝珠交换限制地址
tags: [Pokemon/ZA, reverse-engineering, ItemData, LinkTrade, AArch64]
status: VERIFIED_STATIC_PENDING_RUNTIME
updated: 2026-11-06
---

# ZA v2.0.2 联机交换限制：原生静态深挖与验证边界

> [!abstract] 阶段性结论
> **全部 535 条道具已经归档为 12 个真实的 ItemType×Pocket 组合；92 种 Mega 石全部 `ItemType=7, Pocket=7, SlotMaxNum=1`，红蓝宝珠 `ItemType=7, Pocket=2, SlotMaxNum=999`。原生 ELF 查到了交易相关字符串、少量确切的指令引用，及 CommandCancelTrade 类型信息引用的原生代码；但当前仍没有在实际 Link Trade 运行中证实读取 HeldItem 后拒绝 Mega 石/宝珠的首个条件分支。**

## 1. 数据与验证版本

- 游戏：`Pokémon Legends: Z-A v2.0.2`，不混用其他版本相同 `main+offset`。
- 主表：`Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/world/exl/item_data/item_data/item_data.bin`，50,372 bytes、535 条、50 个原生字段。
- 本项目源码：[[za-itemtype-pocket-complete|全部 535 条分类名单]]；[[za-items-real-data-audit|原始道具主表实际解析]]。
- ExeFS：`Unpack/v2.0.2/exefs/main/main.elf`，66,579,944 bytes，SHA-256 `470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d`。
- [ItemData CI 已通过](https://github.com/969981/ZA_Resources/actions/runs/42175498736)、[第一次交易静态扫描已通过](https://github.com/969981/ZA_Resources/actions/runs/42175858056)、[深入代码反汇编与常量审核已通过](https://github.com/969981/ZA_Resources/actions/runs/42221876645)。

## 2. 关键字段与控制组

| 控制道具 | ID | ItemType | Pocket | SlotMaxNum | CanNotHold |
|---|---:|---:|---:|---:|---|
| 金属膜 | 233 | 7 | 2 | 999 | false |
| 吃剩的东西 | 234 | 7 | 2 | 999 | false |
| 朱红色宝珠 | 534 | 7 | 2 | 999 | false |
| 靛蓝色宝珠 | 535 | 7 | 2 | 999 | false |
| 耿鬼进化石 | 656 | 7 | 7 | 1 | false |
| 92 种 Mega 石 | 多个 | 7 | 7 | 1 | false |

- `ItemType=7`：同类型含普通携带物、原始回归宝珠和 Mega 石，因此**不能直接用 `ItemType==7` 单独解释禁交易**。
- `Pocket=7`：能识别这 92 种 Mega 石，但**不能单独解释红蓝宝珠**，因为它们实际属于 Pocket 2。
- `SlotMaxNum=1`：与 Mega 石的单件上限一致，**但还没有证据表明 Link Trade 会查询这个字段**。
- `CanNotHold=false`：以上所有样本均一致，不代表“可以送出”，不具有区分力。
- 如果实机确认红蓝宝珠也被阻止，就必须查明与一般 Pocket 2 携带物不同的其他属性、物品 ID/名单、库存状态或专门业务检查。

## 3. 已确认：CommandCancelTrade 静态代码区域

第一次 ELF 扫描找到 `CommandCancelTrade` 类型字符串 VA = **0x3252D03**，指令 `main+0x2DC4154` 的 `ADRP + ADD` 引用此字符串。第二轮用 Capstone 独立反汇编上下文，确认附近有真实指令：

~~~asm
0x2DC413C: sub  sp, sp, #0x50
0x2DC4140: stp  x29, x30, [sp, #0x20]
0x2DC414C: add  x29, sp, #0x20
0x2DC4154: adrp x0, #0x3252000
0x2DC4158: add  x0, x0, #0xd03
0x2DC4164: bl   #0xc360c0
0x2DC4174: bl   #0x96129c
0x2DC417C: cmp  w8, #0x100
0x2DC4180: b.hs #0x2dc41a0
~~~

**确认的仅仅是这里存在原生函数样式代码、调用以及 `CommandCancelTrade` 类型名引用。** `0x2DC413C` 是有具体序言的静态候选函数边界，**不是**已验证的交换携带物许可函数。`CommandConfirmTrade` 在 `.rodata` 中也有字符串（VA 0x32B5599），本轮未找到能够把该字符串直接关联到禁止道具检查的可靠 xref。

## 4. 已确认：交易界面资源的原生引用

| 指令 PC | 指向字符串 | 研究意义 |
|---|---|---|
| `main+0x2D304E0` | `net_topmenu_trade_10_06` | 菜单/页面上下文 |
| `main+0x2D315B4` | `net_topmenu_trade_10_07` | 菜单/页面上下文 |
| `main+0x2DC4154` | `CommandCancelTrade` 类型名 | 命令类型元数据上下文 |

`main+0x2D31588` 观察到 `bl #0xAC19E4` 和随后的 `tbz w0,#0`，但这是 UI 关联代码附近的一条普通条件检查；没有包含 HeldItem、物品分类/ ID 及正负对照，不得认定为物品禁交易分支。

## 5. 重要反证：534/535 和 656/657 常量不是自动成立的交易黑名单

在 `main.elf` `.rodata` 中，原生数据扫描发现：

| 位置（数据 VA） | 连续 32 位数字 | 周围情况 |
|---|---|---|
| `0x3358434` | 534, 535 | 邻近包含 519~573 大量历史道具 ID，以及 TM/树果编号 |
| `0x33598E4` | 656, 657 | 邻近有 29、30、32、各种球、回复物、TM 编号 |
| `0x335A708` | 656, 657 | 邻近大量历史石、形态、其他道具 ID |

该数据与道具 ID 列表有关，但**不是只包含受限物品的短名单**。在它们相同 **4 KB 页**中发现一些 ARM64 `ADRP`，然而需要区分**引用页基址**与**引用数组中具体元素**：

| 指令 PC | ADD 得到的地址 | 含 534/535 或 656/657 的位置 | 判断 |
|---|---|---|---|
| `main+0x218B14C` | `0x3358060` | `0x3358434` | **不相同** |
| `main+0x2196320` | `0x335A524` | `0x335A708` | **不相同** |
| `main+0x21963DC` | `0x335929C` | `0x33598E4` | **不相同** |

第二、三行的附近原生汇编还包含：

~~~asm
mov    w26, #0x4a2
mov    w25, #0x28
ldr    w28, [x24, w27, sxtw #2]
umaddl x8, w28, w25, x22
~~~

可确认的是**索引数组读取、0x28 字节步长和动态乘加计算**；附近的循环与比较呈现二分式检索特征，更接近通用查找/索引数据，具体数据结构仍待验证。**不能把这些函数说成“拿 656/657 来判定能不能交易”。**

## 6. 审计文件（永久留在 Git，非仅 Actions）

- [完整 535 条数据分类](za-itemtype-pocket-complete.md)
- [Trade string 符号候选 TSV](data/za-v2.0.2-trade-elf-strings.tsv)
- [Trade ELF 5 条精确引用](data/za-v2.0.2-trade-elf-xrefs.tsv)
- [Pointer/RELA 25 条数据引用](data/trade-rela-pointer-sites.tsv)
- [深层 37 条目标字符串](data/trade-target-strings.tsv)
- [深层 3 条目标静态代码引用](data/trade-code-xrefs-deep.tsv)
- [3 组道具 ID 数据位置](data/item-id-adjacency.tsv)
- [243 条 ID 上下文（含表头）](data/item-id-table-neighborhoods.tsv)
- [24 条地址页关联](data/item-id-table-page-references.tsv)
- [静态反汇编关键指令](data/trade-candidate-disasm-selected.tsv)
- [静态候选分支与调用](data/trade-candidate-branchcalls.tsv)

> [!warning] 数据分类口径
> 深层“3 条代码引用”是从**37 条重点字符串**中筛出的结果；第一次“5 条代码引用”是从 **68 条较宽关键词字符串**中筛出的结果，两轮筛选口径不同，并非数据自相矛盾。25 个指针/重定位结果是链接元数据，不保证都是可执行消费者；24 条 ADRP 同页访问也**不等于** 24 条对物品 ID 的代码引用。

## 7. 可实际操作的 Link Trade / GDB 验证路线

任天堂官方的操作顺序是：联机配对后 **选择 Pokémon → Offer up → 看到对方 Pokémon → Trade it 确认**。资料见 [Nintendo Support: How to Start a Multiplayer Game](https://en-americas-support.nintendo.com/app/answers/detail/a_id/68627/)。请将阶段性日志与这些 UI 阶段对齐。

统一条件：同一个 v2.0.2 **BuildID**、同一个 Pokémon、同一队伍和相同物品拥有状态下测试：

| 组 | HeldItem 目标 ID | 目的 |
|---|---:|---|
| A | 0 / 无 | Pokémon 自身资格基线 |
| B | 233 金属膜 | 正常可交换且触发通信进化的携带物对照 |
| C | 234 吃剩的东西 | 普通非进化携带物对照 |
| D | 656 耿鬼进化石 | Mega 石单件/口袋限制对照 |
| E | 534 朱红色宝珠 | 专属物品，同 Pocket 2 |
| F | 535 靛蓝色宝珠 | 专属物品，同 Pocket 2 |

记录：`buildId,mainBase,itemId,pokemonSelected,offerUpAllowed,tradeItAllowed,heldBefore,heldAfter,bagBefore,bagAfter,errorMessage,breakPc,registers,lr,branchTarget`。交换失败时要区分**Pokémon 不可选**、**可送出但无法双方确认**、**Pokémon 交换成功但物品返回**三种行为；它们的调用链不必相同。

### 推荐验证次序（只读）

1. 用已验证静态候选处的断点确认交易页面或取消命令是否真正执行，严禁把仅触发断点就当成禁交易证据。
2. 从被选 Pokémon 的运行时对象追踪 **HeldItem 的实际字段与访问地址**；应先用正常道具/更换道具确认该字段的大小与偏移，不猜 16/32 位或结构体偏移。
3. 在 **B/C 与 D/E/F** 控制组对同一读取调用执行只读 watchpoint/backtrace；保留第一个出现不同条件跳转的 PC。
4. 复核两侧来源：本机过滤、数据序列化/清除、对方库存、确认/网络同步、回滚；不能把网络失败直接归因为服务器拦截。
5. 在相同 BuildID 下复现至少两次，并保存原始指令、寄存器与 `main+offset` 之后才能将此地址由 `CANDIDATE` 升级为 `CONFIRMED`。

### 静态分析复现

~~~bash
python scripts/Probe-ZA-Trade-ELF.py --repo . --output .za-work/trade-native
python scripts/Probe-ZA-Trade-Native-Deep.py --repo . --output .za-work/trade-native-deep
python scripts/Probe-ZA-ItemID-Table-Xrefs.py
python -m pip install capstone==5.0.6
python scripts/Disassemble-ZA-Trade-Sites.py
~~~

### 当前事实边界

- **CONFIRMED**：原始 ItemData 对照、535 条道具分类、68 个字符串、5 条初始代码引用、3 条深入代码引用、25 个指针/重定位数据、3 个 ID 邻接样本、24 条同页 ADRP 及 Capstone 实测代码窗口。
- **CANDIDATE**：`main+0x2DC413C` 及附近属于交易命令类型处理相关函数；`0x2196320/0x21963DC` 处执行通用数据索引查找。
- **UNKNOWN**：真正的 Link Trade `HeldItem` 拒绝函数、首次失败分支、是否查询 Pocket/SlotMaxNum/ItemID、红蓝宝珠与 Mega 石是否共用校验代码。

**当前不能给出被实机验证为“限制交换函数”的准确 `main+offset`；静态代码候选与运行时条件分支必须分开记录。**
