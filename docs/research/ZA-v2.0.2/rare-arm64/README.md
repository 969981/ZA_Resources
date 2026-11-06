# ZA v2.0.2 ELF ARM64 只读扫描结果

> 这些是实际 AArch64 指令、BFBS 字段和直接 BL 交叉引用，但不是已经定位的锁闪分支。

- Build ID：b1f12fd919eae86ab8a978317677e64bce443d1f000000000000000000000000
- SHA-256：470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d
- .text：main+0xE1D664 到 main+0x31605E0；36,974,460 bytes
- UBFM/LSR 高 4 位提取候选：106

## 真实 BFBS rare 字段

- ik.fb.wild_pokemon.EncountData.rare：field ID 6，vtable slot offset 16；该值不是运行时地址。

## 公开 Getter/Setter 的直接 BL 计数

| 入口 RVA | 直接 BL 次数 |
|---|---:|
| PID_Get main+0xE4DBE0 | 4 |
| PID_Set main+0xE57350 | 1 |
| TID_Get main+0xE49D50 | 6 |
| Species_Get main+0xE49940 | 75 |
| IV_Get_HP main+0xE4BCF0 | 3 |
| Personal_Load main+0xE380C0 | 1 |
| Shiny_CheckCandidate main+0xE5D1E8 | 1 |
| Shiny_ModeClassifierCandidate main+0xE5D244 | 1 |
| Shiny_ModeSetterCandidate main+0xE46024 | 0 |
| Shiny_ModeCheckCandidate main+0xE45F7C | 0 |
| PID_ToShinyCandidate main+0xE5D21C | 1 |
| PID_ModeAdjustCandidate main+0xE5D284 | 1 |

## 虚函数包装器的 ELF 指针交叉引用

- 找到 2 处与目标包装器/函数 RVA 相同的 64-bit 字面指针。
- 详细位置：shiny-function-pointer-xrefs.csv 与 shiny-wrapper-pointer-map.json。
- 这些不能取代运行时追踪，仍需验证上层间接 BLR 的来源。


## ARM64 B 尾调用与高位测试

- 直接 B 尾调用 PID_Set：2 个。
- TBZ/TBNZ 检查 28–31 高位：8083 处。
- 已导出 pid-tail-branches.csv、rare-highbit-tests.csv 与 pid-shiny-function-windows.md。


## 优先进一步人工核对的高位候选

| 指令 RVA | 分数（启发式） | 最近 PID Set BL 距离 |
|---|---:|---:|
| main+0x114099C | 10 | 3153396 |
| main+0x1AD364C | 10 | 13191844 |
| main+0x2056850 | 10 | 18971816 |
| main+0x2139E44 | 10 | 19903132 |
| main+0x213A590 | 10 | 19905000 |
| main+0x2163CC8 | 10 | 20074784 |
| main+0x2163CD4 | 10 | 20074796 |
| main+0x21646F0 | 10 | 20077384 |
| main+0x225A4CC | 10 | 21084452 |
| main+0x225D2C8 | 10 | 21096224 |
| main+0x226CE1C | 10 | 21160564 |
| main+0x2E85DFC | 10 | 33845844 |
| main+0x2E883D0 | 10 | 33855528 |
| main+0x2E885F8 | 10 | 33856080 |
| main+0x2E89164 | 10 | 33859004 |
| main+0x2E893A0 | 10 | 33859576 |
| main+0x2E8C714 | 10 | 33872748 |
| main+0x2E8EB4C | 10 | 33882020 |
| main+0x3043F70 | 10 | 35673032 |
| main+0x3044038 | 10 | 35673232 |

## 不可跳过的证据门槛

1. 在正确 Build ID 的运行实例里证明某处寄存器值确实来自 Encounter.rare。
2. 对 0x1FFFFFFF、0x2FFFFFFF、0x3FFFFFFF 复测该函数第一处分歧分支。
3. 从该分支追踪真实 PID Setter、TID/SID、最终异色 XOR 和重抽路径。
4. 把完整调用栈、汇编、寄存器、实例类型与反例保留为可核查日志。

同目录有 pid-direct-callers.csv、shift28-candidates.csv、static-audit.json。
无动态 trace 之前，shinyLockBranchRva 仍为 null。
