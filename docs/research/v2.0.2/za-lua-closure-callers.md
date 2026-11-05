---
aliases:
  - ZA Lua 原生调用者闭包与接收对象来源
tags: [pokemon-za, Lua54, Trinity, native, closure, register-flow, provenance]
version: v2.0.2
status: VERIFIED_LEXICAL_OWNER_RECEIVER_CLASS_UNCONFIRMED
source_run: 42021695658
---

# ZA 2.0.2：原生闭包归属、SELF 接收对象与五条缺失 S

> [!IMPORTANT]
> **owner class 只是原生 CALL 指令所在闭包的注册类，不是被调用对象的类。** 标识符原名恢复仍为 0，不对 PokeDocs Hashlist 做推测回填。原生字节码的静态执行路径不能证明运行时实际被调用。

## 1. 固定证据输入

- 四份已通过 SHA-256 的 Lua 5.4 原始文件：dll_util、event_ik、main、main_dynamic。
- `native-c-f-method-edges.tsv`：3,064 条根原型 C→prototype→F 闭包。
- `native-c-s-static-edges.tsv`：878 条根原型 C→S 静态闭包。
- `native-unknown-register-flow-calls.tsv`：1,488 条局部字段→CALL/TAILCALL。
- `pack_index.tsv`：13,181 个原生 TRPAK 描述符包。
- 研究脚本：[Join-ZA-Lua-Closure-Callers.py](../../../scripts/Join-ZA-Lua-Closure-Callers.py)、[Audit-ZA-Lua-PackCoverage.py](../../../scripts/Audit-ZA-Lua-PackCoverage.py)。

## 2. 闭包归属核对

采用同一 `source` 加 `child_proto_id` / `closure_proto_id` 对接目标调用记录的 `proto_id`。若无直接匹配，再依据真实原生 Lua Prototype 的 `parent` 链作嵌套词法关联；多重匹配直接标记冲突，不猜测所属类。

| 归属证据 | 调用数 |
| --- | ---: |
| 直接注册 C→F/C→S 闭包体 | **1,461** |
| 仅词法嵌套于注册闭包 | **7** |
| 未找到支持的注册闭包 | **20** |
| 冲突归属 | **0** |
| 合计 | **1,488** |

直接闭包体涉及 **606 种类 Hash**。注意它们是调用者的 C，不一定是接收字段的 C。

## 3. SELF / GETTABLE / GETFIELD 接收者寄存器来源

工具根据原生 `field_pc` 字节码取得 B（作为寄存器）或 GETTABUP 的 Upvalue 槽，向前最多追踪 16 条指令。只允许明确读取、加载、MOVE 及少量表操作，遇到未知指令、跳转或控制流入口便停止。全部记录仍将 `receiver_class_confirmed=NO`。

| 静态来源 | 调用数 |
| --- | ---: |
| UPVALUE_KEY_LOOKUP | **926** |
| UNKNOWN_OPCODE_BARRIER | **496** |
| SOURCE_OUTSIDE_WINDOW | **57** |
| TABLE_VALUE_FROM_DIRECT_UPVALUE_SLOT | **5** |
| CONTROL_FLOW_BOUNDARY | **2** |
| DIRECT_UPVALUE_SLOT | **2** |

静态 `Cxxxxxxxxxxxxxxxx` 键只证明某次对象值读取使用该键字面量，**不证明**实际 Lua 表/Upvalue 的运行时身份，也不证明动态实例属于该 C。

## 4. 完整 Trinity 描述符范围核查

本版本完整 13,181 包描述符中，后缀精确为 `.blua.trpak` 的仅四个：
- 12145：dll_util
- 12146：event_ik
- 12147：main
- 12148：main_dynamic

四份原生 Lua 常量池共覆盖原始 unresolved 索引 157/162 个目标 Hash。剩余五条 S 不在这四份目标常量池之内：

| 原始 S 行 | Hash | 第三方检索线索（不是原名证据） |
| ---: | --- | --- |
| 23 | `062729EC443620C2` | Ev_sys_megarematch_lose.hx:41 |
| 72 | `1463948047021356` | Ev_sys_megarematch_lose.hx:38 |
| 164 | `34AD86B7E5BB1526` | Ev_sys_megarematch_lose.hx:42 |
| 403 | `81E0610BF8B9337C` | Ev_sys_megarematch.hx:9 |
| 685 | `D0F61B3481E43C08` | Ev_sys_megarematch.hx:12 |

这只证明**本版本已公开完整 Trinity pack index 没有第五个同后缀包**。不能据此断言该符号在其它编码、可执行模块、资料片或其它游戏版本中不存在，也不意味着 Haxe 占位符与游戏内容直接等价。

## 5. CI 与复现

[原生 CI Run 42021695658](https://github.com/969981/ZA_Resources/actions/runs/42021695658)：14 个合成测试成功、四份原生文件 SHA-256 复核、1,488 条逐指令验证和全包索引审计通过。

~~~powershell
py -3 -m unittest discover -s tests -p test_za_lua_closure_callers.py -v
py -3 -m unittest discover -s tests -p test_za_lua_pack_coverage.py -v
py -3 scripts/Join-ZA-Lua-Closure-Callers.py --window 16
py -3 scripts/Audit-ZA-Lua-PackCoverage.py
~~~

输出均在 `Unpack/v2.0.2/romfs/arc/data.trpfs/_index/lua-native/`：
- `native-closure-caller-receiver.tsv`：逐条的 owner class、owner member、调用 PC、接收者寄存器回溯。
- `native-closure-caller-receiver-summary.json`：归属/来源类别统计与输入 Hash。
- `native-lua-pack-coverage.json`：13,181 包覆盖与五条缺口。

## 6. 下一步研究闭环

1. 对 926 条 UPVALUE_KEY_LOOKUP，读取每条 `C` 类字面量（如存在）、Upvalue 槽和上层闭包的 `GETUPVAL/CLOSURE` 路径；应区分“类名的静态表键”和“真实接收者类型”。
2. 对 7 条嵌套闭包，向父原型追踪闭包的创建 PC、捕获的 Upvalue 和赋值/调用语句，提升其归属置信度。
3. 对 20 条未归属 CALL，检查是否为根原型初始化/间接闭包/动态注册路径；没有注册语义时保持 UNKNOWN。
4. 对五条缺失 S，扩大到其它构建或可执行文件实际消费者；仅有第三方 Haxe 线索时不得更改 Hashlist。

关联：[[za-lua-native-opcode-evidence]]、[[za-lua-register-flow]]、[[za-lua-native-targets]]。
