---
title: "ZA v2.0.2 从原生资源到 JSON"
tags: [ZA, extraction, flatbuffers]
---
# 从 TRPFS 到 JSON

## 一、直接使用已导出的数据

仓库已提供 `Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/`。无需为了提取图鉴和遭遇就重做 4.75GB 原始 TRPFS 全量还原。

在 Windows PowerShell 7+ 中，安装新版 [flatc](https://flatbuffers.dev/flatc/)，对一对真实 `.bfbs + .bin` 执行：

```powershell
$root = "Unpack/v2.0.2/romfs/arc/data.trpfs/virtual"
$pair = Join-Path $root "world/ik_data/field/pokemon/encount_data/encount_data"
New-Item -ItemType Directory -Force ".za-work/json/encounter" | Out-Null
flatc --json --raw-binary --strict-json -o ".za-work/json/encounter" `
  (Join-Path $pair "encount_data_array.bfbs") -- `
  (Join-Path $pair "encount_data_array.bin")
```

`flatc` 支持 `.fbs` 和新版本的 `.bfbs` 二进制 schema；`--raw-binary` 用于可能没有 identifier 的数据。可用 `flatc --annotate SCHEMA -- DATA` 检查字段的实际字节区域。**以上是执行模板，本轮没有把它声称为已跑通的真实 2.0.2 解析结果。**

## 二、批量处理全部 schema 对

保留相对目录避免同名文件冲突，失败写审计文件：

```powershell
$root = (Resolve-Path "Unpack/v2.0.2/romfs/arc/data.trpfs/virtual").Path
$out = Join-Path (Get-Location) ".za-work/za-json"
$failed = [Collections.Generic.List[object]]::new()
Get-ChildItem -Path $root -Filter "*.bfbs" -File -Recurse | ForEach-Object {
  $bin = [IO.Path]::ChangeExtension($_.FullName, ".bin")
  if (-not (Test-Path $bin)) { return }
  $relative = [IO.Path]::GetRelativePath($root, $_.DirectoryName)
  $target = Join-Path $out $relative
  New-Item -ItemType Directory -Force $target | Out-Null
  & flatc --json --raw-binary --strict-json -o $target $_.FullName -- $bin
  if ($LASTEXITCODE -ne 0) {
    $failed.Add([pscustomobject]@{Schema=$_.FullName;Binary=$bin;ExitCode=$LASTEXITCODE})
  }
}
$failed | Export-Csv ".za-work/za-json-failed.csv" -NoTypeInformation -Encoding UTF8
```

## 三、没有 schema 的 BIN

`world/exl/item_data/item_data/item_data.bin`、`world/exl/pokedex_contents_data/...` 没有在相邻目录确认配套 `.bfbs`：先查 `tools/PokeDocs/ZA/Flatbuffers`、`tools/gftool`、`tools/pkNX`；再分析文件头、长度、表偏移和 ExeFS 读取调用；最后以多份真实样本验证自建 schema。不能仅重命名后缀或拿不匹配的 schema 强行解码。

## 四、多语言 DAT/TBL

`scripts/Convert-ZA-Virtual.py` 已针对单 section 的加密 UTF-16 DAT 实现经过样例验证的解密，`.tbl` 为 AHTB key/hash/name 表：

```powershell
python scripts/Convert-ZA-Virtual.py --repo . --category ik_message --workers 4 --seven-zip 7z
python scripts/Audit-ZA-VirtualConversion.py --repo .
```

DAT 字串数量不一定等于 TBL 表项数量（`bag.dat` 与 `bag.tbl` 已有差异），**不要按数组位置硬拼 key→文本**。保留 `language,filename,index,keyHash,decodedUtf16,controls,sourceSha256`。区分 `CONVERTED`、`STRUCTURE_ONLY`、`UNSUPPORTED` 和 `FAILED`。

## 五、重新原生解包的必要条件

`tools/ZA.TrinityDump`、`scripts/Run-ZA-FullExtract.py` 和 `.github/workflows/za-m2-full.yml` 可做原生提取。**FullExtract 可能向 master 自动提交推送**；做研究笔记优先复用 `virtual/`，需要原生补档时先检查 [原生流程](https://github.com/969981/ZA_Resources/blob/master/docs/workflows/za-trinity-native-v2.0.2.md)、验证 TRPFD/TRPFS SHA-256 并检查 `_index` 状态。
