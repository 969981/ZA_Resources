# Pin upstream tool source checkouts in ignored tools/_local; do not overwrite existing worktrees.
[CmdletBinding()]
param(
 [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
 [switch]$VerifyOnly,
 [switch]$IncludeOptional
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($RepositoryRoot)
$registry = Get-Content -LiteralPath (Join-Path $root 'tools\upstream.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($registry.schemaVersion -ne 1) { throw 'Unexpected registry schema' }
$null = Get-Command git -ErrorAction Stop
$local = Join-Path $root 'tools\_local'
if (-not $VerifyOnly) { New-Item -ItemType Directory -Path $local -Force | Out-Null }
foreach ($tool in $registry.sources) {
 if (-not $tool.required -and -not $IncludeOptional) { continue }
 $name = [string]$tool.name
 $rev = [string]$tool.ref
 if ($name -notmatch '^[A-Za-z0-9_.-]+$' -or $rev -notmatch '^[0-9a-f]{40}$') { throw "Invalid pin: $name" }
 $dir = Join-Path $local $name
 if (-not (Test-Path -LiteralPath (Join-Path $dir '.git'))) {
  if ($VerifyOnly) { throw "Missing tool: $dir" }
  if (Test-Path -LiteralPath $dir) { throw "Refusing to overwrite existing directory: $dir" }
  $cloneArgs = @('clone','--filter=blob:none','--no-checkout')
  if ($name -eq 'PokeDocs') { $cloneArgs += '--sparse' }
  $cloneArgs += @([string]$tool.repository,$dir)
  & git @cloneArgs
  if ($LASTEXITCODE -ne 0) { throw "Clone failed: $name" }
  if ($name -eq 'PokeDocs') {
   & git -C $dir sparse-checkout set --cone ZA/Hashlists/FileSystem
   if ($LASTEXITCODE -ne 0) { throw 'PokeDocs sparse init failed' }
  }
  & git -C $dir fetch --depth 1 origin $rev
  if ($LASTEXITCODE -ne 0) { throw "Fetch pinned commit failed: $name" }
  & git -C $dir checkout --detach $rev
  if ($LASTEXITCODE -ne 0) { throw "Checkout pinned commit failed: $name" }
 }
 $head = (& git -C $dir rev-parse HEAD).Trim()
 if ($LASTEXITCODE -ne 0 -or $head -cne $rev) { throw "Pinned mismatch: $name expected $rev actual $head" }
 & git -C $dir diff --quiet
 if ($LASTEXITCODE -ne 0) { throw "Working tree changed: $name" }
 & git -C $dir diff --cached --quiet
 if ($LASTEXITCODE -ne 0) { throw "Staged changes: $name" }
 if ($name -eq 'gftool' -and -not $VerifyOnly) {
  & git -C $dir submodule update --init --recursive
  if ($LASTEXITCODE -ne 0) { throw 'gftool nested dependency init failed' }
 }
 if ($name -eq 'PokeDocs') {
  if (-not (Test-Path -LiteralPath (Join-Path $dir 'ZA\Hashlists\FileSystem\hashes_inside_fd.txt') -PathType Leaf)) {
   throw 'ZA hash file not found in PokeDocs checkout'
  }
 }
 Write-Host "Verified pinned source $name $rev"
}
Write-Host 'Tool bootstrap only; no ZA game data extracted.'
