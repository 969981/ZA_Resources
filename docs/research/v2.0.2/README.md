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
