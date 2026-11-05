---
aliases:
  - ZA Lua 原生 Upvalue 捕获链与闭包创建
tags: [pokemon-za, Lua54, Trinity, native, Upvalue, CLOSURE, Obsidian, evidence]
version: v2.0.2
status: VERIFIED_LEXICAL_CAPTURE_RUNTIME_ENV_UNKNOWN
source_run: 42025851252
---

# ZA 2.0.2：沿 CLOSURE 捕获链追踪 926 条静态类键

> [!IMPORTANT]
> 这里的“根 Chunk 外部 Upvalue”指 Lua 5.4 字节码所描述的捕获源，不是已确证的运行时 `_ENV` 表，更不是 CALL 的动态接收实例。**原始 Hash 名称新增确认：0；运行时接收者类确认：0。**

## 1. 字节码解析器改动

原先的 `scripts/_vendor/Analyze-SV-Lua54.py` 在定位 Lua 5.4 Prototype 的 Upvalue 数据时跳过三个字节的 `instack/idx/kind` 描述符。本轮在不修改任何原始数据的前提下保留每项原始描述符，额外核验：

- `nupvalues` 数量必须能用 8-bit Upvalue 指令索引表示。
- `instack` 必须属于 `0/1`；0 代表捕获父原型的 Upvalue，1 代表捕获父原型的寄存器。
- 根 Prototype 的 `nupvalues` 与 Chunk 文件头的 `main_upvalues` 一致。
- 原生 `CLOSURE` 的 Bx 必须落在父 Prototype 的 child-index 内；沿 parent tree 精确查找创建位置。
- 对 `instack=1` 的父寄存器，通过既有 16 指令保守回溯寻找其生产者。多处创建不擅自认定唯一运行时来源。
- 每份输入重新检查 SHA-256、原生 Pack 索引和 Prototype 数量。

## 2. 原生追踪结果

来自 1,488 条调用中 926 条 `UPVALUE_KEY_LOOKUP`：

| 指标 | 真实验证值 |
| --- | ---: |
| 静态 C Hash 键查找 | **926** |
| 涉及不同原生 Prototype | **512** |
| 沿捕获关系追到根 Chunk 外部 Upvalue | **926** |
| 20 条此前未注册的 CALL | **20**（11 个 Proto，全部 main） |
| 词法嵌套方法 CALL | **7** |
| 原始名称或实例接收者类新增确认 | **0** |

五组静态查找键数量保持不变：`IkScriptCommand` 908、`CafeEvent` 8、`CharacterCommand` 7、`ObjectTemplateDataManager` 2、`FadeCommand` 1。它们是 PokeDocs 已存在的 C 表名字，本轮只增加了原生捕获拓扑证据。

**可以证明**：926 次被调用字段前的类 Hash 表查找，使用的 Upvalue 引用都能经原生捕获描述符回溯到根 Chunk 外部 Upvalue。

**不能证明**：外部 Upvalue 的宿主如何初始化、何时修改、是否等同 Lua `_ENV`，以及被调用表值是否具有与 C Hash 对应的运行时实例类型。

## 3. 修复 7+20 结构证据的可复核性

除了 926 条捕获链，本轮对之前只标记为“词法嵌套”的 7 条，以及 20 条缺乏注册 owner 的 CALL 逐条导出了 `parent_proto_id`、`parent_child_index`、父原型 `CLOSURE Bx` 创建 PC、以及当前子原型的全部 Upvalue `instack/idx/kind`。

这只能提升闭包**创建位置与上下文**的证据等级；原始 C→F/C→S 注册仍未出现在这 20 条对应的直接方法映射中，因此不强行分类到某个原始类。

## 4. 已提交的复现脚本及输出

- [上游解析器：保存 Upvalue 原始描述符](https://github.com/969981/ZA_Resources/blob/master/scripts/_vendor/Analyze-SV-Lua54.py)
- [Trace-ZA-Lua-Upvalue-Captures.py](https://github.com/969981/ZA_Resources/blob/master/scripts/Trace-ZA-Lua-Upvalue-Captures.py)
- [合成测试](https://github.com/969981/ZA_Resources/blob/master/tests/test_za_lua_upvalue_captures.py)
- [CI Run #42025851252](https://github.com/969981/ZA_Resources/actions/runs/42025851252)

~~~powershell
py -3 -m unittest discover -s tests -p test_za_lua_upvalue_captures.py -v
py -3 scripts/Trace-ZA-Lua-Upvalue-Captures.py --max-window 16
~~~

输出位置：`Unpack/v2.0.2/romfs/arc/data.trpfs/_index/lua-native/`

- `native-upvalue-capture-lookups.tsv`：926 条原生 C 键、GETTABUP PC/offset、Upvalue 槽和捕获链。
- `native-closure-unresolved-sites.tsv`：7 + 20 条无直接方法闭包归属 CALL 的父子创建指令、Upvalue 布局。
- `native-upvalue-capture-summary.json`：256 位输入完整性、原生 Proto 数量和各等级统计。

## 5. 下一轮突破点

由于 926 条已统一回溯到根 Chunk 的外部 Upvalue，继续扩大普通字段引用扫描的价值下降。下一步更直接的路线应是：

1. 在 ExeFS 中查找创建 Lua VM、加载四份原生 `.blua`、初始化根 Chunk Upvalue 的函数与调用点，证明宿主环境究竟指向哪里。
2. 针对 `IkScriptCommand` 在该环境下的静态 C 键读取，追踪表值由哪段初始化代码写入；尽可能建立 `C Hash → 表值来源 → 原生方法 CALL` 的闭环。
3. 对 20 条 `main` 未归属 CALL，通过 `CLOSURE` Bx 和父函数写入关系检查是否是内部辅助方法/动态注册，而不是推测正式类名。
4. 五条未命中任何 Lua 常量池的 S 保持未知，继续查找其他版本或二进制引用。

关联：[[za-lua-closure-callers]]、[[za-lua-register-flow]]、[[za-lua-native-opcode-evidence]]。
