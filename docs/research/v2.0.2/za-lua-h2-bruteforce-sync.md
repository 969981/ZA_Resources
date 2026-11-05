---
tags: [pokemon-za, Lua54, Hash, H2, FNV1a, native-evidence, Obsidian]
version: v2.0.2
date: 2026-11-05
status: SOURCE_GRAMMAR_EXACT_MATCH_NOT_NATIVE_ORIGINAL_NAME
---

# ZA 2.0.2 Lua：PokeDocs 三轮 H2 暴力候选对账（16 条）

> [!IMPORTANT] **本页是跨仓库研究摘要，不是恢复出原版 Lua 可读字符串的证明。** ZA 当前 PokeDocs/develop 未命名 **S 114 / F 41** 行未修改。以下共 **S 10 / F 6** 个新完整 64 位 Hash 精确候选（H2）；没有写进原始 Hashlist，也没有把 Haxe 重建源码当成 2.0.2 原生调用链原名。

## 已完成的原生 C++ 命名文法计算

- PokeDocs 三轮实际候选计算总计 **1,167,121,655 次**（含不同轮次重复组合），包括 SV C 和 ZA S/F。
- 第一轮：ZA 162,271,660 次，新增 12 个。
- 第二轮：ZA 388,577,622 次，基于前轮 H2 种子扩展，再新增 3 个。
- 第三轮：ZA `Ev_sys_megarematch` 上下文专用 317,296,440 次，再新增 1 个。
- 结果合并为 **ZA S 10 / F 6**。候选全部根据原始空白行的完整 64 位 Hash 独立复算，并与目前 ZA 原生 Opcode/闭包索引分别关联。

可追溯主证据：

- [PokeDocs H2 Overlay：SV/ZA 28 条](https://github.com/969981/PokeDocs/blob/develop/docs/evidence/hash-bruteforce-2026-11-05/h2-candidate-overlay.tsv)
- [输入来源 SHA-256、分组、确认级别 JSON](https://github.com/969981/PokeDocs/blob/develop/docs/evidence/hash-bruteforce-2026-11-05/h2-overlay-summary.json)
- [三个阶段的完整分析与计算边界](https://github.com/969981/PokeDocs/blob/develop/docs/Lua-Hash-BruteForce-2026-11-05.md)
- 原生成功 CI：[第一轮](https://github.com/969981/PokeDocs/actions/runs/42029953436)、[第二轮](https://github.com/969981/PokeDocs/actions/runs/42031392850)、[Mega Rematch 定向第三轮](https://github.com/969981/PokeDocs/actions/runs/42032644286)、[H2 Overlay 校验](https://github.com/969981/PokeDocs/actions/runs/42033011221)。

## 五条四包缺失 S：已有三条 H2 字符串

这五条在已验证的四份 ZA v2.0.2 BLUA（Pack 12145–12148）**原生目标常量池中没有出现**。由于名称匹配只发生在 PokeDocs 的候选文法计算中，原始常量缺失这一事实不发生变化。

| S 行 | 64 位 Hash | H2 候选 | 备注 |
| ---: | --- | --- | --- |
| 23 | `062729EC443620C2` | `Get_BossName` | 初次命中；上下文函数从选择值取消息 |
| 72 | `1463948047021356` | `Get_BossNameIndex` | 第二轮 H2 种子扩展命中 |
| 164 | `34AD86B7E5BB1526` | `Get_BossBattleID` | 第三轮定向事件词汇命中 |
| 403 | `81E0610BF8B9337C` | **未命中** | 重建 Haxe 中是 Mega Rematch 选择消息数组 |
| 685 | `D0F61B3481E43C08` | **未命中** | 重建 Haxe 中是 SPN Boss 数组 |

这三个候选互相关联，但**完整 Hash 精确匹配 ≠ 原版可读标识符必然等于此字符串**。第三方重建可用来指导下一轮词典，不允许成为 H3 原名凭据；剩余两条仍保持 UNKNOWN，拒绝推测填充。

## 其它 13 个 ZA H2：原生 Opcode 关系

除上面的三个四包缺失 S，其它 13 个 ZA 命中都有独立的原生 Opcode 引用，其中：

- `S522136910C73A819` 候选 `Wait_CompleteTurn`：当前原生索引有 **744 条 Opcode 引用、1 条 C→S 静态闭包**，可优先沿实际消费者追踪。
- `F931F8A64586A46A6` 候选 `ShowMessageNpcEvent`：有 **78 条原生 Opcode 引用**，适合做对应 Proto/PC 交叉核对。
- `S80725197C3054FB8` 候选 `StopRequestPauseEventDisable`：6 条原生 Opcode 引用，含 5 条相邻字段调用边。
- 剩余逐条请直接查 [Overlay TSV](https://github.com/969981/PokeDocs/blob/develop/docs/evidence/hash-bruteforce-2026-11-05/h2-candidate-overlay.tsv) 中 `native_structure/native_opcode_refs/native_C_to_S_edges`。

请严格区分：**原生引用证实“Hash 曾被某条指令使用”，并不能直接证实这个 H2 可读字符串存在于原版源码。**

## 下一步

1. 对 `Wait_CompleteTurn` 与 `ShowMessageNpcEvent`，优先连接 `child_proto_id / proto_id / field_pc / call_pc`、Upvalue 捕获链和 ELF Lua 宿主结构，证明接收者值来源。
2. 对两条未命中数组 Hash，调查其它原始版本/脚本编译前标识符来源；不要凭语义自填数组变量名。
3. 工具要展示可读名称时，**只读引用单独的 H2 Overlay** 并明确标注“候选”，不覆盖当前 PokeDocs 的未知行或 ZA 原始资源。

关联：[[za-lua-closure-callers]]、[[za-lua-upvalue-captures]]、[[za-lua-native-opcode-evidence]]、[[za-lua-host-elf]]。
