[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$Version = 'v2.0.2',
    [string]$NcaDirectory = '4a70b3ff963bfe412681185cea68bf55_NCA',
    [string]$SevenZip = '',
    [switch]$Full
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Find-SevenZip([string]$Requested) {
    $names = @()
    if ($Requested) { $names += $Requested }
    $names += @('7z', '7za', 'D:\Tool\7-Zip\7z.exe')
    if ($env:ProgramFiles) { $names += (Join-Path $env:ProgramFiles '7-Zip\7z.exe') }
    foreach ($name in $names) {
        if (Test-Path -LiteralPath $name -PathType Leaf) { return (Resolve-Path -LiteralPath $name).ProviderPath }
        $cmd = Get-Command -Name $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    throw '7-Zip not found. Supply -SevenZip or put 7z on PATH.'
}
function SHA256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Join-Safe([string]$Root, [string]$Relative) {
    if ([string]::IsNullOrWhiteSpace($Relative) -or [System.IO.Path]::IsPathRooted($Relative) -or
        $Relative.Contains('\') -or $Relative -match '(^|/)\.\.?(/|$)' -or $Relative.StartsWith('/')) {
        throw "Unsafe relative path: $Relative"
    }
    $full = [System.IO.Path]::GetFullPath((Join-Path $Root ($Relative.Replace('/', [System.IO.Path]::DirectorySeparatorChar))))
    $prefix = $Root.TrimEnd([char[]]@('\','/')) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Path escapes repo: $Relative" }
    return $full
}
$repoRoot = (Resolve-Path -LiteralPath $RepositoryRoot).ProviderPath.TrimEnd([char[]]@('\','/'))
$manifestFile = Join-Path $repoRoot (Join-Path 'manifests' (Join-Path $Version 'transfer_manifest.json'))
if (-not (Test-Path -LiteralPath $manifestFile -PathType Leaf)) { throw "Manifest missing: $manifestFile" }
$manifest = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schemaVersion -ne 1 -or $manifest.version -cne $Version -or $manifest.ncaDirectory -cne $NcaDirectory) {
    throw 'Manifest schema, version or NCA mismatch.'
}
$sevenZipExe = $null
$verified = 0
$archiveCount = 0
foreach ($record in @($manifest.files)) {
    $arts = @($record.artifacts)
    if ($arts.Count -lt 1) { throw "No artifacts for $($record.sourceRelativePath)" }
    $parts = @()
    foreach ($art in $arts) {
        $path = Join-Safe $repoRoot ([string]$art.path)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Artifact missing: $path" }
        if ((Get-Item -LiteralPath $path).Length -ne [long]$art.sizeBytes -or
            (SHA256 $path) -ne [string]$art.sha256) {
            throw "Size or SHA256 mismatch: $path"
        }
        $parts += $path
    }
    if ($record.representation -ceq '7z-volumes') {
        if (-not $sevenZipExe) { $sevenZipExe = Find-SevenZip $SevenZip }
        $baseName = [System.IO.Path]::GetFileName([string]$record.sourceRelativePath)
        for ($i=0; $i -lt $arts.Count; $i++) {
            $expected = $baseName + '.7z.' + ('{0:D3}' -f ($i + 1))
            if ([System.IO.Path]::GetFileName($parts[$i]) -cne $expected) {
                throw "Incorrect/missing archive volume order: expected $expected"
            }
        }
        & $sevenZipExe t '-bd' $parts[0]
        if ($LASTEXITCODE -ne 0) { throw "7z t failed: $($record.sourceRelativePath)" }
        $archiveCount++
    } elseif ($record.representation -ceq 'original') {
        if ($parts.Count -ne 1 -or (SHA256 $parts[0]) -ne [string]$record.sourceSha256) {
            throw "Copied original differs from source SHA256: $($record.sourceRelativePath)"
        }
    } else {
        throw "Unsupported representation: $($record.representation)"
    }
    $verified++
    Write-Host "OK verified $($record.sourceRelativePath)"
}
if ($Full) {
    $fullStage = Join-Path $repoRoot (Join-Path '.za-restore' ([guid]::NewGuid().ToString('N')))
    New-Item -ItemType Directory -Path $fullStage -Force | Out-Null
    try {
        & (Join-Path $PSScriptRoot 'Restore-ZAResources.ps1') -RepositoryRoot $repoRoot -Version $Version -NcaDirectory $NcaDirectory -SevenZip $SevenZip -DestinationRoot $fullStage
        if (-not $?) { throw 'Full restore verification failed.' }
    } finally {
        Remove-Item -LiteralPath $fullStage -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host 'Full restore/source SHA256 comparison passed.'
}
Write-Host ("PASS: {0} files, {1} multi-volume 7z files; full restore: {2}" -f $verified, $archiveCount, [bool]$Full)
