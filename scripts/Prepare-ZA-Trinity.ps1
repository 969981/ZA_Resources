# Reconstruct ZA originals and verify original hashes outside Git. Uses existing verified archive workflow.
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$Workspace,
 [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
 [string]$SevenZip = '',
 [string]$OodleDllPath = '',
 [switch]$IncludeTrpakHashes,
 [switch]$SkipRestore,
 [switch]$SkipHashBuild
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($RepositoryRoot).TrimEnd([char[]]@('\','/'))
$work = [IO.Path]::GetFullPath($Workspace).TrimEnd([char[]]@('\','/'))
if ($work -eq $root -or $work.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
 throw 'Workspace must be outside this repository'
}
$manifestPath = Join-Path $root 'manifests\v2.0.2\transfer_manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schemaVersion -ne 1 -or $manifest.version -ne 'v2.0.2') { throw 'Unexpected source manifest' }
New-Item -Path $work -ItemType Directory -Force | Out-Null
foreach ($relative in @('arc/data.trpfd','arc/data.trpfs')) {
 if (-not $SkipRestore) {
  $opts = @{RepositoryRoot=$root; DestinationRoot=$work; SourceRelativePath=$relative; ManifestJson=$manifestPath}
  if ($SevenZip) { $opts.SevenZip = $SevenZip }
  & (Join-Path $PSScriptRoot 'Restore-ZARomFS.ps1') @opts
  if (-not $?) { throw "Restore failed for $relative" }
 }
 $records = @($manifest.files | Where-Object { $_.sourceRelativePath -ceq $relative })
 if ($records.Count -ne 1) { throw "Missing or duplicate manifest source: $relative" }
 $inputFile = Join-Path $work $relative.Replace('/', [IO.Path]::DirectorySeparatorChar)
 if (-not (Test-Path -LiteralPath $inputFile -PathType Leaf)) { throw "Missing original: $inputFile" }
 $actual = (Get-FileHash -LiteralPath $inputFile -Algorithm SHA256).Hash.ToLowerInvariant()
 if ((Get-Item -LiteralPath $inputFile).Length -ne [long]$records[0].sourceSizeBytes -or $actual -cne [string]$records[0].sourceSha256) {
  throw "Restored size/SHA256 mismatch: $relative"
 }
 Write-Host "Verified original: $relative $actual"
}
$local = Join-Path $root 'tools\_local'
New-Item -Path $local -ItemType Directory -Force | Out-Null
$cache = Join-Path $local 'GFPAKHashCache.bin'
if (-not $SkipHashBuild) {
 $hashdir = Join-Path $local 'PokeDocs\ZA\Hashlists\FileSystem'
 $argsPython = @((Join-Path $PSScriptRoot 'Build-ZA-GFPAKHashCache.py'), '--hashlist', (Join-Path $hashdir 'hashes_inside_fd.txt'))
 if ($IncludeTrpakHashes) { $argsPython += @('--hashlist', (Join-Path $hashdir 'hashes_inside_trpak.txt')) }
 $argsPython += @('--output', $cache, '--overwrite', '--report', (Join-Path $local 'GFPAKHashCache.report.json'))
 $py = Get-Command python -ErrorAction Stop
 & $py.Source @argsPython
 if ($LASTEXITCODE -ne 0) { throw 'ZA GFPAK hash cache generation failed' }
}
if (-not (Test-Path -LiteralPath $cache -PathType Leaf) -or (Get-Item -LiteralPath $cache).Length -le 8) {
 throw 'Missing non-empty ZA GFPAKHashCache.bin'
}
if (-not $OodleDllPath) {
 $existing = Join-Path $root 'scripts\deps\oo2core_8_win64.dll'
 if (Test-Path -LiteralPath $existing -PathType Leaf) { $OodleDllPath = $existing }
}
if ($OodleDllPath) {
 $src = (Resolve-Path -LiteralPath $OodleDllPath -ErrorAction Stop).ProviderPath
 $dest = Join-Path $local 'oo2core_8_win64.dll'
 if ($src -cne $dest) { Copy-Item -LiteralPath $src -Destination $dest -Force }
 Write-Host ("Local-only Oodle SHA256: " + (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash)
}
Write-Host "Ready: verified RomFS $work; ZA hash cache $cache"
