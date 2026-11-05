# Verify complete pinned third-party sources already committed under tools/.
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
if ($registry.schemaVersion -ne 2 -or $registry.sourceTracking -ne 'vendor-only') { throw 'Unexpected tool registry' }
$null = Get-Command git -ErrorAction Stop
foreach ($tool in @($registry.sources) + @($registry.extraZA)) {
 $name = [string]$tool.name
 $path = if ($tool.PSObject.Properties['path']) { [string]$tool.path } else { "tools/$name" }
 if (-not $path.StartsWith('tools/', [StringComparison]::Ordinal) -or $path -match '(^|/)\.\.?(/|$)') {
  throw "Unsafe source directory: $path"
 }
 $expected = [string]$tool.sourceTreeSha
 if ($expected -notmatch '^[0-9a-f]{40}$') { throw "Invalid tree SHA for $path" }
 $full = Join-Path $root $path.Replace('/', [IO.Path]::DirectorySeparatorChar)
 if (-not (Test-Path -LiteralPath $full -PathType Container)) { throw "Missing vendored source directory: $full" }
 $actual = (& git -C $root rev-parse "HEAD:$path").Trim()
 if ($LASTEXITCODE -ne 0 -or $actual -cne $expected) { throw "Pinned tree mismatch: $path expected=$expected actual=$actual" }
 $gitlinks = @(& git -C $root ls-files --stage -- $path | Where-Object { $_ -match '^160000 ' })
 if ($gitlinks.Count -gt 0) { throw "Gitlink detected under $path" }
 if ($name -eq 'gftool' -and -not (Test-Path -LiteralPath (Join-Path $full 'NxMiddleware') -PathType Container)) {
  throw 'Nested NxMiddleware missing from gftool'
 }
 if ($name -eq 'PokeDocs' -and -not (Test-Path -LiteralPath (Join-Path $full 'ZA\Hashlists\FileSystem\hashes_inside_fd.txt') -PathType Leaf)) {
  throw 'ZA file hash dictionary missing'
 }
 Write-Host "Verified pinned vendor tree: $path $actual"
}
Write-Host 'All vendor sources are committed locally. No network download or extraction needed.'
