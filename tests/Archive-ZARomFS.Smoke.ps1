[CmdletBinding()]
param(
    [string]$SevenZip = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).ProviderPath
$archiveScript = Join-Path $repoRoot 'scripts\Archive-ZARomFS.ps1'
$verifyScript = Join-Path $repoRoot 'scripts\Verify-ZARomFS.ps1'
$restoreScript = Join-Path $repoRoot 'scripts\Restore-ZARomFS.ps1'
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('za-romfs-smoke-' + [guid]::NewGuid().ToString('N'))
$testRepo = Join-Path $tempRoot 'repo'
$source = Join-Path $tempRoot 'source'
$target = Join-Path $testRepo 'v2.0.2\4a70b3ff963bfe412681185cea68bf55_NCA\1'
$hiddenDirectory = Join-Path $source 'romfs\.hidden'
$largeDirectory = Join-Path $source 'arc'
$restoredOne = Join-Path $tempRoot 'restored-one'
$restoredAll = Join-Path $tempRoot 'restored-all'
New-Item -ItemType Directory -Path $testRepo,$hiddenDirectory,$largeDirectory -Force | Out-Null
try {
    $smallPath = Join-Path $hiddenDirectory 'hidden.small'
    [IO.File]::WriteAllBytes($smallPath, [Text.Encoding]::UTF8.GetBytes('small hidden fixture'))
    $largePath = Join-Path $largeDirectory 'random.trpfs'
    $buffer = New-Object byte[] (2MB + 173)
    $random = [Security.Cryptography.RandomNumberGenerator]::Create()
    $random.GetBytes($buffer)
    $random.Dispose()
    [IO.File]::WriteAllBytes($largePath, $buffer)

    & $archiveScript -SourcePath $source -TargetPath $target -RepositoryRoot $testRepo -SevenZip $SevenZip -ThresholdMiB 1 -VolumeMiB 1 -CompressionLevel 5 -Resume
    $csv = Import-Csv -LiteralPath (Join-Path $testRepo 'manifests\v2.0.2-romfs-inventory.csv')
    if ($csv.Count -ne 2) { throw ("Expected two inventory rows, got {0}." -f $csv.Count) }
    $hiddenRecord = $csv | Where-Object { $_.OriginalRelativePath -ceq 'romfs/.hidden/hidden.small' }
    if (-not $hiddenRecord -or $hiddenRecord.ArchiveType -cne 'Raw') { throw 'Hidden directory raw file was omitted or misclassified.' }
    $largeRecord = $csv | Where-Object { $_.OriginalRelativePath -ceq 'arc/random.trpfs' }
    if (-not $largeRecord -or $largeRecord.ArchiveType -cne '7z' -or [int]$largeRecord.VolumeCount -lt 2) {
        throw 'Synthetic large file did not create multiple 7z volumes.'
    }
    & $verifyScript -SourcePath $source -TargetPath $target -RepositoryRoot $testRepo -SevenZip $SevenZip -ThresholdMiB 1 -VolumeMiB 1
    & $restoreScript -RepositoryRoot $testRepo -TargetPath $target -DestinationRoot $restoredOne -SourceRelativePath 'arc/random.trpfs' -SevenZip $SevenZip -VolumeMiB 1
    & $restoreScript -RepositoryRoot $testRepo -TargetPath $target -DestinationRoot $restoredAll -SevenZip $SevenZip -VolumeMiB 1
    foreach ($original in @($smallPath, $largePath)) {
        $rel = $original.Substring($source.Length + 1).Replace('\', [IO.Path]::DirectorySeparatorChar)
        foreach ($root in @($restoredOne, $restoredAll)) {
            $copy = Join-Path $root $rel
            if (Test-Path -LiteralPath $copy -PathType Leaf) {
                if ((Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash -cne (Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash) {
                    throw ("Restored synthetic hash differs: {0}" -f $rel)
                }
            }
        }
    }
    $directRestore = Join-Path $tempRoot 'restored-from-volume'
    $firstVolume = Join-Path (Split-Path -Parent $largeRecord.TargetRelativePath | ForEach-Object { Join-Path $testRepo $_ }) (Split-Path -Leaf $largeRecord.TargetRelativePath)
    & $restoreScript -RepositoryRoot $testRepo -DestinationRoot $directRestore -ArchiveFirstVolume $firstVolume -SevenZip $SevenZip -VolumeMiB 1
    $directFile = Join-Path $directRestore 'random.trpfs'
    if ((Get-FileHash -LiteralPath $largePath -Algorithm SHA256).Hash -cne (Get-FileHash -LiteralPath $directFile -Algorithm SHA256).Hash) {
        throw 'Direct .7z.001 restoration hash differs.'
    }
    $beforeManifest = (Get-FileHash -LiteralPath (Join-Path $testRepo 'manifests\v2.0.2-romfs-inventory.csv') -Algorithm SHA256).Hash
    & $archiveScript -SourcePath $source -TargetPath $target -RepositoryRoot $testRepo -SevenZip $SevenZip -ThresholdMiB 1 -VolumeMiB 1 -Resume -VerifyOnly
    $afterManifest = (Get-FileHash -LiteralPath (Join-Path $testRepo 'manifests\v2.0.2-romfs-inventory.csv') -Algorithm SHA256).Hash
    if ($beforeManifest -cne $afterManifest) { throw 'VerifyOnly unexpectedly changed the manifest.' }
    Write-Host 'PASS: hidden files, incremental archive, multi-volume checks, VerifyOnly, single restore and full restore.'
} finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
