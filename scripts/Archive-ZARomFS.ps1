[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][Alias('SourceRoot')][string]$SourcePath,
    [Parameter(Mandatory = $true)][Alias('DestinationRoot')][string]$TargetPath,
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ManifestCsv = '',
    [string]$ManifestJson = '',
    [string]$Version = 'v2.0.2',
    [string]$NcaDirectory = '4a70b3ff963bfe412681185cea68bf55_NCA',
    [string]$SevenZip = '',
    [ValidateRange(0, 1024)][int]$ThresholdMiB = 20,
    [ValidateRange(1, 45)][int]$VolumeMiB = 45,
    [ValidateRange(0, 9)][int]$CompressionLevel = 5,
    [switch]$Resume,
    [switch]$VerifyOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Find-SevenZip([string]$Requested) {
    $candidates = @()
    if ($Requested) { $candidates += $Requested }
    if ($env:ProgramFiles) { $candidates += (Join-Path $env:ProgramFiles '7-Zip\7z.exe') }
    $candidates += @('C:\Program Files (x86)\7-Zip\7z.exe', '7z.exe', '7z')
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $candidate).ProviderPath
        }
        $command = Get-Command -Name $candidate -ErrorAction SilentlyContinue
        if ($command) { return $command.Source }
    }
    throw '7-Zip was not found. Pass -SevenZip with the Windows 7z.exe path or add 7z.exe to PATH.'
}

function Invoke-SevenZip([string]$Executable, [string[]]$Arguments) {
    $quotedArguments = @()
    foreach ($argument in $Arguments) {
        $quotedArguments += '"' + ([string]$argument).Replace('"', '\"') + '"'
    }
    $process = Start-Process -FilePath $Executable -ArgumentList ($quotedArguments -join ' ') -Wait -PassThru -NoNewWindow
    [int]$process.ExitCode
}

function Get-RepoRelativePath([string]$FullPath, [string]$RepoRoot) {
    $prefix = $RepoRoot.TrimEnd([char[]]@('\','/')) + [IO.Path]::DirectorySeparatorChar
    if (-not $FullPath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Artifact is outside RepositoryRoot: $FullPath"
    }
    $FullPath.Substring($prefix.Length).Replace('\', '/')
}

function Get-SourceFiles([string]$Root) {
    $excludedDirectoryNames = @('.git', '.za-work', '.za-restore', '.cache', 'node_modules', '__pycache__')
    $stack = New-Object System.Collections.Stack
    $files = New-Object 'System.Collections.Generic.List[System.IO.FileInfo]'
    $script:ExcludedSourceFiles = New-Object 'System.Collections.Generic.List[object]'
    $stack.Push($Root)
    while ($stack.Count -gt 0) {
        $directory = [string]$stack.Pop()
        foreach ($item in (Get-ChildItem -LiteralPath $directory -Force -ErrorAction Stop)) {
            $relative = $item.FullName.Substring($Root.Length).TrimStart([char[]]@('\','/')).Replace('\', '/')
            if ($item.PSIsContainer) {
                if ($excludedDirectoryNames -contains $item.Name) {
                    $script:ExcludedSourceFiles.Add([ordered]@{ path = $relative; reason = 'excluded cache or Git metadata directory' })
                    Write-Host ("EXCLUDED directory {0}" -f $relative)
                    continue
                }
                if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                    throw "Source contains a directory link; refusing to follow an external path: $relative"
                }
                $stack.Push($item.FullName)
                continue
            }
            $temporaryName = ($item.Name -match '(?i)(\.tmp|\.temp|\.partial|\.part)$') -or
                ($item.Name -match '^(?i:Thumbs\.db|desktop\.ini|\.DS_Store)$') -or
                $item.Name.StartsWith('~$')
            if ($temporaryName) {
                $script:ExcludedSourceFiles.Add([ordered]@{ path = $relative; reason = 'temporary or operating-system metadata file' })
                Write-Host ("EXCLUDED file {0}" -f $relative)
                continue
            }
            $files.Add([System.IO.FileInfo]$item)
        }
    }
    @($files | Sort-Object Length, FullName)
}

function Get-VolumeParts([string]$Directory, [string]$BaseName) {
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) { return @() }
    $pattern = '^' + [regex]::Escape($BaseName + '.7z.') + '\d{3,}$'
    @(Get-ChildItem -LiteralPath $Directory -File -Force |
        Where-Object { $_.Name -match $pattern } |
        Sort-Object { [int]([regex]::Match($_.Name, '\.7z\.(\d+)$').Groups[1].Value) })
}

function Assert-VolumeParts([object[]]$Parts, [string]$BaseName, [long]$MaximumBytes) {
    if ($Parts.Count -eq 0) { throw 'No 7z volumes found.' }
    for ($index = 0; $index -lt $Parts.Count; $index++) {
        $expected = $BaseName + '.7z.' + ('{0:D3}' -f ($index + 1))
        if ($Parts[$index].Name -cne $expected) {
            throw ("Volume sequence has a gap or unexpected name: expected {0}, found {1}" -f $expected, $Parts[$index].Name)
        }
        if ([long]$Parts[$index].Length -gt $MaximumBytes) {
            throw ("Volume exceeds configured {0} byte limit: {1}" -f $MaximumBytes, $Parts[$index].FullName)
        }
        if ([long]$Parts[$index].Length -ge 100000000) {
            throw ("Volume exceeds GitHub's 100,000,000 byte object limit: {0}" -f $Parts[$index].FullName)
        }
    }
}

function Test-ArchivePayload([object[]]$Parts, [string]$FileName, [long]$ExpectedLength, [string]$ExpectedHash, [string]$SevenZipExe, [string]$WorkRoot) {
    $exitCode = Invoke-SevenZip -Executable $SevenZipExe -Arguments @('t', '-bd', $Parts[0].FullName)
    if ($exitCode -ne 0) { throw ("7z t failed with exit code {0}" -f $exitCode) }
    $restorePath = Join-Path $WorkRoot ('verify-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $restorePath -Force | Out-Null
    try {
        $exitCode = Invoke-SevenZip -Executable $SevenZipExe -Arguments @('x', '-y', '-bd', $Parts[0].FullName, ('-o' + $restorePath))
        if ($exitCode -ne 0) { throw ("7z restore check failed with exit code {0}" -f $exitCode) }
        $restored = Join-Path $restorePath $FileName
        if (-not (Test-Path -LiteralPath $restored -PathType Leaf)) {
            throw ("Archive did not restore the expected relative filename: {0}" -f $FileName)
        }
        $restoredItem = Get-Item -LiteralPath $restored
        if ([long]$restoredItem.Length -ne $ExpectedLength -or (Get-Sha256 $restored) -cne $ExpectedHash) {
            throw 'Restored file length or SHA-256 differs from the source.'
        }
    } finally {
        Remove-Item -LiteralPath $restorePath -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function New-PartRecords([object[]]$Parts, [string]$RepoRoot) {
    $records = @()
    foreach ($part in $Parts) {
        $records += [ordered]@{
            path = (Get-RepoRelativePath $part.FullName $RepoRoot)
            sizeBytes = [long]$part.Length
            sha256 = (Get-Sha256 $part.FullName)
        }
    }
    @($records)
}

function Save-Manifests([object[]]$Records, [string]$CsvPath, [string]$JsonPath, [string]$VersionValue, [string]$NcaValue, [int]$ThresholdValue, [int]$VolumeValue, [int]$LevelValue, [object[]]$Excluded) {
    foreach ($path in @($CsvPath, $JsonPath)) {
        $parent = Split-Path -Parent $path
        if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    }
    $csvTemp = $CsvPath + '.partial'
    $jsonTemp = $JsonPath + '.partial'
    $csvRows = @($Records | ForEach-Object {
        [pscustomobject][ordered]@{
            OriginalRelativePath = $_.sourceRelativePath
            OriginalSizeBytes = [long]$_.sourceSizeBytes
            SHA256 = $_.sourceSha256
            ArchiveType = $_.archiveType
            TargetRelativePath = $_.targetRelativePath
            VolumeCount = [int]$_.volumeCount
            CompressedTotalBytes = [long]$_.compressedTotalBytes
            VerificationStatus = $_.verificationStatus
            GitCommitBatch = $_.gitCommitBatch
        }
    })
    if ($csvRows.Count -gt 0) {
        $csvRows | Export-Csv -LiteralPath $csvTemp -NoTypeInformation -Encoding UTF8
    } else {
        'OriginalRelativePath,OriginalSizeBytes,SHA256,ArchiveType,TargetRelativePath,VolumeCount,CompressedTotalBytes,VerificationStatus,GitCommitBatch' |
            Set-Content -LiteralPath $csvTemp -Encoding UTF8
    }
    $manifest = [ordered]@{
        schemaVersion = 1
        version = $VersionValue
        ncaDirectory = $NcaValue
        compression = [ordered]@{
            archiveTypeThresholdMiB = $ThresholdValue
            format = '7z'
            volumeMiB = $VolumeValue
            level = $LevelValue
            multithreaded = $true
        }
        excludedSourceFiles = @($Excluded)
        files = @($Records)
    }
    $manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $jsonTemp -Encoding UTF8
    Move-Item -LiteralPath $csvTemp -Destination $CsvPath -Force
    Move-Item -LiteralPath $jsonTemp -Destination $JsonPath -Force
}

$sourceRoot = (Resolve-Path -LiteralPath $SourcePath -ErrorAction Stop).ProviderPath.TrimEnd([char[]]@('\','/'))
$repoRoot = (Resolve-Path -LiteralPath $RepositoryRoot -ErrorAction Stop).ProviderPath.TrimEnd([char[]]@('\','/'))
$targetRoot = [IO.Path]::GetFullPath($TargetPath).TrimEnd([char[]]@('\','/'))
$repoPrefix = $repoRoot + [IO.Path]::DirectorySeparatorChar
$sourcePrefix = $sourceRoot + [IO.Path]::DirectorySeparatorChar
if (-not $targetRoot.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'TargetPath must be inside RepositoryRoot so manifest artifact paths stay repository-relative.'
}
if ($targetRoot.Equals($sourceRoot, [StringComparison]::OrdinalIgnoreCase) -or
    $targetRoot.StartsWith($sourcePrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'TargetPath cannot be the source directory or a directory inside it.'
}
if ($Version -notmatch '^v\d+\.\d+\.\d+$') { throw 'Version must look like v2.0.2.' }
if ($NcaDirectory -notmatch '^[0-9a-fA-F]{32}_NCA$') { throw 'NcaDirectory must be 32 hex characters followed by _NCA.' }
if (-not $ManifestCsv) { $ManifestCsv = Join-Path $repoRoot 'manifests\v2.0.2-romfs-inventory.csv' }
if (-not $ManifestJson) { $ManifestJson = Join-Path $repoRoot 'manifests\v2.0.2\transfer_manifest.json' }
$thresholdBytes = [long]$ThresholdMiB * 1MB
$maximumVolumeBytes = [long]$VolumeMiB * 1MB
$workRoot = Join-Path $repoRoot '.za-work\romfs-v2.0.2'
if (-not $VerifyOnly) { New-Item -ItemType Directory -Path $workRoot -Force | Out-Null }

$oldBatchByPath = @{}
if (Test-Path -LiteralPath $ManifestJson -PathType Leaf) {
    try {
        $oldManifest = Get-Content -LiteralPath $ManifestJson -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($oldRecord in @($oldManifest.files)) {
            if ($oldRecord.gitCommitBatch) { $oldBatchByPath[[string]$oldRecord.sourceRelativePath] = [string]$oldRecord.gitCommitBatch }
        }
    } catch {
        Write-Warning 'Existing JSON manifest could not be read; new verified records will replace it.'
    }
}
$sourceFiles = @(Get-SourceFiles $sourceRoot)
if ($sourceFiles.Count -eq 0) { throw 'SourcePath contains no eligible files.' }
Write-Host ("Scanned {0} eligible files; excluded {1} temporary/cache entries." -f $sourceFiles.Count, $script:ExcludedSourceFiles.Count)
if ($Resume) { Write-Host 'Resume mode: matching verified outputs will be retained; conflicts will be recorded.' }
if ($VerifyOnly) { Write-Host 'VerifyOnly mode: no archive or manifest files will be written.' }
$sevenZipExe = $null
$records = New-Object 'System.Collections.Generic.List[object]'
$failedCount = 0

foreach ($file in $sourceFiles) {
    $relative = $file.FullName.Substring($sourceRoot.Length).TrimStart([char[]]@('\','/')).Replace('\', '/')
    $targetFile = Join-Path $targetRoot ($relative.Replace('/', [IO.Path]::DirectorySeparatorChar))
    $entry = [ordered]@{
        sourceRelativePath = $relative
        sourceSizeBytes = [long]$file.Length
        sourceSha256 = ''
        archiveType = if ([long]$file.Length -lt $thresholdBytes) { 'Raw' } else { '7z' }
        targetRelativePath = ''
        volumeCount = 0
        compressedTotalBytes = 0L
        verificationStatus = 'Pending'
        gitCommitBatch = if ($oldBatchByPath.ContainsKey($relative)) { $oldBatchByPath[$relative] } else { '' }
        archiveParts = @()
        verificationMessage = ''
    }
    try {
        $sourceHash = Get-Sha256 $file.FullName
        $entry.sourceSha256 = $sourceHash
        if ($entry.archiveType -eq 'Raw') {
            if (Test-Path -LiteralPath $targetFile) {
                if (-not (Test-Path -LiteralPath $targetFile -PathType Leaf)) { throw ("CONFLICT: destination exists but is not a file: {0}" -f $targetFile) }
                $targetItem = Get-Item -LiteralPath $targetFile
                if ([long]$targetItem.Length -ne [long]$file.Length -or (Get-Sha256 $targetFile) -cne $sourceHash) {
                    throw ("CONFLICT: existing raw file differs from source; preserved: {0}" -f $targetFile)
                }
                $parts = @($targetItem)
                $entry.verificationStatus = 'Verified'
                Write-Host ("SKIP verified raw {0}" -f $relative)
            } elseif ($VerifyOnly) {
                $entry.verificationStatus = 'Missing'
                throw ("MISSING: raw destination file: {0}" -f $relative)
            } else {
                $stage = Join-Path $workRoot ('copy-' + [guid]::NewGuid().ToString('N'))
                New-Item -ItemType Directory -Path $stage -Force | Out-Null
                try {
                    $stagedFile = Join-Path $stage $file.Name
                    Copy-Item -LiteralPath $file.FullName -Destination $stagedFile
                    if ((Get-Item -LiteralPath $stagedFile).Length -ne [long]$file.Length -or (Get-Sha256 $stagedFile) -cne $sourceHash) {
                        throw 'Staged raw copy failed source size/SHA-256 verification.'
                    }
                    if ((Get-Sha256 $file.FullName) -cne $sourceHash) { throw 'Source changed while copying; no destination was published.' }
                    New-Item -ItemType Directory -Path (Split-Path -Parent $targetFile) -Force | Out-Null
                    Move-Item -LiteralPath $stagedFile -Destination $targetFile
                } finally {
                    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
                }
                $parts = @(Get-Item -LiteralPath $targetFile)
                $entry.verificationStatus = 'Verified'
                Write-Host ("OK raw {0}" -f $relative)
            }
            $entry.archiveParts = @(New-PartRecords $parts $repoRoot)
            $entry.targetRelativePath = $entry.archiveParts[0].path
            $entry.compressedTotalBytes = [long]$parts[0].Length
        } else {
            if (Test-Path -LiteralPath $targetFile) {
                throw ("CONFLICT: uncompressed destination exists for a large file; preserved: {0}" -f $targetFile)
            }
            $targetDirectory = Split-Path -Parent $targetFile
            $existingParts = @(Get-VolumeParts $targetDirectory $file.Name)
            $existingVerified = $false
            if ($existingParts.Count -gt 0) {
                try {
                    Assert-VolumeParts $existingParts $file.Name $maximumVolumeBytes
                    if (-not $sevenZipExe) { $sevenZipExe = Find-SevenZip $SevenZip }
                    Test-ArchivePayload $existingParts $file.Name ([long]$file.Length) $sourceHash $sevenZipExe $workRoot
                    $existingVerified = $true
                } catch {
                    Write-Warning ("Existing volumes are incomplete or invalid for {0}: {1}" -f $relative, $_.Exception.Message)
                }
            }
            if ($existingVerified) {
                $parts = $existingParts
                $entry.verificationStatus = 'Verified'
                Write-Host ("SKIP verified 7z {0}" -f $relative)
            } elseif ($VerifyOnly) {
                $entry.verificationStatus = if ($existingParts.Count -gt 0) { 'Invalid' } else { 'Missing' }
                throw ("MISSING: no fully verified archive for {0}" -f $relative)
            } else {
                if (-not $sevenZipExe) { $sevenZipExe = Find-SevenZip $SevenZip }
                New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
                $stage = Join-Path $workRoot ('archive-' + [guid]::NewGuid().ToString('N'))
                New-Item -ItemType Directory -Path $stage -Force | Out-Null
                try {
                    $archiveBase = Join-Path $stage ($file.Name + '.7z')
                    Push-Location -LiteralPath $file.DirectoryName
                    try {
                        $archiveExit = Invoke-SevenZip -Executable $sevenZipExe -Arguments @('a', '-t7z', ('-mx=' + $CompressionLevel), '-mmt=on', ('-v' + $VolumeMiB + 'm'), '-bd', '-y', $archiveBase, $file.Name)
                    } finally {
                        Pop-Location
                    }
                    if ($archiveExit -ne 0) { throw ("7z archive creation failed with exit code {0}." -f $archiveExit) }
                    $stagedParts = @(Get-VolumeParts $stage $file.Name)
                    Assert-VolumeParts $stagedParts $file.Name $maximumVolumeBytes
                    Test-ArchivePayload $stagedParts $file.Name ([long]$file.Length) $sourceHash $sevenZipExe $workRoot
                    if ((Get-Sha256 $file.FullName) -cne $sourceHash) { throw 'Source changed while archiving; generated volumes were not published.' }

                    $stagedByName = @{}
                    foreach ($part in $stagedParts) { $stagedByName[$part.Name] = $part }
                    foreach ($part in $existingParts) {
                        if (-not $stagedByName.ContainsKey($part.Name)) {
                            throw ("CONFLICT: unexpected existing volume preserved: {0}" -f $part.FullName)
                        }
                        if ((Get-Sha256 $part.FullName) -cne (Get-Sha256 $stagedByName[$part.Name].FullName)) {
                            throw ("CONFLICT: existing volume differs from verified output; preserved: {0}" -f $part.FullName)
                        }
                    }
                    foreach ($part in $stagedParts) {
                        $destinationPart = Join-Path $targetDirectory $part.Name
                        if (-not (Test-Path -LiteralPath $destinationPart)) {
                            Move-Item -LiteralPath $part.FullName -Destination $destinationPart
                        }
                    }
                    $parts = @(Get-VolumeParts $targetDirectory $file.Name)
                    Assert-VolumeParts $parts $file.Name $maximumVolumeBytes
                    Test-ArchivePayload $parts $file.Name ([long]$file.Length) $sourceHash $sevenZipExe $workRoot
                    $entry.verificationStatus = 'Verified'
                    Write-Host ("OK 7z {0} ({1} volumes, {2} bytes)" -f $relative, $parts.Count, (($parts | Measure-Object -Property Length -Sum).Sum))
                } finally {
                    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
                }
            }
            $entry.archiveParts = @(New-PartRecords $parts $repoRoot)
            $entry.targetRelativePath = $entry.archiveParts[0].path
            $entry.volumeCount = $parts.Count
            $entry.compressedTotalBytes = [long](($parts | Measure-Object -Property Length -Sum).Sum)
        }
    } catch {
        $message = $_.Exception.Message
        if ($message.StartsWith('CONFLICT:')) {
            $entry.verificationStatus = 'Conflict'
            $entry.verificationMessage = $message.Substring(9).Trim()
        } elseif ($message.StartsWith('MISSING:')) {
            if ($entry.verificationStatus -eq 'Pending') { $entry.verificationStatus = 'Missing' }
            $entry.verificationMessage = $message.Substring(8).Trim()
        } else {
            $entry.verificationStatus = 'Error'
            $entry.verificationMessage = $message
        }
        Write-Error -Message ("{0}: {1}" -f $entry.verificationStatus, $entry.verificationMessage) -ErrorAction Continue
    }
    if ($entry.verificationStatus -ne 'Verified') { $failedCount++ }
    $records.Add($entry)
    if (-not $VerifyOnly) {
        Save-Manifests $records.ToArray() $ManifestCsv $ManifestJson $Version $NcaDirectory $ThresholdMiB $VolumeMiB $CompressionLevel $script:ExcludedSourceFiles.ToArray()
    }
}
Write-Host ("Finished: {0} files, {1} not verified, {2} excluded." -f $records.Count, $failedCount, $script:ExcludedSourceFiles.Count)
if ($failedCount -gt 0) { exit 2 }
