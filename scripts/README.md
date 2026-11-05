# Local processing tools

The v2.0.2 RomFS scripts support Windows PowerShell 5.1 and PowerShell 7. They use Windows-native file operations and 7-Zip. Pass explicit source, target and repository paths.

- Archive-ZARomFS.ps1 — scan, copy or compress, verify outputs and update the CSV and JSON manifests. Supports -Resume and -VerifyOnly.
- Verify-ZARomFS.ps1 — rescan the source and perform a full artifact audit, including 7z test and restored SHA-256 comparison.
- Restore-ZARomFS.ps1 — restore one source-relative file, the complete RomFS tree, or directly from a .7z.001 file.
- Archive-ZARomFS.Smoke.ps1 — synthetic regression check using temporary files and 1 MiB volumes.

See [v2.0.2 RomFS archive and recovery](../docs/romfs-v2.0.2-archive.md) for commands and safety behavior.

## Internal resource extraction

See [tools](../tools/README.md) and [ZA extraction workflow](../docs/workflows/za-trinity-extraction.md). Run Sync-ZA-Tools.ps1 to verify the six committed pinned source snapshots; Prepare-ZA-Trinity.ps1 to restore verified original files; Run-ZA-TrinityDump.ps1 to index/extract, and Convert-ZA-ExeFS.py for NSO-to-ELF.

## 原生 Upvalue 捕获链（ZA v2.0.2）

- `Trace-ZA-Lua-Upvalue-Captures.py`：解析 Lua 5.4 `instack/idx/kind` 三字节 Upvalue 描述符，逐级对账 `CLOSURE Bx` 与父 Prototype；核对 926 条已确认原生静态 C 类键查找以及 7＋20 条缺乏直接闭包归属的 CALL。输出为小型 TSV/JSON。
- `py -3 -m unittest discover -s tests -p test_za_lua_upvalue_captures.py -v`
- `py -3 scripts/Trace-ZA-Lua-Upvalue-Captures.py --max-window 16`
- CI：`.github/workflows/za-lua-upvalue-captures.yml`。**根 Chunk 外部 Upvalue 不等于运行时接收类或已证明的 `_ENV`。**

## 原生闭包与 receiver 源头追踪（ZA v2.0.2）

- `Join-ZA-Lua-Closure-Callers.py`：以 source+child_proto_id 关联 1,488 条局部 CALL 与 C→F/C→S 闭包；上溯 parent Proto，记录有界 SELF/GETTABLE/GETFIELD 接收寄存器来源。并不宣称 runtime receiver class 已证实。
- `Audit-ZA-Lua-PackCoverage.py`：验证完整 13,181 个 Trinity 包中的 `.blua.trpak` 只有四个，并独立比较原始 162 个 unresolved S/F/E Hash 与四份原生常量池的 157 个命中。
- `py -3 scripts/Join-ZA-Lua-Closure-Callers.py --window 16`；`py -3 scripts/Audit-ZA-Lua-PackCoverage.py`。
- CI：`.github/workflows/za-lua-closure-callers.yml`，通过原生四包 SHA-256 和合成测试后才发布索引 TSV/JSON。

## 原生 ZA Lua 四个包的证据发布与局部调用链

- `Publish-ZA-LuaArtifact.py`：从成功的 [Actions run 42011668436](https://github.com/969981/ZA_Resources/actions/runs/42011668436) Artifact 13407204049 校验、保留并发布 4 份真实 `.blua`、原生常量/指令 TSV；没有重复执行 4.75 GB 原始 Trinity 还原。独立 Actions `za-lua-native-artifact-publish.yml` 会校验所有 SHA-256 再提交。
- `Analyze-ZA-Lua-DirectCalls.py`：仅在 `GETFIELD/GETTABUP/SELF(k=1)` 后紧邻 `CALL/TAILCALL` 且调用寄存器相同时记录局部原生证据；不猜测原始名称或跨基本块数据流。
- [Obsidian 研究与原生证据等级](../docs/research/v2.0.2/za-lua-native-opcode-evidence.md)
