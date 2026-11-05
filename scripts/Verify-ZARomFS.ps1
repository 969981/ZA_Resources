[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourcePath,
    [Parameter(Mandatory = $true)][string]$TargetPath,
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ManifestCsv = '',
    [string]$ManifestJson = '',
    [string]$SevenZip = '',
    [string]$Version = 'v2.0.2',
    [string]$NcaDirectory = '4a70b3ff963bfe412681185cea68bf55_NCA',
    [ValidateRange(0, 1024)][int]$ThresholdMiB = 20,
    [ValidateRange(1, 45)][int]$VolumeMiB = 45
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
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return (Resolve-Path -LiteralPath $candidate).ProviderPath }
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

function Get-SourceFiles([string]$Root) {
    $excludedDirectoryNames = @('.git', '.za-work', '.za-restore', '.cache', 'node_modules', '__pycache__')
    $stack = New-Object System.Collections.Stack
    $files = New-Object 'System.Collections.Generic.List[System.IO.FileInfo]'
    $stack.Push($Root)
    while ($stack.Count -gt 0) {
        $directory = [string]$stack.Pop()
        foreach ($item in (Get-ChildItem -LiteralPath $directory -Force -ErrorAction Stop)) {
            if ($item.PSIsContainer) {
                if ($excludedDirectoryNames -contains $item.Name) { continue }
                if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw ("Unexpected source directory link: {0}" -f $item.FullName) }
                $stack.Push($item.FullName)
                continue
            }
            if (($item.Name -match '(?i)(\.tmp|\.temp|\.partial|\.part)$') -or
                ($item.Name -match '^(?i:Thumbs\.db|desktop\.ini|\.DS_Store)$') -or $item.Name.StartsWith('~$')) { continue }
            $files.Add([System.IO.FileInfo]$item)
        }
    }
    @($files | Sort-Object FullName)
}
function Get-VolumeParts([string]$Directory, [string]$BaseName) {
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) { return @() }
    $pattern = '^' + [regex]::Escape($BaseName + '.7z.') + '\d{3,}$'
    @(Get-ChildItem -LiteralPath $Directory -File -Force |
        Where-Object { $_.Name -match $pattern } |
        Sort-Object { [int]([regex]::Match($_.Name, '\.7z\.(\d+)$').Groups[1].Value) })
}
function Assert-VolumeParts([object[]]$Parts, [string]$BaseName, [long]$MaximumBytes) {
    if ($Parts.Count -eq 0) { throw 'No archive volumes found.' }
    for ($index = 0; $index -lt $Parts.Count; $index++) {
        $expected = $BaseName + '.7z.' + ('{0:D3}' -f ($index + 1))
        if ($Parts[$index].Name -cne $expected) { throw ("Missing or out-of-order volume: expected {0}, found {1}" -f $expected, $Parts[$index].Name) }
        if ([long]$Parts[$index].Length -gt $MaximumBytes) { throw ("Volume exceeds configured size: {0}" -f $Parts[$index].FullName) }
        if ([long]$Parts[$index].Length -ge 100000000) { throw ("Volume exceeds GitHub 100,000,000 byte limit: {0}" -f $Parts[$index].FullName) }
    }
}
function Get-RepoPath([string]$RepoRoot, [string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or [IO.Path]::IsPathRooted($RelativePath) -or
        $RelativePath.Contains('\') -or $RelativePath -match '(^|/)\.\.?(/|$)') {
        throw ("Unsafe manifest path: {0}" -f $RelativePath)
    }
    $full = [IO.Path]::GetFullPath((Join-Path $RepoRoot ($RelativePath.Replace('/', [IO.Path]::DirectorySeparatorChar))))
    $prefix = $RepoRoot.TrimEnd([char[]]@('\','/')) + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw ("Manifest path escapes repository: {0}" -f $RelativePath) }
    $full
}
function Save-Results([object[]]$Records, [string]$CsvPath, [string]$JsonPath, [object]$Manifest) {
    $csvTemp = $CsvPath + '.partial'
    $jsonTemp = $JsonPath + '.partial'
    $rows = @($Records | ForEach-Object {
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
    $rows | Export-Csv -LiteralPath $csvTemp -NoTypeInformation -Encoding UTF8
    $Manifest.files = @($Records)
    $Manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $jsonTemp -Encoding UTF8
    Move-Item -LiteralPath $csvTemp -Destination $CsvPath -Force
    Move-Item -LiteralPath $jsonTemp -Destination $JsonPath -Force
}

$sourceRoot = (Resolve-Path -LiteralPath $SourcePath -ErrorAction Stop).ProviderPath.TrimEnd([char[]]@('\','/'))
$repoRoot = (Resolve-Path -LiteralPath $RepositoryRoot -ErrorAction Stop).ProviderPath.TrimEnd([char[]]@('\','/'))
$targetRoot = [IO.Path]::GetFullPath($TargetPath).TrimEnd([char[]]@('\','/'))
$prefix = $repoRoot + [IO.Path]::DirectorySeparatorChar
if (-not $targetRoot.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'TargetPath must be inside RepositoryRoot.' }
if (-not $ManifestCsv) { $ManifestCsv = Join-Path $repoRoot 'manifests\v2.0.2-romfs-inventory.csv' }
if (-not $ManifestJson) { $ManifestJson = Join-Path $repoRoot 'manifests\v2.0.2\transfer_manifest.json' }
if (-not (Test-Path -LiteralPath $ManifestJson -PathType Leaf)) { throw ("JSON manifest missing: {0}" -f $ManifestJson) }
$manifest = Get-Content -LiteralPath $ManifestJson -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schemaVersion -ne 1 -or $manifest.version -cne $Version -or $manifest.ncaDirectory -cne $NcaDirectory) {
    throw 'Manifest version, NCA directory or schema does not match the requested RomFS.'
}
$thresholdBytes = [long]$ThresholdMiB * 1MB
$maximumVolumeBytes = [long]$VolumeMiB * 1MB
$workRoot = Join-Path $repoRoot '.za-work\romfs-v2.0.2-verify'
New-Item -ItemType Directory -Path $workRoot -Force | Out-Null
$sevenZipExe = $null
$manifestByPath = @{}
foreach ($record in @($manifest.files)) { $manifestByPath[[string]$record.sourceRelativePath] = $record }
$sourceFiles = @(Get-SourceFiles $sourceRoot)
$sourcePaths = @{}
$failureCount = 0

foreach ($file in $sourceFiles) {
    $relative = $file.FullName.Substring($sourceRoot.Length).TrimStart([char[]]@('\','/')).Replace('\', '/')
    $sourcePaths[$relative] = $true
    $record = $manifestByPath[$relative]
    if (-not $record) {
        Write-Error -Message ("ERROR unlisted source file: {0}" -f $relative) -ErrorAction Continue
        $failureCount++
        continue
    }
    $status = 'Verified'
    $message = ''
    try {
        $sourceHash = Get-Sha256 $file.FullName
        if ([long]$record.sourceSizeBytes -ne [long]$file.Length -or [string]$record.sourceSha256 -cne $sourceHash) {
            throw 'Source size or SHA-256 differs from the archived manifest.'
        }
        $isRaw = [long]$file.Length -lt $thresholdBytes
        if ($isRaw -and $record.archiveType -cne 'Raw') { throw 'Archive type should be Raw for a file below 20 MiB.' }
        if (-not $isRaw -and $record.archiveType -cne '7z') { throw 'Archive type should be 7z for a file at or above 20 MiB.' }
        $targetFile = Join-Path $targetRoot ($relative.Replace('/', [IO.Path]::DirectorySeparatorChar))
        if ($isRaw) {
            if (-not (Test-Path -LiteralPath $targetFile -PathType Leaf)) { throw ("Copied source file is missing: {0}" -f $relative) }
            $targetItem = Get-Item -LiteralPath $targetFile
            if ([long]$targetItem.Length -ne [long]$file.Length -or (Get-Sha256 $targetFile) -cne $sourceHash) { throw 'Raw target size or SHA-256 differs from source.' }
            if (@($record.archiveParts).Count -ne 1) { throw 'Raw file manifest must contain exactly one artifact record.' }
            $partMeta = @($record.archiveParts)[0]
            $repoPart = Get-RepoPath $repoRoot ([string]$partMeta.path)
            if ($repoPart -cne $targetFile -or [long]$partMeta.sizeBytes -ne [long]$targetItem.Length -or [string]$partMeta.sha256 -cne (Get-Sha256 $targetFile)) {
                throw 'Raw artifact metadata does not match the target file.'
            }
            if ([int]$record.volumeCount -ne 0) { throw 'Raw files must have a volume count of zero.' }
            if ([long]$record.compressedTotalBytes -ne [long]$targetItem.Length) { throw 'Raw artifact total size is incorrect.' }
        } else {
            if (Test-Path -LiteralPath $targetFile) { throw 'Uncompressed target exists for a file stored as 7z volumes.' }
            $targetDirectory = Split-Path -Parent $targetFile
            $parts = @(Get-VolumeParts $targetDirectory $file.Name)
            Assert-VolumeParts $parts $file.Name $maximumVolumeBytes
            $metadata = @($record.archiveParts)
            if ($parts.Count -ne $metadata.Count -or [int]$record.volumeCount -ne $parts.Count) { throw 'Volume count differs from the manifest or a volume is missing.' }
            if (-not $sevenZipExe) { $sevenZipExe = Find-SevenZip $SevenZip }
            for ($index = 0; $index -lt $parts.Count; $index++) {
                $expectedName = $file.Name + '.7z.' + ('{0:D3}' -f ($index + 1))
                if ($parts[$index].Name -cne $expectedName) { throw ("Volume sequence gap at {0}" -f $expectedName) }
                $repoPart = Get-RepoPath $repoRoot ([string]$metadata[$index].path)
                if ($repoPart -cne $parts[$index].FullName -or
                    [long]$metadata[$index].sizeBytes -ne [long]$parts[$index].Length -or
                    [string]$metadata[$index].sha256 -cne (Get-Sha256 $parts[$index].FullName)) {
                    throw ("Volume metadata size, path or SHA-256 mismatch: {0}" -f $parts[$index].Name)
                }
            }
            $total = [long](($parts | Measure-Object -Property Length -Sum).Sum)
            if ([long]$record.compressedTotalBytes -ne $total) { throw 'Total volume bytes differ from the manifest.' }
            $exitCode = Invoke-SevenZip -Executable $sevenZipExe -Arguments @('t', '-bd', $parts[0].FullName)
            if ($exitCode -ne 0) { throw ("7z t failed with exit code {0}" -f $exitCode) }
            $restorePath = Join-Path $workRoot ([guid]::NewGuid().ToString('N'))
            New-Item -ItemType Directory -Path $restorePath -Force | Out-Null
            try {
                $exitCode = Invoke-SevenZip -Executable $sevenZipExe -Arguments @('x', '-y', '-bd', $parts[0].FullName, ('-o' + $restorePath))
                if ($exitCode -ne 0) { throw ("7z restore check failed with exit code {0}" -f $exitCode) }
                $restored = Join-Path $restorePath $file.Name
                if (-not (Test-Path -LiteralPath $restored -PathType Leaf)) { throw 'Restored filename does not match the original basename.' }
                if ([long](Get-Item -LiteralPath $restored).Length -ne [long]$file.Length -or (Get-Sha256 $restored) -cne $sourceHash) {
                    throw 'Restored content length or SHA-256 differs from source.'
                }
            } finally {
                Remove-Item -LiteralPath $restorePath -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
        $record.verificationStatus = 'Verified'
        $record.verificationMessage = ''
        Write-Host ("OK {0} {1}" -f $record.archiveType, $relative)
    } catch {
        $status = 'Error'
        $message = $_.Exception.Message
        $record.verificationStatus = $status
        $record.verificationMessage = $message
        Write-Error -Message ("ERROR {0}: {1}" -f $relative, $message) -ErrorAction Continue
        $failureCount++
    }
}

foreach ($record in @($manifest.files)) {
    if (-not $sourcePaths.ContainsKey([string]$record.sourceRelativePath)) {
        $record.verificationStatus = 'Error'
        $record.verificationMessage = 'Manifest entry has no matching source file.'
        Write-Error -Message ("ERROR source missing for manifest entry: {0}" -f $record.sourceRelativePath) -ErrorAction Continue
        $failureCount++
    }
}
Save-Results @($manifest.files) $ManifestCsv $ManifestJson $manifest
Write-Host ("Audit complete: {0} source files, {1} failures." -f $sourceFiles.Count, $failureCount)
if ($failureCount -gt 0) { exit 2 }
