---
title: ZA v2.0.2 联机交换原生 ELF 静态候选
aliases: [ZA Trade native 字符串与地址]
tags: [Pokemon/ZA, LinkTrade, AArch64, ELF, v2.0.2]
status: CONFIRMED_STRINGS_AND_XREFS_RUNTIME_FUNCTION_UNKNOWN
updated: 2026-11-06
---

# ZA v2.0.2 联机交换：main.elf 静态候选和地址

> [!abstract] 当前真实进展
> 在 GitHub Actions [成功运行 #42175858056](https://github.com/969981/ZA_Resources/actions/runs/42175858056) 中，读取仓库 **66,579,944 bytes** 的原生 `main.elf`，通过已校验的 ELF64/AArch64 地址映射，取得 **68 个符合交易/交换/携带关键词的只读 ASCII 字符串**和 **5 个精确 ADRP+ADD 指令引用**。**没有通过运行时证据确认任何一个是 Mega 石或宝珠的限制函数。**

关联：[[za-items-real-data-audit]]、[[za-mega-stone-orb-trade-restrictions]]。

## 可核对的永久数据

- [68 条字符串完整证据 TSV](data/za-v2.0.2-trade-elf-strings.tsv)
- [5 条 AArch64 精确引用 TSV](data/za-v2.0.2-trade-elf-xrefs.tsv)
- [静态扫描 Python 脚本](../../../scripts/Probe-ZA-Trade-ELF.py)
- [GitHub Actions 工作流](../../../.github/workflows/za-trade-native-probe.yml)
- [完整 Actions 日志与 14 天 Artifact](https://github.com/969981/ZA_Resources/actions/runs/42175858056)
- ELF 固定路径：`Unpack/v2.0.2/exefs/main/main.elf`
- 原始 SHA-256：`470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d`

## 1. 重要交易字符串（这里的地址是 **数据地址**）

| 字符串 | ELF 虚拟地址 | 研判 |
|---|---|---|
| `TradeMatchingPage` | `0x31ADC1D` | 交易匹配页面关联名 |
| `TradeMatchingControlView` | `0x321B81B` | 匹配控件关联名 |
| `TradeMatchingTextView` | `0x32BF728` | 匹配文本 UI 关联名 |
| `WaitReadyToTradeCoroutine` | `0x322629F` | 可能是交易准备/等待状态流程 |
| `BoxExchange` | `0x320FFAF` | 箱子交换关联名 |
| `BoxExchangePresenter` | `0x3230546` | 交换 UI Presenter |
| `PartnerExchangeAction` | `0x31A7FED` | 伙伴交换动作关联名 |
| `net_trade` | `0x31FA6DF` | 网络交易资源或模块名 |
| `/trade_offer` | `0x325CED8` | 交易 offer 字符串 |
| `/trade_reset` | `0x32BEFB9` | 交易 reset 字符串 |
| `trade_my_mons_%s` | `0x31D9982` | 我方交易预览资源 |
| `trade_opp_mons_%s` | `0x31D9993` | 对方交易预览资源 |
| `holdItem` | `0x32A908E` | 携带物成员或文本标识（**不是交易判定函数**） |
| `CommandConfirmTrade` | `0x32B5599` | 匿名命名空间中的交易确认命令类型信息 |
| `CommandCancelTrade` | `0x3252D03` | 匿名命名空间中的交易取消命令类型信息 |
| `gfa::network::trade::SyncSaveClient::State` | `0x3247F3B`、`0x3248036` 所在完整字符串 | 原生网络保存同步类型信息 |

**注意：** 所有字符串均是原始 ELF 中 `.rodata` 的 ASCII 字节匹配。没有符号名、类名上下文或指令引用时，**不能将这一数据地址直接当成函数 PC**。

## 2. 真正观察到的 5 条指令引用

| AArch64 指令 PC | 目标字符串 VA | 对应内容 | 证据等级 |
|---|---|---|---|
| `main+0x294F97C` | `0x32049CB` | `ik_message/dat/JPN/common/trade_demo.dat` | 字符串 xref |
| `main+0x294F9B4` | `0x32465A4` | `ik_demo/sd/sd9130_trade/sd9130_trade.trtml` | 字符串 xref |
| `main+0x2D304E0` | `0x31CF646` | `net_topmenu_trade_10_06` | UI 资源名 xref |
| `main+0x2D315B4` | `0x31DA20E` | `net_topmenu_trade_10_07` | UI 资源名 xref |
| `main+0x2DC4154` | `0x3252D03` | `CommandCancelTrade` 类型信息 | 类型名 xref |

5 条均经过 **AArch64 ADRP + ADD** 计算，严格匹配了目标数据地址；**没有一条可以单凭静态字符串引用认定为道具禁止转移判断**。

### 优先级排序

1. **交易 UI/控制流**：`TradeMatchingPage`、`TradeMatchingControlView`、`WaitReadyToTradeCoroutine`；优先寻找页面切换及“提交交换物”的调用方。
2. **确认/取消命令**：`CommandConfirmTrade`、`CommandCancelTrade`；检查命令分派、对象生命期与交易资格判断发生的位置。
3. **交换双方数据**：`BoxExchange`、`trade_my_mons_%s`、`trade_opp_mons_%s`、`holdItem`，对照物品 ID 如何在选择与交换确认之前被读取。
4. **P2P 状态**：`gfa::network::trade::SyncSaveClient::State`。先查保存/同步，再判断是否存在服务器或本地的二次检查。
5. **低优先级误报**：TLS/SSL 的 `key_exchange`、`exchange_rate` 不是 Pokémon 联机交换校验。

## 3. 现在无法支持的断言

- `main+0x2D304E0` 是“检查是否能交易 Mega 石的函数”：**UNKNOWN**，这里只知道它引用了 UI 资源名。
- `CommandConfirmTrade` 一定执行持有物黑名单判断：**UNKNOWN**。
- 由于 Mega 石 `Pocket=7` 就一定被禁交易：**UNKNOWN**；红蓝宝珠 `Pocket=2`，不能用同一条件解释。
- 红蓝宝珠一定走同一条禁止交易的条件分支：**UNKNOWN**。
- 任何本次命中的指令 PC 已经过 GDB 原生断点确认：**FALSE**，本轮仅做离线静态扫描。

## 4. 下一步：最小可证实的 GDB 对照

建议在相同 v2.0.2 BuildID、同一只可交换 Pokémon、相同网络/队伍状态下，分组比较：

1. 不带道具；
2. 携带金属膜（Id `233`）；
3. 携带耿鬼进化石（Id `656`）；
4. 携带朱红色宝珠（Id `534`）；
5. 携带靛蓝色宝珠（Id `535`）。

记录每组 **列表是否可选 → 是否允许 Offer up → 是否允许双方确认 → 保存/返还持有物**；这些分界决定应该追 UI、物品序列化、库存保护还是通信提交阶段。

将目标的 `HeldItem` 读取和携带物 ID 送入判断链，比较正常/受限两组执行的同一基础块及返回值。只有找到**同一 PC 在相同条件下出现可重复且因道具不同而变化的判断**，才能写为“已定位真实限制函数”，届时补充精确 `main+offset`、原始指令、BuildID、调用栈和截图/日志。

## 5. 如何复现静态扫描

~~~bash
python scripts/Probe-ZA-Trade-ELF.py --repo . --output .za-work/trade-native
~~~

该命令读取固定 SHA-256 的 `main.elf`，不修改资源，导出 `trade-string-candidates.tsv`、`trade-adr-xrefs.tsv`、`trade-probe-summary.json`。完整结果已在本仓库留存永久 TSV，不依赖 14 天的 Actions Artifact。


## 新增：主程序更深入的检索和指令审核

继续阅读 [[za-trade-native-deep-analysis]]。此次扩展确认：`main+0x2DC413C` 附近的函数序言及 `CommandCancelTrade` 类型名引用；两个 Mega ID `656/657` 邻接表和红蓝宝珠 ID `534/535` 邻接表均混有多种普通 ID，静态代码的同页引用不能误当物品过滤器。真实禁止转移分支仍待运行时验证。
