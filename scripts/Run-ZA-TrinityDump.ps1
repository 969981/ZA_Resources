# ZA GFTool.Core dumper: descriptor index, dry-run, or bounded/full extraction.
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$Workspace,
 [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
 [string]$OutputRoot = '',
 [ValidateRange(0,2147483647)][int]$MaxPacks = 2,
 [ValidateRange(0,2147483647)][int]$StartPack = 0,
 [ValidateRange(0,2147483647)][int]$MaxFiles = 0,
 [switch]$DryRun,
 [switch]$DescriptorOnly,
 [switch]$IncludeUnused
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($RepositoryRoot)
$source = [IO.Path]::GetFullPath($Workspace).TrimEnd([char[]]@('\','/'))
if (-not $OutputRoot) { $OutputRoot = Join-Path $root 'Unpack\v2.0.2\romfs\arc\data.trpfs' }
$output = [IO.Path]::GetFullPath($OutputRoot)
if ($output -eq $source -or $output.StartsWith($source + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
 throw 'Output must be outside the original RomFS workspace'
}
$cache = Join-Path $root 'tools\_local\GFPAKHashCache.bin'
$oodle = Join-Path $root 'tools\_local\oo2core_8_win64.dll'
$project = Join-Path $root 'tools\ZA.TrinityDump\ZA.TrinityDump.csproj'
if (-not (Test-Path -LiteralPath $cache -PathType Leaf)) { throw 'Run Prepare-ZA-Trinity.ps1 first' }
if (-not $DryRun -and -not $DescriptorOnly -and -not (Test-Path -LiteralPath $oodle -PathType Leaf)) {
 throw 'Missing local Oodle library; supply via Prepare-ZA-Trinity.ps1 -OodleDllPath'
}
$dotnet = Get-Command dotnet -ErrorAction Stop
$argv = @('run','--project',$project,'-c','Release','--','--romfs',$source,'--output',$output,'--cache',$cache)
if ($DescriptorOnly) { $argv += '--descriptor-only' }
if ($DryRun) { $argv += '--dry-run' }
if ($IncludeUnused) { $argv += '--include-unused' }
if (Test-Path -LiteralPath $oodle -PathType Leaf) { $argv += @('--oodle',$oodle) }
if ($MaxPacks -gt 0) { $argv += @('--max-packs',"$MaxPacks") }
if ($StartPack -gt 0) { $argv += @('--start-pack',"$StartPack") }
if ($MaxFiles -gt 0) { $argv += @('--max-files',"$MaxFiles") }
& $dotnet.Source @argv
if ($LASTEXITCODE -ne 0) { throw "Trinity run failed ($LASTEXITCODE). Review _index/export.jsonl." }
