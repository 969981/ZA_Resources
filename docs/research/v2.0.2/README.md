# Z-A v2.0.2 investigation index

Starting points:
- ExeFS modules and the source inventory already committed under `v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/`.
- Trinity descriptor and container: `1/arc/data.trpfd` + `data.trpfs`.
- Audio: Wwise bank/pack files.
- Runtime/game-data analysis: separate verified research notes.

No internal Trinity field maps have been independently validated in this document yet. Use [the note template](TECHNICAL_NOTE_TEMPLATE.md) for new discoveries.

## Lua 5.4 原生逆向

- [TRPFD 索引中四个 Lua Pack 的原始位置](za-lua-native-targets.md)
- [已真实解出的 4 份 Lua 5.4、9,222 个 Proto、2,140 条未知 Hash 原生指令引用](za-lua-native-opcode-evidence.md) — 不把原生 Hash 引用误写成恢复原始名称。
- [原生寄存器追踪：1,488 条局部字段→CALL、其中新增 922 条](za-lua-register-flow.md) — 经 4 份 SHA-256 验证的字节码执行，原始名字仍未确认。
- [原生闭包归属：1,461 直接＋7 词法嵌套，926 条五类静态 C Hash 查找](za-lua-closure-callers.md) — 严格区分 caller class 与 runtime receiver，另 5 条 S 缺失于四份原生常量池。
- [原生 Upvalue 描述符和 CLOSURE 创建链：926 条全部追到根 Chunk 外部 Upvalue](za-lua-upvalue-captures.md) — 512 Proto，保留 7＋20 条闭包异常证据，运行时绑定仍未知。
- [原生 ELF Lua 宿主定位：_ENV、LUA_NOENV、Lua 路径及 AArch64 xrefs](za-lua-host-elf.md) — 验证三份 ELF、13 个高信号地址引用，根 P0.U0 的运行时绑定仍未知。
- [PokeDocs 三轮 11.67 亿次定向 Hash 文法枚举：ZA 16 个 H2 精确候选及五条原生缺失 S 的对账](za-lua-h2-bruteforce-sync.md) — 只读候选映射，不修改原生 Hashlist；H2 不等于原生已确认原名。

## 事件与异色研究

- [Z-A 神兽锁闪证据链与蒂安希 EX1／超梦 EX2 的任务、触发器、遭遇数据](za-legendary-shiny-lock-diancie-mewtwo-events.md) — 已直接解析 v2.0.2 的 `sub_quest.bin`、`trigger_sub_0119.bin`、`trigger_sub_0120.bin` 和遭遇表；原生异色模式判断指令已静态定位；EX1/EX2 运行时入口仍待验证。
- [本次 FlatBuffers 原始解析证据 JSON](za-ex1-ex2-flatbuffers-evidence.json) — 任务 ID、8+4 条触发记录、战斗标识及遭遇数据原值。

## Rare 原生 ARM64 静态审计

- [v2.0.2 神兽锁闪运行时代码静态审计](za-rare-arm64-runtime-chain-audit.md) — battle 数据中间层、ELF SHA、5 个精确掩码位点的反汇编与误报分析（原生执行链未闭合）。
- [Rare ARM64 全部候选 JSON](za-rare-arm64-static-candidates.json) / [5 处原生反汇编](za-rare-arm64-exact-sites.md) — 静态位置，非已确认的运行时 main+offset。

- [EX1／EX2 的原生 Spawner 精确交叉引用](za-ex1-ex2-spawner-crosswalk.json) — `id_sub119_01 → sub_119_diancie`、`id_sub120_01 → sub_120_mewtwo`，13 组数据库共 2,211 条源记录，通过真实文件及合成测试核实。

- [原生三态异色生成、PID XOR、防闪与实际分支（新增核心研究）](za-native-shiny-generator-pid-branch.md) — 0x6570C4–0x6571A0、0xE5D1E8、0xE5D200、0xE5D21C 原生 ARM64 静态确认，精确说明与原始 Rare 字段转换仍未闭合的部分。
- [原生 PID getter/setter 调用研究](za-pid-accessor-native-xrefs.md) / [精确 B/BL 引用 JSON](za-pid-accessor-callsite-xrefs.json) / [PID 防闪调用者汇编](za-pid-antishiny-caller-contexts.md) — 主程序 SHA 及 CI 测试通过。

- [描述结构 +0x68 → 内部 64 位 Rare 模式与 PID 生成完整静态证据](za-native-shiny-generator-pid-branch.md) / [5 条真正的状态构建调用者](za-native-rare-builder-callers.md) — 包括 +0x68 原始 `0x2FFFFFFF` 比较、实际转换指令和 0xE3EB64 生成器到个体 setter 的代码链。

## EX1／EX2 Rare 字段来源与 GDB 验证

- [EX1 蒂安希／EX2 超梦 Rare 来源及 GDB 取证操作文档](za-ex1-ex2-rare-provenance-gdb-validation.md) — 明确已闭合的原生静态 PID 处理和仍未验证的 FlatBuffers→+0x68 内存赋值、实机 EX 战斗。
- [主程序 +0x68 读写访问普查 JSON](za-rare-descriptor-offset68-xrefs.json) / [上游候选函数反汇编](za-rare-native-descriptor-origin-candidates.md) — 审计所有特定 LDR/STR 直接访问，排除把常见结构偏移误报为 Rare setter。
- [只读 GDB 记录器](../../../scripts/gdb/za_ex_rare_trace.py) / [EX1 EX2 日志对账工具](../../../scripts/Analyze-ZA-EX-Rare-GDB.py) — CI 完成合成测试；尚无实机日志，不将其当作运行时已证实。

## 道具和交换限制（Obsidian）
- [道具主表 FlatBuffers、分类体系、中文文本及导出流程](za-item-data-and-classification.md)
- [Mega 石与红蓝宝珠交换限制：证据、设计假说与实测路径](za-mega-stone-orb-trade-restrictions.md)
- [ZA 2.0.2 原生道具 535 项实表、92 种 Mega 石和红蓝宝珠对账](za-items-real-data-audit.md) — 完整字段 CSV、中文关联、对照组和复现脚本。
- [ZA v2.0.2 联机交换原生 ELF 静态候选（68 字符串、5 条指令引用）](za-trade-native-candidates.md) — 固定主程序 SHA、证据 TSV 与 GDB 后续对照。
## 535 条道具全分组与交换原生深入研究
- [ItemType × Pocket 的 12 个组合、535 条中英双语全量清单](za-itemtype-pocket-complete.md)
- [Link Trade 原生静态深挖：CommandCancelTrade 指令、历史 ID 表与待做 GDB 验证](za-trade-native-deep-analysis.md)
