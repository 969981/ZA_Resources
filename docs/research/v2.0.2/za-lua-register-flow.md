---
tags: [pokemon-za, lua, lua54, trinity, register-flow, native-evidence]
status: SCRIPT_SYNTHETIC_TESTED_NATIVE_CI_PENDING
version: v2.0.2
---
# ZA 2.0.2：Lua 原生寄存器数据流与未知 Hash

## 研究起点

原生 `dll_util`、`event_ik`、`main`、`main_dynamic` 四份 Lua 5.4 已发布并通过 SHA-256 与完整解析；见 [[za-lua-native-opcode-evidence]]。其中未知 S/F/E 的原生常量 1,365 次、原生 opcode 引用 2,140 次、相邻字段访问→CALL 566 次。这是**字节码调用证据**，不是原始标识符恢复。

最新的原生常量 TSV 有 157 种未知目标 Hash。另 5 条 S 在这四份字节码的目标常量池中**没有出现**，不是扩大 `CALL`/`GETTABLE` 识别规则就能补齐：

| 原始 S 行 | Hash | 交叉佐证源（第三方 Haxe，非原生） |
| ---: | --- | --- |
| 23 | `062729EC443620C2` | `source/event_ik/Ev_sys_megarematch_lose.hx:41` |
| 72 | `1463948047021356` | `source/event_ik/Ev_sys_megarematch_lose.hx:38` |
| 164 | `34AD86B7E5BB1526` | `source/event_ik/Ev_sys_megarematch_lose.hx:42` |
| 403 | `81E0610BF8B9337C` | `source/event_ik/Ev_sys_megarematch.hx:9` |
| 685 | `D0F61B3481E43C08` | `source/event_ik/Ev_sys_megarematch.hx:12` |

第三方源码路径只是定位候选，不能倒推出游戏原名或当前四包中必有对应字节码；五项必须继续搜其他版本/包/资产，保留 UNKNOWN。

## 本阶段新增工具

`python scripts/Trace-ZA-Lua-RegisterFlow.py --max-window 16`

在每个原生 Prototype 内：

1. `GETFIELD`、`GETTABUP`、`SELF(k=1)` 的 Hash 常量建立字段值来源；
2. `LOADK`/`LOADKX` 与 `MOVE` 追踪短程 key-register，再定位 `GETTABLE`、`SETTABLE`、`SELF(k=0)` 的未知 Hash 使用；
3. `MOVE` 的确证复制关系传递字段来源至新的函数寄存器，直到 `CALL` 或 `TAILCALL`；
4. 遇到未知副作用指令、条件、跳转、函数调用、表写入以及已知跳转落点即丢弃寄存器状态，避免跨分支伪造链路；
5. 读取已固定的四份原生文件 SHA-256、原始 Pack 唯一性、已有 566 条邻接证据，并单独报告新的非邻接边与因更严格控制流规则排除的原邻接边。

在 `Unpack/v2.0.2/romfs/arc/data.trpfs/_index/lua-native/` 产生：

- `native-unknown-register-flow-calls.tsv`：实际 `field_pc → CALL_pc`、寄存器、`MOVE` 次数与字节偏移；
- `native-unknown-register-key-uses.tsv`：原生 `LOADK` 键进入动态表访问/写入的确证局部关系；
- `native-unknown-register-flow-summary.json`：来源 SHA、样本计数、基线差异与证据限制。

此工具的证据等级为 `NATIVE_LUA54_STRAIGHT_LINE_REGISTER_CALL` 与 `NATIVE_LUA54_REGISTER_KEY_TABLE_REFERENCE`。前者不证明运行时一定执行、接收对象类型或原始符号名；后者不等于函数调用。

## 运行与证据等级

```powershell
py -3 -m unittest discover -s tests -p test_za_lua_register_flow.py -v
py -3 scripts/Trace-ZA-Lua-RegisterFlow.py --max-window 16
```

本地合成指令测试与真实原生字节码全量 CI 结果应分别记录。不能在 CI 完成前宣称新增原生调用数量，也不能自动覆盖 PokeDocs 的 S/F/E 原始 Hash 表。新工作流 `za-lua-native-register-flow.yml` 在研究分支先测试并上传 Artifact；合并到 `master` 后才将通过校验的 TSV/JSON 提交入仓库。

下一步需要从已知的 `C→F`/`C→S` 根闭包所指向的 child Prototype 出发，将寄存器级字段引用连接到明确的方法所属对象，优先挑选有多重 Hash/原型上下文的调用，而非用第三方名称直接替换 UNKNOWN。