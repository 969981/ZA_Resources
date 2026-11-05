[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceRomfsRoot,
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$Version = 'v2.0.2',
    [string]$NcaDirectory = '4a70b3ff963bfe412681185cea68bf55_NCA',
    [string]$SevenZip = '',
    [ValidateRange(1,90)][int]$VolumeMiB = 90,
    [ValidateRange(1,90)][int]$ThresholdMiB = 90,
    [ValidateRange(0,9)][int]$CompressionLevel = 1
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
    throw '7-Zip not found. Supply -SevenZip "D:\Tool\7-Zip\7z.exe" or install 7z on PATH.'
}
function SHA256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function RelativeToRepo([string]$FullPath) {
    return $FullPath.Substring($repoRoot.Length + 1).Replace('\', '/')
}
function Add-Artifact([string]$FullPath) {
    $item = Get-Item -LiteralPath $FullPath
    return [ordered]@{
        path = (RelativeToRepo $item.FullName)
        sizeBytes = [long]$item.Length
        sha256 = (SHA256 $item.FullName)
    }
}
function Assert-Exit([string]$Action, [int]$Code) {
    if ($Code -ne 0) { throw "$Action failed, 7-Zip exit code $Code" }
}
function ExistingVolumes([string]$Directory, [string]$BaseName) {
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) { return @() }
    $prefix = [regex]::Escape($BaseName + '.7z.')
    return @(Get-ChildItem -LiteralPath $Directory -File |
        Where-Object { $_.Name -match ('^' + $prefix + '[0-9]{3,}$') } |
        Sort-Object Name)
}
function Assert-Volumes([object[]]$Volumes, [string]$BaseName) {
    if ($Volumes.Count -eq 0) { throw "Missing archive volumes for $BaseName" }
    for ($i = 0; $i -lt $Volumes.Count; $i++) {
        $expected = $BaseName + '.7z.' + ('{0:D3}' -f ($i + 1))
        if ($Volumes[$i].Name -cne $expected) {
            throw "Non-contiguous archive volumes: expected $expected, got $($Volumes[$i].Name)"
        }
        if ($Volumes[$i].Length -ge 100000000) { throw "Volume exceeds GitHub 100 MB limit: $expected" }
    }
}
if ($Version -notmatch '^v[0-9]+\.[0-9]+\.[0-9]+$') { throw 'Version must look like v2.0.2' }
if ($NcaDirectory -notmatch '^[0-9a-fA-F]{32}_NCA$') { throw 'NcaDirectory must be 32 hex characters followed by _NCA' }
$sourceRoot = (Resolve-Path -LiteralPath $SourceRomfsRoot).ProviderPath.TrimEnd([char[]]@('\','/'))
$repoRoot = (Resolve-Path -LiteralPath $RepositoryRoot).ProviderPath.TrimEnd([char[]]@('\','/'))
$destRoot = Join-Path $repoRoot (Join-Path $Version (Join-Path $NcaDirectory '1'))
$destFull = [System.IO.Path]::GetFullPath($destRoot)
$sourcePrefix = $sourceRoot + [System.IO.Path]::DirectorySeparatorChar
if ($destFull.Equals($sourceRoot, [StringComparison]::OrdinalIgnoreCase) -or
    $destFull.StartsWith($sourcePrefix, [StringComparison]::OrdinalIgnoreCase) -or
    $sourceRoot.StartsWith(($destFull + [System.IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'SourceRomfsRoot cannot contain the destination RomFS tree. Use separate input and repository folders.'
}
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot 'AGENTS.md'))) {
    Write-Warning 'RepositoryRoot does not contain AGENTS.md; confirm this is the ZA_Resources clone.'
}
$files = @(Get-ChildItem -LiteralPath $sourceRoot -File -Recurse | Sort-Object FullName)
if ($files.Count -eq 0) { throw 'SourceRomfsRoot contains no files.' }
$thresholdBytes = [long]$ThresholdMiB * 1MB
$workRoot = Join-Path $repoRoot '.za-work'
New-Item -ItemType Directory -Force -Path $workRoot | Out-Null
$sevenZipExe = $null
$entries = New-Object System.Collections.Generic.List[object]
try {
    foreach ($file in $files) {
        $rel = $file.FullName.Substring($sourcePrefix.Length).Replace('\', '/')
        $target = Join-Path $destRoot ($rel.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
        $targetDir = Split-Path -Parent $target
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        $originalHash = SHA256 $file.FullName
        $representation = 'original'
        $artifacts = @()
        if ([long]$file.Length -le $thresholdBytes) {
            if (Test-Path -LiteralPath $target -PathType Leaf) {
                if ((Get-Item -LiteralPath $target).Length -ne $file.Length -or (SHA256 $target) -ne $originalHash) {
                    throw "Existing file differs from source; refusing overwrite: $target"
                }
            } else {
                Copy-Item -LiteralPath $file.FullName -Destination $target
                if ((SHA256 $target) -ne $originalHash) { throw "Copy hash mismatch: $rel" }
            }
            $artifacts = @((Add-Artifact $target))
        } else {
            $representation = '7z-volumes'
            if (Test-Path -LiteralPath $target) {
                throw "Uncompressed large file already in destination; refusing to alter it: $target"
            }
            if (-not $sevenZipExe) { $sevenZipExe = Find-SevenZip $SevenZip }
            $volumes = @(ExistingVolumes $targetDir $file.Name)
            if ($volumes.Count -eq 0) {
                $stage = Join-Path $workRoot ([guid]::NewGuid().ToString('N'))
                New-Item -ItemType Directory -Force -Path $stage | Out-Null
                $archiveBase = Join-Path $stage ($file.Name + '.7z')
                Push-Location -LiteralPath $file.DirectoryName
                try {
                    & $sevenZipExe a '-t7z' ('-mx=' + $CompressionLevel) ('-v' + $VolumeMiB + 'm') '-bd' $archiveBase $file.Name
                    Assert-Exit "Archive $rel" $LASTEXITCODE
                } finally {
                    Pop-Location
                }
                $newVolumes = @(ExistingVolumes $stage $file.Name)
                Assert-Volumes $newVolumes $file.Name
                & $sevenZipExe t '-bd' $newVolumes[0].FullName
                Assert-Exit "Archive test $rel" $LASTEXITCODE
                foreach ($vol in $newVolumes) {
                    Move-Item -LiteralPath $vol.FullName -Destination (Join-Path $targetDir $vol.Name)
                }
                Remove-Item -LiteralPath $stage -Recurse -Force
                $volumes = @(ExistingVolumes $targetDir $file.Name)
            }
            Assert-Volumes $volumes $file.Name
            & $sevenZipExe t '-bd' $volumes[0].FullName
            Assert-Exit "Archive test $rel" $LASTEXITCODE
            # Also independently reconstruct original bytes and verify SHA-256.
            $validationDir = Join-Path $workRoot ([guid]::NewGuid().ToString('N'))
            New-Item -ItemType Directory -Force -Path $validationDir | Out-Null
            try {
                & $sevenZipExe x '-y' '-bd' $volumes[0].FullName ('-o' + $validationDir)
                Assert-Exit "Restore check $rel" $LASTEXITCODE
                $validationFile = Join-Path $validationDir $file.Name
                if (-not (Test-Path -LiteralPath $validationFile -PathType Leaf)) {
                    throw "Archive does not restore the expected filename: $rel"
                }
                if ((Get-Item -LiteralPath $validationFile).Length -ne $file.Length -or
                    (SHA256 $validationFile) -ne $originalHash) {
                    throw "Restored source SHA-256 mismatch: $rel"
                }
            } finally {
                Remove-Item -LiteralPath $validationDir -Recurse -Force -ErrorAction SilentlyContinue
            }
            $artifacts = @($volumes | ForEach-Object { Add-Artifact $_.FullName })
        }
        $entries.Add([ordered]@{
            sourceRelativePath = $rel
            sourceSizeBytes = [long]$file.Length
            sourceSha256 = $originalHash
            representation = $representation
            artifacts = $artifacts
        })
        Write-Host ("OK {0}  {1}  {2}" -f $representation, $rel, $file.Length)
    }
    $manifestDir = Join-Path $repoRoot (Join-Path 'manifests' $Version)
    New-Item -ItemType Directory -Path $manifestDir -Force | Out-Null
    $manifestPath = Join-Path $manifestDir 'transfer_manifest.json'
    $manifest = [ordered]@{
        schemaVersion = 1
        game = 'Pokemon Legends Z-A'
        version = $Version
        ncaDirectory = $NcaDirectory
        createdUtc = (Get-Date).ToUniversalTime().ToString('o')
        compression = [ordered]@{
            algorithm = '7z'
            level = $CompressionLevel
            volumeMiB = $VolumeMiB
            thresholdMiB = $ThresholdMiB
        }
        files = @($entries.ToArray())
    }
    $tempManifest = Join-Path $manifestDir 'transfer_manifest.json.partial'
    $manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $tempManifest -Encoding UTF8
    Move-Item -LiteralPath $tempManifest -Destination $manifestPath -Force
    Write-Host "Manifest: $manifestPath"
    Write-Host ("Complete: {0} source files" -f $entries.Count)
} finally {
    if (Test-Path -LiteralPath $workRoot) {
        $remaining = @(Get-ChildItem -LiteralPath $workRoot -Force)
        if ($remaining.Count -eq 0) { Remove-Item -LiteralPath $workRoot -Force }
    }
}
