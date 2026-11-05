---
aliases:
  - ZA 原生 Lua 5.4 解析
  - ZA Lua 四个 TRPAK 原生字节码
tags: [pokemon-za, lua, native-bytecode, trinity, opcode, evidence]
game_version: v2.0.2
status: NATIVE_LUA54_FOUR_FILES_VERIFIED
source_workflow_run: 42011668436
source_artifact_id: 13407204049
---

# ZA v2.0.2 — 原生 Lua 已提取：四个 .blua、指令引用与类闭包

> [!warning] 证据边界
> 本轮四份字节码确实来自 SHA-256 已校验的原版 TRPFD/TRPFS，并完整通过 Lua 5.4 解析。**原生 Hash 常量被实际 opcode 引用，不能自动确定原始名称**。重建 Haxe 的命名/调用上下文只有独立交叉佐证；不会把 Hash 字面量或静态闭包直接误当为原版名字。

## 1. 原始来源和提取证明

- 原始 `data.trpfd`：9,877,520 bytes；SHA-256 `d1beb3763deab33691c5930e026006278f4586dac094f8d0ea2494ecb6f851f8`。
- 原始 `data.trpfs`：4,753,821,072 bytes；SHA-256 `64169ef62030dd8e39bb884aff885fd51e7c0758c595c64c4b3fb7b6dad9683d`，从 87 个 7z 分卷重建并校验。
- 实际提取：[ZA four-pack workflow run 42011668436](https://github.com/969981/ZA_Resources/actions/runs/42011668436)，四个目标均成功读取，`failedFileCount:0`，`verifiedExtractedBytes:8177757`。工作流最终 **Git rebase 因未暂存的工作区变化失败**，但 Windows 原生资源已保存为 Actions Artifact `13407204049`；这不是 Lua 解码失败。
- Artifact 后续由独立 `za-lua-native-artifact-publish.yml` **从原有 2.5 MB 压缩证据恢复后直接发布**，不再耗时恢复 4.75 GB 原始容器。原有两包 `ai_influence` 解码日志保留；四包新日志写入独立 `lua-target-*.jsonl/json`。
- 定位依据：[[za-lua-native-targets|四份原生 Lua TRPFD Pack 位置]]。

| Pack | 原始虚拟文件 | 解出字节数 | SHA-256 |
| ---: | --- | ---: | --- |
| 12145 | `script/lua/bin/release/dll_util/dll_util.blua` | 16,479 | `cc77b9440afeef775baf29aeeae381c37458a38e2920e2a162b0679c4d1b8af2` |
| 12146 | `script/lua/bin/release/event_ik/event_ik.blua` | 7,666,228 | `f238160475095b02e8c5302d907adbd1b48b2fd793a4a8c72ee8c9689fdfd698` |
| 12147 | `script/lua/bin/release/main/main.blua` | 478,571 | `d9677f20ab3dfe350eec746d06769cf244bf316ee27fbd73a4bc208e5ff1b8a8` |
| 12148 | `script/lua/bin/release/main_dynamic/main_dynamic.blua` | 16,479 | `cc77b9440afeef775baf29aeeae381c37458a38e2920e2a162b0679c4d1b8af2` |

`dll_util` 与 `main_dynamic` 的完整 SHA-256 完全相同；这是字节事实，不据此猜测两个包的设计意图。四个文件有标准 Lua 5.4 头 `1B 4C 75 61 54 00 19 93 0D 0A 1A 0A`，并通过 `Lua54.parse()` 完整消费，无尾部多余数据。

## 2. 原生解码统计（来自已验证的四份 .blua）

| 类型 | event_ik | main | dll_util + main_dynamic | 合计 |
| --- | ---: | ---: | ---: | ---: |
| 原生 proto | 7,388 | 1,638 | 196 | **9,222** |
| 未命名 S/F/E Hash 常量出现 | 1,145 | 220 | 0 | **1,365** |
| 未命名 Hash 原生 opcode 引用 | 1,863 | 277 | 0 | **2,140** |
| 根原型 C→F 闭包 | 2,868 | 196 | 0 | **3,064** |
| 根原型 C→S 闭包 | 25 | 853 | 0 | **878** |

2,140 条真实指令引用的类型分布：**S 1,435、F 655、E 50**；去重以后有原生 opcode 使用的未知 Hash 分别为 **S 111/116、F 43/43、E 3/3**，总计 157/162。

主要原生指令操作包括 `GETFIELD`、`SELF`、`LOADK`、`GETTABUP`、`SETFIELD`、`SETTABUP`，而不是对二进制中的 64 位随机字节做模糊搜索。原生 `proto_id`、`parent_proto_id`、`pc`、`file_offset_hex`、`opcode`、`constant_index` 均单独保留以便回读。

**未命名 S 仍 116、F 43、E 3。** 五条 S 目前未取得上述受支持 opcode 引用；这不证明它们未被使用，可能属于未覆盖的数据流/动态引用情形。

## 3. 可复核产物

提取并发布后存放在 `Unpack/v2.0.2/romfs/arc/data.trpfs/`：

- `virtual/script/lua/bin/release/{dll_util,event_ik,main,main_dynamic}/*.blua`：四份原生文件，SHA-256 与本页逐一对应。
- `_index/lua-native/native-lua-summary.json`：四份 SHA/大小/头/Proto 数量及方法证据统计。
- `_index/lua-native/native-unknown-constants.tsv`：1,365 个原型常量。
- `_index/lua-native/native-unknown-opcode-references.tsv`：2,140 个确实读取目标常量索引的原生指令。
- `_index/lua-native/native-c-f-method-edges.tsv`：3,064 个 C→F 根原型闭包结构关系。
- `_index/lua-native/native-c-s-static-edges.tsv`：878 个 C→S 根原型闭包结构关系。
- `_index/lua-native/lua-target-publish-proof.json`：从原生 87 分卷来源至四个虚拟输出的固定 SHA 检查。
- `_index/lua-native/native-haxe-crosswalk.tsv`：由 `za-lua-native-crosswalk.yml` 把原生 opcode Hash 连接至重建 Haxe 的同一 Hash；保持原名未知。
- `_index/lua-native/native-unknown-direct-call-edges.tsv`：由 `za-lua-native-direct-calls.yml` 额外识别同一 Proto、**紧邻**的 `GETFIELD/GETTABUP/SELF` 字段加载与 `CALL/TAILCALL`，要求目标函数寄存器 `A` 完全相同，记录两条原生 PC/文件偏移。不跨越非紧邻代码推断调用链，也不证明 receiver class 或原始方法名。

现有原始 PokeDocs 与前期 611 个 `HASH_EXACT_CANDIDATE` 均不被原生分析器重写。

## 4. 本地复验

~~~powershell
# 在 ZA_Resources 仓库根目录；原始文件只读
py -3 .\scripts\Locate-ZA-Lua-Packs.py --verify-only
py -3 .\scripts\Analyze-ZA-Lua-Native.py --require-all
py -3 .\scripts\Analyze-ZA-Lua-DirectCalls.py
py -3 .\scripts\Crosswalk-ZA-Lua-Native.py

# 使用测试夹具，不依赖原始 ROM
py -3 -m unittest discover -s tests -p test_za_lua_native_pipeline.py -v
py -3 -m unittest discover -s tests -p test_za_lua_direct_calls.py -v
~~~

## 5. 下一轮原始命名恢复条件

1. 优先研究那些 **同时有原生 opcode 引用和重建调用位置**的 111 条 S，通过 `proto_id/pc` 确认实际读写/调用对象的原生来源。
2. 对 878 条根原型 C→S 静态闭包，继续追踪目标 child proto 的实际寄存器数据流，不能将相邻 C/S Hash 误当为完整原生方法名称。
3. 核实剩余 5 条 S 没有当前 opcodes 识别是否因 `GETTABLE/SETTABLE` 经过寄存器而遗漏，再核实是否来自表字段/全局标志引用。
4. **只有**拿到原名字符串的真实来源且完整 FNV-1a-64 校验一致时才将名称由 UNKNOWN 升级；原生 opcode/类关系只提高证据等级，不制造新名称。

相关文档：[[za-lua-native-targets]]、[ZA Lua 第四阶段重建源码证据](https://github.com/969981/SV_Resources/blob/master/docs/research/za-lua-native-evidence-gap.md)。
