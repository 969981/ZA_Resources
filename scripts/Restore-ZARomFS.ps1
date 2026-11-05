[CmdletBinding(DefaultParameterSetName = 'Manifest')]
param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$TargetPath = '',
    [Parameter(Mandatory = $true)][string]$DestinationRoot,
    [Parameter(ParameterSetName = 'Manifest')][string]$SourceRelativePath = '',
    [Parameter(Mandatory = $true, ParameterSetName = 'Volume')][string]$ArchiveFirstVolume,
    [string]$ManifestJson = '',
    [string]$SevenZip = '',
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

function Get-VolumeParts([string]$Directory, [string]$BaseName) {
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) { return @() }
    $pattern = '^' + [regex]::Escape($BaseName + '.7z.') + '\d{3,}$'
    @(Get-ChildItem -LiteralPath $Directory -File -Force |
        Where-Object { $_.Name -match $pattern } |
        Sort-Object { [int]([regex]::Match($_.Name, '\.7z\.(\d+)$').Groups[1].Value) })
}
function Assert-VolumeParts([object[]]$Parts, [string]$BaseName, [long]$MaximumBytes) {
    if ($Parts.Count -eq 0) { throw 'No volumes found for archive.' }
    for ($index = 0; $index -lt $Parts.Count; $index++) {
        $expected = $BaseName + '.7z.' + ('{0:D3}' -f ($index + 1))
        if ($Parts[$index].Name -cne $expected) { throw ("Missing or out-of-order volume: expected {0}, found {1}" -f $expected, $Parts[$index].Name) }
        if ([long]$Parts[$index].Length -gt $MaximumBytes) { throw ("Volume exceeds configured size: {0}" -f $Parts[$index].FullName) }
        if ([long]$Parts[$index].Length -ge 100000000) { throw ("Volume exceeds GitHub's 100,000,000 byte object limit: {0}" -f $Parts[$index].FullName) }
    }
}
function Get-RepoPath([string]$RepoRoot, [string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or [IO.Path]::IsPathRooted($RelativePath) -or
        $RelativePath.Contains('\') -or $RelativePath -match '(^|/)\.\.?(/|$)') { throw ("Unsafe manifest path: {0}" -f $RelativePath) }
    $full = [IO.Path]::GetFullPath((Join-Path $RepoRoot ($RelativePath.Replace('/', [IO.Path]::DirectorySeparatorChar))))
    $prefix = $RepoRoot.TrimEnd([char[]]@('\','/')) + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw ("Manifest path escapes repository: {0}" -f $RelativePath) }
    $full
}
function Get-DestinationFile([string]$Root, [string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or [IO.Path]::IsPathRooted($RelativePath) -or
        $RelativePath.Contains('\') -or $RelativePath -match '(^|/)\.\.?(/|$)') { throw ("Unsafe source-relative path: {0}" -f $RelativePath) }
    $full = [IO.Path]::GetFullPath((Join-Path $Root ($RelativePath.Replace('/', [IO.Path]::DirectorySeparatorChar))))
    $prefix = $Root.TrimEnd([char[]]@('\','/')) + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw ("Restore path escapes DestinationRoot: {0}" -f $RelativePath) }
    $full
}
function Publish-RestoredFile([string]$StagedFile, [string]$TargetFile, [long]$ExpectedSize, [string]$ExpectedHash) {
    if ((Get-Item -LiteralPath $StagedFile).Length -ne $ExpectedSize -or (Get-Sha256 $StagedFile) -cne $ExpectedHash) {
        throw 'Staged restored file does not match the original size and SHA-256.'
    }
    if (Test-Path -LiteralPath $TargetFile) {
        if ((Test-Path -LiteralPath $TargetFile -PathType Leaf) -and
            (Get-Item -LiteralPath $TargetFile).Length -eq $ExpectedSize -and (Get-Sha256 $TargetFile) -ceq $ExpectedHash) {
            Write-Host ("SKIP already restored {0}" -f $TargetFile)
            return
        }
        throw ("Destination exists and differs; refusing overwrite: {0}" -f $TargetFile)
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $TargetFile) -Force | Out-Null
    Copy-Item -LiteralPath $StagedFile -Destination $TargetFile
    if ((Get-Item -LiteralPath $TargetFile).Length -ne $ExpectedSize -or (Get-Sha256 $TargetFile) -cne $ExpectedHash) {
        throw ("Final restored file failed size/SHA-256 verification: {0}" -f $TargetFile)
    }
    Write-Host ("OK restored {0}" -f $TargetFile)
}
function Test-AndExtract([string]$FirstPart, [string]$ExpectedFileName, [string]$RestoreDirectory, [string]$SevenZipExe) {
    $exitCode = Invoke-SevenZip -Executable $SevenZipExe -Arguments @('t', '-bd', $FirstPart)
    if ($exitCode -ne 0) { throw ("7z t failed with exit code {0}" -f $exitCode) }
    New-Item -ItemType Directory -Path $RestoreDirectory -Force | Out-Null
    $exitCode = Invoke-SevenZip -Executable $SevenZipExe -Arguments @('x', '-y', '-bd', $FirstPart, ('-o' + $RestoreDirectory))
    if ($exitCode -ne 0) { throw ("7z extraction failed with exit code {0}" -f $exitCode) }
    $restored = Join-Path $RestoreDirectory $ExpectedFileName
    if (-not (Test-Path -LiteralPath $restored -PathType Leaf)) { throw ("Archive did not contain the expected basename: {0}" -f $ExpectedFileName) }
    $restored
}

$repoRoot = (Resolve-Path -LiteralPath $RepositoryRoot -ErrorAction Stop).ProviderPath.TrimEnd([char[]]@('\','/'))
if (-not $TargetPath) { $TargetPath = Join-Path $repoRoot 'v2.0.2\4a70b3ff963bfe412681185cea68bf55_NCA\1' }
$targetRoot = [IO.Path]::GetFullPath($TargetPath).TrimEnd([char[]]@('\','/'))
$destinationRoot = [IO.Path]::GetFullPath($DestinationRoot).TrimEnd([char[]]@('\','/'))
New-Item -ItemType Directory -Path $destinationRoot -Force | Out-Null
$maximumVolumeBytes = [long]$VolumeMiB * 1MB
$sevenZipExe = $null
$workRoot = Join-Path $repoRoot '.za-work\restore'
New-Item -ItemType Directory -Path $workRoot -Force | Out-Null

if ($PSCmdlet.ParameterSetName -eq 'Volume') {
    $first = (Resolve-Path -LiteralPath $ArchiveFirstVolume -ErrorAction Stop).ProviderPath
    if ($first -notmatch '\.7z\.001$') { throw 'ArchiveFirstVolume must name a .7z.001 file.' }
    $baseName = [IO.Path]::GetFileName($first).Substring(0, [IO.Path]::GetFileName($first).Length - '.7z.001'.Length)
    $parts = @(Get-VolumeParts (Split-Path -Parent $first) $baseName)
    Assert-VolumeParts $parts $baseName $maximumVolumeBytes
    $sevenZipExe = Find-SevenZip $SevenZip
    $stage = Join-Path $workRoot ([guid]::NewGuid().ToString('N'))
    try {
        $stagedFile = Test-AndExtract $first $baseName $stage $sevenZipExe
        $targetFile = Get-DestinationFile $destinationRoot $baseName
        Publish-RestoredFile $stagedFile $targetFile ([long](Get-Item -LiteralPath $stagedFile).Length) (Get-Sha256 $stagedFile)
    } finally {
        Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    }
    return
}

if (-not $ManifestJson) { $ManifestJson = Join-Path $repoRoot 'manifests\v2.0.2\transfer_manifest.json' }
if (-not (Test-Path -LiteralPath $ManifestJson -PathType Leaf)) { throw ("Manifest missing: {0}" -f $ManifestJson) }
$manifest = Get-Content -LiteralPath $ManifestJson -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schemaVersion -ne 1) { throw 'Unsupported manifest schema.' }
$records = @($manifest.files)
if ($SourceRelativePath) {
    $records = @($records | Where-Object { [string]$_.sourceRelativePath -ceq $SourceRelativePath })
    if ($records.Count -ne 1) { throw ("Expected exactly one manifest entry for {0}" -f $SourceRelativePath) }
}
foreach ($record in $records) {
    $relative = [string]$record.sourceRelativePath
    $destinationFile = Get-DestinationFile $destinationRoot $relative
    if ($record.archiveType -ceq 'Raw') {
        $parts = @($record.archiveParts)
        if ($parts.Count -ne 1) { throw ("Raw record must have one artifact: {0}" -f $relative) }
        $artifact = Get-RepoPath $repoRoot ([string]$parts[0].path)
        if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) { throw ("Raw artifact missing: {0}" -f $artifact) }
        if ([long](Get-Item -LiteralPath $artifact).Length -ne [long]$parts[0].sizeBytes -or (Get-Sha256 $artifact) -cne [string]$parts[0].sha256) {
            throw ("Raw artifact size or hash mismatch: {0}" -f $relative)
        }
        Publish-RestoredFile $artifact $destinationFile ([long]$record.sourceSizeBytes) ([string]$record.sourceSha256)
        continue
    }
    if ($record.archiveType -cne '7z') { throw ("Unsupported archive type for {0}" -f $relative) }
    $archiveParts = @($record.archiveParts)
    if ($archiveParts.Count -eq 0) { throw ("No volume entries in manifest for {0}" -f $relative) }
    $paths = @()
    foreach ($partMeta in $archiveParts) {
        $path = Get-RepoPath $repoRoot ([string]$partMeta.path)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ("Archive volume missing: {0}" -f $path) }
        if ([long](Get-Item -LiteralPath $path).Length -ne [long]$partMeta.sizeBytes -or (Get-Sha256 $path) -cne [string]$partMeta.sha256) {
            throw ("Archive volume size or hash mismatch: {0}" -f $path)
        }
        $paths += $path
    }
    $baseName = [IO.Path]::GetFileName($relative)
    $diskParts = @(Get-VolumeParts (Split-Path -Parent $paths[0]) $baseName)
    Assert-VolumeParts $diskParts $baseName $maximumVolumeBytes
    if ($diskParts.Count -ne $paths.Count -or [int]$record.volumeCount -ne $paths.Count) { throw ("Volume count mismatch: {0}" -f $relative) }
    for ($index = 0; $index -lt $paths.Count; $index++) {
        if ($diskParts[$index].FullName -cne $paths[$index]) { throw ("Volume order mismatch: {0}" -f $relative) }
    }
    if (-not $sevenZipExe) { $sevenZipExe = Find-SevenZip $SevenZip }
    $stage = Join-Path $workRoot ([guid]::NewGuid().ToString('N'))
    try {
        $stagedFile = Test-AndExtract $paths[0] $baseName $stage $sevenZipExe
        Publish-RestoredFile $stagedFile $destinationFile ([long]$record.sourceSizeBytes) ([string]$record.sourceSha256)
    } finally {
        Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Write-Host ("Restore complete: {0} file(s) to {1}" -f $records.Count, $destinationRoot)
