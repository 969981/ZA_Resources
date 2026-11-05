---
aliases:
  - ZA Lua 原生 Pack 四目标
tags: [pokemon-za, lua, trpfd, trpfs, native-evidence]
status: INDEX_VERIFIED_EXTRACTION_PENDING
---

# ZA 2.0.2：Lua 原生 Pack 定位、提取与证据链

> [!warning] 原生证据边界
> TRPFD 路径及包编号已证实，并不代表 TRPFS 解包或 Lua 解析已经成功。第三方 Haxe 占位符引用不是游戏原生 Lua。即使 Lua 字节码中有 opcode 常量引用，也不能直接填入尚未取得证据的原始符号名称。

## 1. TRPFD 本机索引发现

输入：Unpack/v2.0.2/romfs/arc/data.trpfs/_index/descriptor_summary.json、pack_index.tsv、file_index.tsv.gz。

- 原生 data.trpfd：9,877,520 bytes，SHA-256 D1BEB3763DEAB33691C5930E026006278F4586DAC094F8D0EA2494ECB6F851F8。
- 原生索引：238,546 文件、13,181 包，238,521 个名称匹配，25 个虚拟路径未知。
- 四个 Pack 连续且均引用一个文件，打包大小相加 1,463,128 bytes，并非 Lua 解码后大小。

| Pack | TRPAK 原生路径 | 打包大小 |
| ---: | --- | ---: |
| 12145 | arc/scriptluabinreleasedll_utildll_util.blua.trpak | 7,400 |
| 12146 | arc/scriptluabinreleaseevent_ikevent_ik.blua.trpak | 1,325,888 |
| 12147 | arc/scriptluabinreleasemainmain.blua.trpak | 122,440 |
| 12148 | arc/scriptluabinreleasemain_dynamicmain_dynamic.blua.trpak | 7,400 |

运行 scripts/Locate-ZA-Lua-Packs.py 将从完整 gzip 文件索引反查四份实际虚拟路径和原始文件 Hash；结果放到同目录 lua_pack_locations.json。必须四个唯一命中且 ID/原生包路径都与表格完全一致；不依据 Haxe 重新猜测。

## 2. 再做四包定向解码

已有原始恢复脚本 Restore-ZA-TrinityDirect.py（校验 87 卷尺寸/SHA-256、7z t、恢复的两份原始 Trinity 文件 SHA-256）。工具 ZA.TrinityDump 可用下列命令解压四个包：

~~~powershell
py -3 .\scripts\Locate-ZA-Lua-Packs.py
py -3 .\scripts\Locate-ZA-Lua-Packs.py --verify-only
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-ZA-TrinityDump.ps1 -Workspace 'D:\ZA_Trinity_Workspace' -StartPack 12145 -MaxPacks 4 -MaxFiles 4
py -3 .\scripts\Analyze-ZA-Lua-Native.py --require-all
~~~

注意现有 ZA.TrinityDump 的 --start-pack 是有引用包的遍历序号，不是原生 Pack ID 的通用定位器。针对本版本，完整 pack_index.tsv 的 13,181 个编号连续、没有无引用包，此处两者数值相同。任何版本漂移必须中止。

## 3. 原生 Lua 的分析产物

- scripts/_vendor/Analyze-SV-Lua54.py：从用户已有 SV_Resources 的 Lua 5.4 读取逻辑复制；仅代码复用，不复用 SV 的游戏 SHA/数值或验证结论。
- scripts/Analyze-ZA-Lua-Native.py：读取四份实际原生 ZA 虚拟文件，记录完整 SHA-256、Lua 5.4 Header、子 prototype 数量、常量、源 PC/文件偏移和读取常量的实际 opcode。
- native-unknown-constants.tsv：游戏原生 Lua 常量池中确实出现的剩余 S/F/E Hash 字符串。常量存在不证明被调用。
- native-unknown-opcode-references.tsv：指令真实使用该常量索引，记录原型、PC、字节偏移、指令。
- native-c-f-method-edges.tsv 和 native-c-s-static-edges.tsv：匹配严格的原生闭包赋值指令序列。不能把 C→S 直接误称为完整业务调用链。
- native-lua-summary.json：四份 SHA-256、状态与计数，尚不确定的符号保留未知。

分析目标取自用户既有 SV_Resources 第四轮提交 83e4959 的 unresolved-symbol-index.tsv：S 116、F 43、E 3。**原始命名补全仍维持 611 条，新增值不得无依据地写回原版 PokeDocs**。

## 4. 已知恢复工作流问题

2026-11-05 的 ZA Trinity smoke 工作流已验证 87 个归档分卷、4.75 GB TRPFS、原生 C# 解析器，以及首两个资源包的实际解码与校验。最后 Git 发布因先 git pull --rebase 再 git add 而失败：出现 cannot pull with rebase: You have unstaged changes。这是发布顺序故障，不是原始数据无法解包。新工作流应先 stage/commit 结果，再 fetch/rebase/push，且失败时保留 Actions artifact 供检查。

## 5. 证据等级

- CONFIRMED_NATIVE_TRPFD_INDEX：文件路径、包索引等元数据，非 Lua 字节码。
- VERIFIED_EXTRACTED_FILE_BYTES：实际虚拟资源长度与 SHA-256 回读成功。
- NATIVE_LUA54_CONSTANT_PRESENT_ONLY：原型常量池中存在目标 Hash，不等于使用。
- NATIVE_LUA54_OPCODE_CONSTANT_REFERENCE：常量索引确实被原生字节码指令使用。
- NATIVE_ROOT_CLASS_S_CLOSURE_ASSIGNMENT：严格根原型赋值序列，可用于建立 C→S 静态方法关联。
- CONFIRMED_NATIVE_SYMBOL_NAME：需要进一步原始字符串或其他严格的原生名称证据；前述任何一条并不自动达到这个级别。
