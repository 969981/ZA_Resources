---
title: ZA v2.0.2 主程序地址与运行时证据
tags: [ZA, ExeFS, Ghidra, AArch64, address]
---
# ExeFS 地址定位及动态核验

## 版本证据

仓库 `Unpack/v2.0.2/exefs/exefs-manifest.json` 中 `main` 的 Build ID：

`b1f12fd919eae86ab8a978317677e64bce443d1f000000000000000000000000`

- `Unpack/v2.0.2/exefs/main/main.elf`：66,579,944 字节，SHA256 `470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d`。
- `Unpack/v2.0.2/exefs/main/main.uncompressed.nso`：解压后的 NSO。
- `Unpack/v2.0.2/exefs/main/provenance.json`：来源与转换元数据。

## 四种不要混淆的定位

| 概念 | 表示 |
| --- | --- |
| 资源路径 | `virtual/world/.../encount_data_array.bin` |
| 文件内偏移 | `file+0x...` |
| 程序镜像 RVA | `main+0x...` |
| 进程绝对地址 | `loadedMainBase + RVA` |
| 游戏地图地点 | `sceneId + (x,y,z)` |

ELF 虚拟地址、NSO 压缩文件偏移和进程绝对 VA 不一定相同；内存 ASLR 变化后需重新取得模块基址。

## 静态定位与断点

1. 在 Ghidra/IDA 中载入 `main.elf`，核对 ELF 段映射、地址基准和 Build ID。
2. 从 `encount_data`、`pokemon_spawner`、`trdata` 等经证实的字段/资源读取者找到函数 xref，继续追踪对象创建、level、PID、IV、EC、shiny 判定和最终保存。
3. 记录函数 `RVA`、所在段、调用者、被调用者、关联字段和资源来源。
4. 在相同 Build ID 的游戏/模拟器上核对 PC、LR、寄存器、参数和真实内存数据，至少普通野生与剧情固定分别复核。
5. 使用仓库现有 `docs/research/v2.0.2/` Lua 调用证据链研究辅助事件路径，不能把 Hash 相似性当作原生调用签名。

## 外部资料边界

[Decryptu/pokeldn ZA 逆向笔记](https://decryptu.github.io/pokeldn/za.html) 有主程序/Pokemon 结构交叉线索，但**不等同于本知识库已在 v2.0.2 复现的偏移表**。须逐条核对主程序 SHA、Build ID、镜像映射和断点结果。

目标 `address_index.csv`：
`version,buildId,module,rva,elfVa,fileOffset,loadedBase,runtimeVa,description,caller,callee,sourcePath,instruction,proof,evidence`。未知地址保留 UNKNOWN，不跨版本复用。
