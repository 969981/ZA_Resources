---
title: ZA v2.0.2 原始道具主表实测、Mega 石与宝珠对账
aliases: [ZA 535 项道具实表, ZA Mega 石与宝珠参数差异]
tags: [Pokemon/ZA, FlatBuffers, 道具, v2.0.2, 原生验证]
status: CONFIRMED_DATA_UNRESOLVED_TRADE
updated: 2026-11-06
---

# ZA v2.0.2 原始道具主表实测与 Mega 石/宝珠对账

> [!success] 已完成的**真实解析**
> 已从 `Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/world/exl/item_data/item_data/item_data.bin` **直接读取 50,372 字节**，按仓库原生 `ItemDataArray.fbs` 解析成 **535 条、50 个 Schema 字段**的完整记录。再按道具的 `Id` 对照简中、英文的 `itemname.dat.json`，不是拿历史最大道具编号猜条数。

关联：[[za-item-data-and-classification]]、[[za-mega-stone-orb-trade-restrictions]]。

## 输入、可下载输出及复现

| 文件 | 内容 | 记录数 |
|---|---|---:|
| [全量道具 CSV](data/za-v2.0.2-items-all-fields.csv) | 535 个道具，50 个原生字段 + 中/英文名称 + 研究分组 | 535 |
| [Mega 石、宝珠、普通携带物对比 CSV](data/za-v2.0.2-mega-orbs-controls.csv) | 92 Mega 石、2 宝珠、12 种对照物，字段保持完整 | 106 |
| [结构化统计 JSON](data/za-v2.0.2-item-summary.json) | 记录数、字段数、分类统计、共同属性及原始 Git blob SHA | — |
| [原生二进制](../../../Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/world/exl/item_data/item_data/item_data.bin) | 只读源输入，Git blob `128dc0c3e423486c3c753f8bf17f0186fa40d241` | 535 |
| [导出脚本](../../../scripts/Export-ZA-Items.py) | 无第三方 Python 依赖、可在本地复现全部 CSV | — |
| [合成测试](../../../tests/test_za_item_export.py) | 字段注解、ushort 枚举、单记录、越界、分类及真实资源测试 | — |

执行方法：仓库根目录运行：

~~~bash
python scripts/Export-ZA-Items.py --repo . --version v2.0.2 --output .za-work/items
python -m unittest discover -s tests -p test_za_item_export.py -v
~~~

[GitHub Actions 对账](../../../.github/workflows/za-itemdata-export.yml) 使用稀疏检出复核源 BIN，并导出一个可下载的 `za-v2.0.2-items` Artifact。**上面的导出和统计已由本次直接解析得到；CI 是否成功另以真实 Actions 日志为准，不把工作流文件存在当成 CI 成功。**

## 结构完整性

- 原始大小：**50,372 bytes**。
- `ItemDataArray.Table`：**535 条**；`Id` **全部唯一**。
- ID 最小 **1**、最大 **2684**。**不能**把 1~2684 全部认为“存在于主表”。
- Schema 字段：**50**；CSV 额外提供 `NameZH`、`NameEN`、`ResearchGroup`，总计 **53 列**。
- `ItemType` 原始值计数：`0:29, 1:66, 2:58, 3:28, 4:26, 5:160, 7:160, 9:8`。枚举 `6、8` 当前源表无记录，不给它们强加中文含义。
- `Pocket` 原始值计数：`0:19, 1:26, 2:121, 3:7, 4:44, 5:66, 6:160, 7:92`。
- 只有 **3 条**记录为 `CanNotHold=true`：`1278 洛托姆型录`、`2137 索财灵的硬币`、`2619 彩色螺丝`。由此明确：`CanNotHold` 不是“禁止联机交易”的同义词。

## 最重要的实测对比

| 字段 | Mega 石（全部 92 种） | Red Orb（534） | Blue Orb（535） | Leftovers（234） |
|---|---|---|---|---|
| 中文 | 各物种进化石 | 朱红色宝珠 | 靛蓝色宝珠 | 吃剩的东西 |
| `ItemType` | **7** | **7** | **7** | **7** |
| `Pocket` | **7** | **2** | **2** | **2** |
| `SlotMaxNum` | **1** | **999** | **999** | **999** |
| `CanNotHold` | false | false | false | false |
| `WorkFormChange` | false | false | false | false |
| `CanUseInBattle` | false | false | false | false |
| `MachineIndex` | -1 | -1 | -1 | -1 |

关键结论：
1. **92 种 Mega 石全都同时具备 `ItemType=7`、`Pocket=7`、`SlotMaxNum=1`、`CanNotHold=false`。** `SlotMaxNum=1` 与官方同种 Mega 石只持一枚的规则相一致。
2. **红蓝宝珠与 Mega 石不在同一个 Pocket，也没有单件 1 的上限。** 因此“红蓝宝珠被禁止交换**是因为它们和 Mega 石同为 Pocket 7**”这种解释被原始数据直接否定（REJECTED）。
3. **红蓝宝珠和普通携带物拥有一样的 `ItemType=7`、`Pocket=2`、`SlotMaxNum=999`、`CanNotHold=false` 基础配置。** 这些字段不足以区分是否可通过联机交换转移。
4. 主表中 Mega 石和红蓝宝珠的 `WorkFormChange` 都是 false；不能把此字段当成是否触发 Mega 或原始回归的唯一判断。
5. 不能因上述字段共有某个值就宣称找到了交换拦截谓词。**ItemData 没有 `CanTrade` 字段**，专有交换规则很可能在其他游戏代码或数据中（CANDIDATE）。

### 快速核对目标 ID

- `534` 朱红色宝珠；`535` 靛蓝色宝珠。
- `656` 耿鬼进化石；`662` 超梦进化石Ｘ；`663` 超梦进化石Ｙ。
- `764` 蒂安希进化石；`2579` 花叶蒂进化石；`2584` 基格尔德进化石。
- `231` 幸运蛋；`233` 金属膜；`234` 吃剩的东西；`270` 生命宝珠；`275` 气势披带；`538` 进化奇石。
- 从 CSV 研究分组筛选 `MegaStone` 获得所有 **92 个**精确 ID，避免以 ID 连续性推断实际条目。

## 定位 Link Trade 禁止转移函数：当前证据边界

本次同时排查了：
- `tools/PokeDocs/ZA/Hashlists/Lua/lua_c_hashes.txt`、`lua_f_hashes.txt`、`lua_s_hashes.txt`；
- `_index/lua-native/native-haxe-crosswalk.tsv`、`native-unknown-direct-call-edges.tsv`；
- 已有 [原生 ELF/Lua 定位证据](za-lua-host-elf.md)。

在这些**已命名、已有的** Lua 哈希表及调用链报告里，未发现可直接确认的 `Trade`/`Exchange`/`HeldItem` 交易检查函数。**没有命中不等于没有代码**：函数可能没有名字、使用非 Lua 模块、通过间接调用，或必须从 ARM64 `main.elf` 追踪。

### 仍需取得的原生执行证据

1. 输入：已提取 `Unpack/v2.0.2/exefs/main/main.elf`（**66,579,944 bytes**）及游戏运行中的 BuildID/加载基址。
2. 正对照：可交易 Pokémon + 普通携带物（例如金属膜 `233` 或吃剩的东西 `234`）。
3. 负对照：同 Pokémon 改持一个 Mega 石（例如耿鬼进化石 `656`）；再分别测试红、蓝宝珠 `534/535`。
4. **分别记录**选取时拒绝、确认后拒绝、宝可梦成功交换但物品返还等情况；它们对应不同判定点。
5. 只读追踪：交易 UI 状态机 → 提取 Pokémon `HeldItem` → 读取物品 ID / `ItemData` → 条件分支 → 交换提交。记录地址 `main+offset`、寄存器、跳转指令、正负对照结果与同一 BuildID。
6. 仅当能在**相同调用链**中复现正常携带物通过、目标特殊道具不通过，才将“某地址是交换限制函数”标注 CONFIRMED。

> [!danger] 尚未证实
> **目前不能给出可靠的 `main+0x...` 交换限制地址，也不能证明红蓝宝珠与 Mega 石使用相同检查。** 不能拿 NPC 花蓓蓓交换的 `field_trade.dat.json` 提示当联机代码定位结果。

## 研究结论

**已确认道具实表配置存在清晰分界：Mega 石是单独口袋、单件上限；宝珠与普通携带物同口袋、999 件上限。交换转移逻辑是否以及如何利用这些条件，必须继续通过本地 ARM64 执行路径和真正的联机交换状态来证实。**


## 本次新增原生交易候选扫描

已对 v2.0.2 的真实 `main.elf` 完成 ELF64/AArch64 只读分析：发现 **68 条交易相关字符串与 5 条 ADRP+ADD 精确指令引用**，永久 TSV 已存入仓库。详见 [[za-trade-native-candidates]]。目前只有静态入口线索，**没有足够证据确认联机交换限制函数地址**。
