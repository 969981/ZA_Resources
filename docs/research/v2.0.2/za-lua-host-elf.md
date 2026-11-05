---
aliases:
  - ZA Lua 宿主 ELF 入口与根环境绑定
tags: [ZA, ELF64, AArch64, Lua54, Trinity, native, reverse-engineering, provenance]
version: v2.0.2
status: VERIFIED_ELF_STRING_AND_ADDRESS_XREF_RUNTIME_BINDING_UNKNOWN
source_run: 42028778681
---

# ZA 2.0.2：原生 ExeFS ELF 的 Lua 加载与根环境入口调查

> [!IMPORTANT]
> **本阶段只证明原始 ELF 中字符串、指令地址、PC 相对寻址、静态重定位的真实结构**。没有从孤立字符串、邻近 BL 或 `C` Hash 字面量直接认定某函数是 Lua 加载器。四份 Lua 的 `P0.U0` 运行时绑定尚未闭合，Hash 原名新增确证仍为 **0**。

## 1. 来源验证

现有 `Unpack/v2.0.2/exefs/exefs-manifest.json` 已列出三份经验证的 ELF64 little-endian AArch64 文件。此次直接对原始导出产物做只读扫描，重新核对其 SHA-256，不拆分、不覆盖 ELF、NSO 或 Lua：

| 模块 | 文件大小 | SHA-256 |
| --- | ---: | --- |
| main.elf | 66,579,944 | `470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d` |
| sdk.elf | 12,120,392 | `de3398fd37a44fa5bd0676ff0593543c0c95930f36a9f79c72df2373f596a90f` |
| rtld.elf | 17,792 | `ed25dab00bb23dfb1eafe5085bd915c44b8ea7bfecf888526507cf9dde7ea710` |

## 2. 原生字符串和 AArch64 PC 相对寻址

经过严格关键词过滤，`main.elf` 有 **90** 条候选字符串，**112** 条 `ADR` / `ADRP+ADD` 匹配地址引用；此筛选下 sdk、rtld 均为 0。这里的「地址引用」不等于调用或执行。

| main ELF 原始字符串 | 静态字符串 VA | 已验证的地址引用指令 PC |
| --- | --- | --- |
| `_ENV` | `0x31F263F` | `0x17AD604`, `0x17AD6B8`, `0x17B9920`, `0x17B9F94` |
| `LUA_NOENV` | `0x31A540F` | `0x17CD58C` |
| `LUA_PATH` | `0x326AB1C` | `0x17CD434` |
| `LUA_CPATH` | `0x321E011` | `0x17CD454` |
| `lua_helper` | `0x32B6EDE` | `0x118ACDC` |
| `TrinityHeapType::Lua` | `0x31BBCE5` | `0x1B2430C`, `0x1B244D0`, `0x1B24610` |
| `arc/data.trpfs` | `0x326AE1B` | `0x1A809F0` |
| `data:/arc/data.trpfd` | `0x32EE619` | `0x1A80A24` |
| `script/lua/bin/release/` | `0x31B7C6E` | 未发现当前扫描模式下的直接地址引用 |
| `.blua` | `0x32D7D84` | 未发现当前扫描模式下的直接地址引用 |

尤其重要：`_ENV`、`LUA_NOENV`、`LUA_PATH` 提供了可直接在 Ghidra/IDA 输入的 ELF 虚拟地址；`script/lua/bin/release/` 与 Trinity 中四份 `.blua` 的路径前缀精确一致，但目前尚未证明是谁引用该字符串及如何加载目标脚本。

## 3. 扩展证据：受限指令窗口及静态 ELF 重定位

再次核验精确字符串 VA 后，从 **10 个关键标记**中找出 **13 个指令级地址引用**，只读导出其周围 ±20 条 AArch64 指令，共 **533 条上下文记录**。其中 `BL` 可标注 PC 相对目标；`BLR` 只能标注寄存器；不能把附近的任意 BL 当成真正 Lua API 调用。

`main.elf` 的原始 RELA 类型计数：
- `R_AARCH64_ABS64`（257）：3,323 条。
- `R_AARCH64_GLOB_DAT`（1025）：55 条。
- `R_AARCH64_JUMP_SLOT`（1026）：919 条。

即使按本地已定义符号的 `st_value + r_addend` 处理 ABS64，这 10 个精确字符串 VA **均未取得直接 QWORD 指针字面量或可绑定的相应 RELA 指针位置**。这只是当前精确匹配模型的边界，并不代表字符串未被其它方式使用。

对 5 个未出现于原生 Lua 常量池的 S Hash 与 `IkScriptCommand` 的 C Hash（`0C062DE5AED06885`）进行 ASCII 前缀、16 位十六进制、little/big-endian UInt64 原始字节匹配，三份 ELF 合计 **0 个直接命中**。不能据此断言可执行文件没有对这些值进行运行时计算、编码或间接引用。

## 4. 证据等级与优先研究顺序

- **CONFIRMED**：ELF SHA、版本、段/节映射、候选字符串内容/VA、精确 ADR/ADRP+ADD 静态寻址、限定上下文内的原始指令字。
- **CANDIDATE**：这些地址附近是否属于 Lua 5.4 库实现、Trinity 资源加载器、宿主环境创建函数。
- **UNKNOWN**：四份 Lua 的 `P0.U0` 是否由游戏运行时注册为 `_ENV`、该表内容的实际来源，以及 `IkScriptCommand` C Hash 的真正运行时表值；五条缺失 S 的原始名字。

优先核查：

1. 在 Ghidra/IDA 中从 `main+0x17AD604/0x17AD6B8/0x17B9920/0x17B9F94` 的 `_ENV` 地址引用，识别函数边界、实参及其可调用者，不把邻近跳转当因果链。
2. 对 `main+0x17CD58C` 的 `LUA_NOENV` 关联代码区，分辨 Lua 标准库配置与游戏的宿主脚本加载。
3. 查找 `script/lua/bin/release/` 和 `.blua` 由何种间接加载路径消费，之后与 `arc/data.trpfs` / `data:/arc/data.trpfd` 原生消费者连接。
4. 真正取得 Lua Chunk 加载函数及其 upvalue 初始化/赋值的连续指令证据，才能把 `P0.U0` 从「原生词法捕获」升级为「实际运行时绑定」。
5. 若需要运行时证据，在具备授权的实验环境下用只读断点记录 `P0.U0`、类表写入和方法调用所属对象，建立同一时序的双向对账。

## 5. 复现及生成文件

- [Probe-ZA-Lua-Host-ELF.py](https://github.com/969981/ZA_Resources/blob/master/scripts/Probe-ZA-Lua-Host-ELF.py)
- [Trace-ZA-Lua-Host-Callsites.py](https://github.com/969981/ZA_Resources/blob/master/scripts/Trace-ZA-Lua-Host-Callsites.py)
- [CI Run #42028778681](https://github.com/969981/ZA_Resources/actions/runs/42028778681)，合成测试 **11/11**，原始三份 ELF 逐份 SHA 校验通过。

~~~powershell
py -3 -m unittest discover -s tests -p test_za_lua_host_elf.py -v
py -3 -m unittest discover -s tests -p test_za_lua_host_callsites.py -v
py -3 scripts/Probe-ZA-Lua-Host-ELF.py
py -3 scripts/Trace-ZA-Lua-Host-Callsites.py --window 20
~~~

输出位于 `Unpack/v2.0.2/romfs/arc/data.trpfs/_index/lua-native/`：

- `native-host-elf-probe-summary.json`、`native-host-elf-string-locators.tsv`
- `native-host-elf-adr-references.tsv`、`native-host-elf-hash-probes.tsv`
- `native-host-elf-highsignal-sites.tsv`、`native-host-elf-pointer-sites.tsv`
- `native-host-elf-bounded-context.tsv`、`native-host-elf-callsites-summary.json`

> [!NOTE]
> 所有报告只保存最小化的字符串/地址/指令信息，不复制或修改原始游戏 ELF，保持可重复跑、可人工复核。

关联：[[za-lua-upvalue-captures]]、[[za-lua-closure-callers]]、[[za-lua-native-opcode-evidence]]。
