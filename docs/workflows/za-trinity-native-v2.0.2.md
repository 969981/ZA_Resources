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

## 从 SV M2 工作流移植的 ZA 全量模式（2026-11-05）

参照 SV 仓库的 `scripts/Run-SV-FullExtract.py` 与 `.github/workflows/sv-m2-full.yml`，ZA 使用 [Run-ZA-FullExtract.py](../../scripts/Run-ZA-FullExtract.py) 与 [za-m2-full.yml](../../.github/workflows/za-m2-full.yml) 进行持久化的批次解包。

| 阶段 | SV Violet 4.0.0 | ZA v2.0.2 |
| --- | ---: | ---: |
| TRPFD 原生资源包总数 | 23,589 | 13,181 |
| TRPFD 原生资源记录 | 408,641 | 238,546 |
| 原始 Trinity 分卷 | 83 | 87 |
| 每轮恢复 | 验证 TRPFD 和 TRPFS SHA-256 | 验证全部 87 个分卷、原始两个文件 SHA-256 |
| 导出 | GFTool.Core + Oodle | GFTool.Core + Oodle |
| 发布 | 分批输出、JSONL、检查点 | 分批输出、JSONL、检查点；独立 Git index 非强制推送 |

**已验证的原生测试**：2026-11-05 的 Windows Actions `42007205332` 原始数据恢复、Pack 0 和 Pack 1 的提取及文件 SHA-256 全部通过；2 个文件合计 122,072 字节。该任务最后只在执行 `git pull --rebase` 时因本地未暂存修改而失败，成功的原生数据通过 Actions 产物 `13405648302` 保存，并已由恢复任务 `42011556198` 重新验证后提交。

**发布错误修复**：不再调用有风险的 `git pull --rebase`，而是使用隔离的临时 Git Index，在远程 `master` 最新父提交上只加入本批已核对的生成文件，利用非强制推送提交；遇到并发修改或被拒绝的推送不覆盖用户修改。此方式有独立的无游戏数据 Git 仓库测试，已在 Actions 中通过。

**全量检查点与审核**：

- `_index/batches/pack-XXXXXX-XXXXXX.jsonl`：每批的真实解包行记录和失败信息；同名 JSON 为记录数、成功数、失败数、校验字节数
- `_index/full-extract-progress.json`：Pack 游标、最新已发布窗口、累计窗口数与 `PARTIAL/COMPLETE/REQUIRES_REPAIR` 状态
- `_index/full-extract-audit.json`：将最终状态与 `data.trpfd/file_index.tsv.gz` 所有 238,546 条原生 Hash 逐项比对，区分 OK、FAILED、UNSEEN
- 90 MiB 及以上生成文件写入 7z 分卷，并实际重新提取比对字节长度和 SHA-256 后再提交

每一个检查点只在该批生成文件经过本地哈希验证后写入 Git 远程；下一次 Windows 工作流使用已发布的 `nextPack` 优先于手动起点，避免跳包、误报全量完成。CI 可基于已经成功推送的 `PARTIAL` 游标调度下一窗口。全量是否完成必须以最终 `COMPLETE` 及审计结果为准。

工作流：[ZA M2 Full Actions](../../.github/workflows/za-m2-full.yml)；恢复工作流：[已验证的前两个包](../../.github/workflows/za-trpfs-recover.yml)。原来的一次性 Smoke Test 保留为手动运行，最后一步也已改为安全发布，避免自动重复恢复整个大归档。

### 本地按批使用

```powershell
# 在还原了原始 data.trpfd / data.trpfs 的 Windows 主机执行
# 注意：默认会将已核验的每批产物推送至 origin/master；预览可增加 --dry-run
python scripts/Run-ZA-FullExtract.py --repo . --workspace 'D:\ZA_Trinity_Workspace' --start-pack 0 --batch-packs 50 --max-batches 10 --time-budget-minutes 180 --seven-zip 'C:\Program Files\7-Zip\7z.exe'
```

注意：完整导出的数据量以及最终文件数仍可能受路径冲突、解析失败、Oodle 兼容性和 Git 文件大小上限影响；不要将索引记录直接算作已解出的实体文件。

## 一键全量模式（2026-11-05）

**入口：** `.github/workflows/za-m2-full.yml`，名称 `ZA M2 ONE-CLICK FULL`，默认 `full_run=true`。只需启动一次，后续 Windows Actions 运行通过已发布的 `nextPack` 检查点自动接力；不会重做已经成功提交的前 700 个 Pack。GitHub 托管运行器有单次时长和磁盘限制，因此“一键全量”指**一次启动、自动分轮完成同一个全量任务**，不是保证一台运行器单次处理 13,181 包。

- 每个验证窗口至少 100 Pack，每轮最多 100 个窗口；每轮仍有安全时间预算，在批次校验及 Git 非强制推送后停止。
- 后续运行由工作流自身通过 `gh workflow run ... full_run=true` 提交；`full_run=false` 可用于只执行指定范围、不自动接力。
- Windows 每轮重新核验 87 个 7z 分卷、`data.trpfd` 与 `data.trpfs` 的原始 SHA-256，运行 GFTool.Core + Oodle 原生解包。
- 各批次保留独立 JSONL、输出文件 SHA-256、超 90 MiB 的 7z 分卷往返校验与安全 Git 提交。
- **完成条件**：`full-extract-progress.json` 显示 `nextPack=13181`、`state=COMPLETE`，并且 `full-extract-audit.json` 的 `complete=true`、`failed=0`、`unseen=0`。若出现无法解码的文件、磁盘/平台配额错误或工作流被取消，则停止并保留最后检查点，不能称已全量完成。

首次一键模式 Git 提交：`2507422704193508cc7b311cbbb523794687b822`。启动运行及继续执行情况以 [GitHub Actions](../../.github/workflows/za-m2-full.yml) 和当前 master 检查点为准。

## 多进程加速（2026-11-05）

**优化涉及两条独立瓶颈**：

1. **Trinity/Oodle 解码**：`Run-ZA-FullExtract.py --parallel-workers 4`（默认四个进程，可设置 1..8）将一个连续的 Pack 窗口划成互不重叠的区间；各子进程有独立 `FileStream`、Oodle native runtime、虚拟输出目录、JSONL 和日志。聚合器验证每个 native Hash、原始 Pack 文件数、文件大小与 SHA-256，全部验收后才按原有路径合并。任何工作进程缺少 Hash、路径冲突或结果损坏均阻止进度完成。
2. **Git 发布**：以前逐文件调用 `git rev-parse` 会产生大量 Git 子进程。现在每次远程 `master` 检查用一次 `git ls-tree -r -z` 批量收集相关 Blob SHA，使用隔离 Git Index 在最新 `master` 上构造非强制提交；远程并发更新时最多重试十次，但同一路径被他人修改则直接拒绝覆盖。

入口是 `.github/workflows/za-m2-full.yml`；默认 **4 个独立 .NET 进程 × 200 Pack/批**，仍按窗口 SHA-256 验证、按原始版本完整审计，并继承上一次 `nextPack`。`parallel_workers=1` 是串行对照/排错模式。每批 JSON 汇总记录 `parallelWorkers`、`workerMetrics`、`decodeSeconds`、`validationAndArchiveSeconds`，可用真实运行结果判断 CPU、磁盘、Git 推送哪个占主要时间。

这是进程并行，Python ThreadPoolExecutor 仅用来同时等待多个独立的 .NET 子进程，并未在线程间共享 Oodle 的运行时状态。较大 Pack 将产生更多临时磁盘读写，进程数量并非越高越快。建议从 4 个进程开始，用 CI 结果度量加速比，不宣称线性四倍提速。

无游戏数据回归测试：`python -m unittest discover -s tests -p 'test_za_parallel.py' -v` 验证并发区间、原生记录对账、SHA-256、路径冲突；发布回归验证 Git 索引隔离、中文路径及批量 Blob 查询。
