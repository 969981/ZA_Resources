[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$Version = 'v2.0.2',
    [string]$NcaDirectory = '4a70b3ff963bfe412681185cea68bf55_NCA',
    [Parameter(Mandatory = $true)][string]$DestinationRoot,
    [string]$SevenZip = ''
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
        throw "Unsafe relative path in manifest: $Relative"
    }
    $full = [System.IO.Path]::GetFullPath((Join-Path $Root ($Relative.Replace('/', [System.IO.Path]::DirectorySeparatorChar))))
    $prefix = $Root.TrimEnd([char[]]@('\','/')) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Manifest path escapes target directory: $Relative"
    }
    return $full
}
$repoRoot = (Resolve-Path -LiteralPath $RepositoryRoot).ProviderPath.TrimEnd([char[]]@('\','/'))
$manifestFile = Join-Path $repoRoot (Join-Path 'manifests' (Join-Path $Version 'transfer_manifest.json'))
if (-not (Test-Path -LiteralPath $manifestFile -PathType Leaf)) { throw "Manifest missing: $manifestFile" }
$manifest = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schemaVersion -ne 1 -or $manifest.version -cne $Version -or $manifest.ncaDirectory -cne $NcaDirectory) {
    throw 'Manifest schema, version or NCA mismatch.'
}
if (-not (Test-Path -LiteralPath $DestinationRoot)) {
    New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
}
$outRoot = (Resolve-Path -LiteralPath $DestinationRoot).ProviderPath.TrimEnd([char[]]@('\','/'))
$sevenZipExe = $null
$workRoot = Join-Path $repoRoot '.za-restore'
foreach ($record in @($manifest.files)) {
    $target = Join-Safe $outRoot ([string]$record.sourceRelativePath)
    $artifacts = @($record.artifacts)
    if ($artifacts.Count -eq 0) { throw "No artifacts for $($record.sourceRelativePath)" }
    $paths = @()
    foreach ($artifact in $artifacts) {
        $path = Join-Safe $repoRoot ([string]$artifact.path)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing artifact: $path" }
        $item = Get-Item -LiteralPath $path
        if ([long]$item.Length -ne [long]$artifact.sizeBytes -or (SHA256 $path) -ne [string]$artifact.sha256) {
            throw "Artifact size/hash mismatch: $path"
        }
        $paths += $path
    }
    if (Test-Path -LiteralPath $target -PathType Leaf) {
        if ((Get-Item -LiteralPath $target).Length -eq [long]$record.sourceSizeBytes -and
            (SHA256 $target) -eq [string]$record.sourceSha256) {
            Write-Host "SKIP verified $($record.sourceRelativePath)"
            continue
        }
        throw "Restored target already exists and differs; refusing overwrite: $target"
    }
    $targetDir = Split-Path -Parent $target
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    if ($record.representation -ceq 'original') {
        if ($paths.Count -ne 1) { throw 'Original representation must have exactly one artifact' }
        Copy-Item -LiteralPath $paths[0] -Destination $target
    } elseif ($record.representation -ceq '7z-volumes') {
        if ($paths[0] -notmatch '\.7z\.001$') { throw 'Archive must begin at .7z.001' }
        if (-not $sevenZipExe) { $sevenZipExe = Find-SevenZip $SevenZip }
        $stage = Join-Path $workRoot ([guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $stage -Force | Out-Null
        try {
            & $sevenZipExe x '-y' '-bd' $paths[0] ('-o' + $stage)
            if ($LASTEXITCODE -ne 0) { throw "7-Zip restore failed: $($record.sourceRelativePath)" }
            $baseName = [System.IO.Path]::GetFileName($target)
            $stageFile = Join-Path $stage $baseName
            if (-not (Test-Path -LiteralPath $stageFile -PathType Leaf)) {
                throw "Archive does not contain expected original filename: $baseName"
            }
            if ((Get-Item -LiteralPath $stageFile).Length -ne [long]$record.sourceSizeBytes -or
                (SHA256 $stageFile) -ne [string]$record.sourceSha256) {
                throw "Restored original SHA-256 differs from manifest: $($record.sourceRelativePath)"
            }
            Copy-Item -LiteralPath $stageFile -Destination $target
        } finally {
            Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
        }
    } else {
        throw "Unknown manifest representation: $($record.representation)"
    }
    if ((Get-Item -LiteralPath $target).Length -ne [long]$record.sourceSizeBytes -or
        (SHA256 $target) -ne [string]$record.sourceSha256) {
        throw "Final restored file differs from original: $($record.sourceRelativePath)"
    }
    Write-Host "OK restored $($record.sourceRelativePath)"
}
Write-Host "Restore complete: $outRoot"
