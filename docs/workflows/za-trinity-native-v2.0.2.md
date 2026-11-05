# ZA v2.0.2 原生 Trinity TRPFD / TRPFS 解包

## 来源

原始数据路径：`v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/1/arc/`。

| 文件 | 原始字节数 | SHA-256 | 存储方式 |
| --- | ---: | --- | --- |
| data.trpfd | 9,877,520 | d1beb3763deab33691c5930e026006278f4586dac094f8d0ea2494ecb6f851f8 | 原始 Git 文件 |
| data.trpfs | 4,753,821,072 | 64169ef62030dd8e39bb884aff885fd51e7c0758c595c64c4b3fb7b6dad9683d | 87 个 7z 分卷，共 4,099,730,369 字节 |

校验标准为 `manifests/v2.0.2/transfer_manifest.json` 记录的全部分卷大小与 SHA-256、`7z t` 完整归档测试、还原后二次 SHA-256，不允许据文件名推断提取正确性。

## 已完成：TRPFD 实际解析

CI [ZA v2.0.2 TRPFD native index](../../.github/workflows/za-trpfd-index.yml) 使用已固定版本的 `tools/gftool/GFTool.Core` 从真实 data.trpfd 解出 `CustomFileDescriptor` FlatBuffer，再用 PokeDocs ZA Hash 缓存命名。结果：

- 资源 Hash / 文件记录：238,546
- Pack 数量：13,181
- 已有路径名：238,521
- 未知路径名：25
- 未引用记录：0

文件存放于 `Unpack/v2.0.2/romfs/arc/data.trpfs/_index/`：

- `descriptor_summary.json`：原始数据 SHA-256、数字统计、验证级别
- `file_index.tsv.gz`：每条原生 Hash、Pack 索引、Pack 名称、虚拟路径
- `pack_index.tsv`：每包名称、原始引用文件数、字节规模

这里的全部文件数量是 **索引记录数**，不代表 238,546 个实体文件已被真正写出。

## 还原与实际解压

独立的 [ZA v2.0.2 TRPFS workflow](../../.github/workflows/za-trpfs-unpack.yml) 在 Windows 上检出原始 87 分卷，运行 `scripts/Restore-ZA-TrinityDirect.py`；核验全部源 SHA-256 后使用 .NET Trinity 解析器检查 data.trpfs 内部索引并以本仓库自带的 Oodle DLL 解压原生资源包。

首轮使用 `--max-packs 2 --max-files 120` 进行真实字节提取、文件哈希复核及失败原因记录；该首轮是兼容性验证，不是宣称全量。文件分别存放在：

- `_index/trpfs-restore.json`：原始 87 个分卷和 2 个原生文件恢复验证依据
- `_index/export.jsonl`：每个 Hash 的 OK / FAILED、包名、偏移、字节数、SHA-256、异常类别
- `_index/batch_summary.json`：成功数、失败数、已核验字节数、失败类型汇总
- `virtual/<原生相对路径>`：真实从 Trinity 包导出的文件；未知 Hash 保留 `_unknown/<hash>.bin`

## 本地全量运行（Windows）

先预留充足空间：4.75 GB 原始 data.trpfs、归档分卷约 4.1 GB，以及尚未确定的全部解压后数据量。应当使用拥有足够空间的工作盘；不要在仓库中还原原始大文件。

~~~powershell
$root = (Get-Location).Path
$inputArc = Join-Path $root 'v2.0.2\4a70b3ff963bfe412681185cea68bf55_NCA\1\arc'
$work = 'D:\ZA_Trinity_Workspace'
$out = Join-Path $root 'Unpack\v2.0.2\romfs\arc\data.trpfs'
python scripts/Restore-ZA-TrinityDirect.py --manifest manifests/v2.0.2/transfer_manifest.json --archive-root $inputArc --workspace $work --sevenzip 'C:\Program Files\7-Zip\7z.exe' --evidence (Join-Path $out '_index\trpfs-restore.json')
.\scripts\Prepare-ZA-Trinity.ps1 -Workspace $work -SkipRestore -SkipHashBuild
.\scripts\Run-ZA-TrinityDump.ps1 -Workspace $work -DescriptorOnly
.\scripts\Run-ZA-TrinityDump.ps1 -Workspace $work -DryRun
.\scripts\Run-ZA-TrinityDump.ps1 -Workspace $work -MaxPacks 2 -MaxFiles 120
# 原生数据兼容性和磁盘容量均已核实后，开始 13,181 包全量导出
.\scripts\Run-ZA-TrinityDump.ps1 -Workspace $work -MaxPacks 0 -MaxFiles 0
python scripts/Summarize-ZA-Trinity.py --output $out --descriptor-summary (Join-Path $out '_index\descriptor_summary.json')
~~~

全量导出需要逐条复核输出及失败记录。大文件必须按仓库政策打包为小于 100,000,000 字节的分卷，不能直接提交到 GitHub。不得把 13,181 包都在索引中出现误写为已经成功解压。
