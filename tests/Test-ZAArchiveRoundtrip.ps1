[CmdletBinding()]
param(
    [string]$SevenZip = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoScripts = Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts'
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('ZA-Archive-Test-' + [guid]::NewGuid().ToString('N'))
$source = Join-Path $tempRoot 'source'
$repo = Join-Path $tempRoot 'repo'
$restored = Join-Path $tempRoot 'restored'
$arc = Join-Path $source 'arc'
$audio = Join-Path $source 'audio/wwise/bin/Switch'
New-Item -ItemType Directory -Path $arc -Force | Out-Null
New-Item -ItemType Directory -Path $audio -Force | Out-Null
New-Item -ItemType Directory -Path $repo -Force | Out-Null
'Test-only repository; no game material' | Set-Content -LiteralPath (Join-Path $repo 'AGENTS.md')
try {
    $rng = New-Object System.Random 247
    [byte[]]$small = [byte[]]::new(257)
    [byte[]]$large = [byte[]]::new((2 * 1024 * 1024) + 333)
    [byte[]]$audioBytes = [byte[]]::new(1024)
    $rng.NextBytes($small)
    $rng.NextBytes($large)
    $rng.NextBytes($audioBytes)
    [System.IO.File]::WriteAllBytes((Join-Path $arc 'data.trpfd'), $small)
    [System.IO.File]::WriteAllBytes((Join-Path $arc 'data.trpfs'), $large)
    [System.IO.File]::WriteAllBytes((Join-Path $audio 'UI.bnk'), $audioBytes)

    $params = @{
        SourceRomfsRoot = $source
        RepositoryRoot = $repo
        SevenZip = $SevenZip
        ThresholdMiB = 1
        VolumeMiB = 1
        CompressionLevel = 1
    }
    & (Join-Path $repoScripts 'Archive-ZAResources.ps1') @params
    & (Join-Path $repoScripts 'Archive-ZAResources.ps1') @params
    $manifestPath = Join-Path $repo 'manifests/v2.0.2/transfer_manifest.json'
    if (-not (Test-Path -LiteralPath $manifestPath)) { throw 'Manifest missing after archive.' }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (@($manifest.files).Count -ne 3) { throw 'Expected three source files.' }
    $largeRecord = @($manifest.files | Where-Object { $_.sourceRelativePath -eq 'arc/data.trpfs' })
    if ($largeRecord.Count -ne 1 -or $largeRecord[0].representation -ne '7z-volumes') {
        throw 'Large resource was not archived into 7z volumes.'
    }
    if (@($largeRecord[0].artifacts).Count -lt 2) { throw 'Expected split archive of at least two volumes.' }
    $archive = Join-Path $repo 'v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/1/arc/data.trpfs.7z.001'
    if (-not (Test-Path -LiteralPath $archive)) { throw 'Expected first .7z.001 volume.' }

    & (Join-Path $repoScripts 'Verify-ZAArchives.ps1') -RepositoryRoot $repo -SevenZip $SevenZip -Full
    & (Join-Path $repoScripts 'Restore-ZAResources.ps1') -RepositoryRoot $repo -SevenZip $SevenZip -DestinationRoot $restored
    foreach ($path in @('arc/data.trpfd','arc/data.trpfs','audio/wwise/bin/Switch/UI.bnk')) {
        $src = Join-Path $source $path
        $dst = Join-Path $restored $path
        if (-not (Test-Path -LiteralPath $dst) -or
            (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash -ne
            (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash) {
            throw "Round-trip differs: $path"
        }
    }
    # Corruption of even one stored volume must fail SHA-256 verification.
    [byte[]]$partBytes = [System.IO.File]::ReadAllBytes($archive)
    [byte[]]$corrupted = [byte[]]$partBytes.Clone()
    $corrupted[2] = $corrupted[2] -bxor 1
    try {
        [System.IO.File]::WriteAllBytes($archive, $corrupted)
        $caught = $false
        try {
            & (Join-Path $repoScripts 'Verify-ZAArchives.ps1') -RepositoryRoot $repo -SevenZip $SevenZip
        } catch {
            $caught = $true
        }
        if (-not $caught) { throw 'Integrity checker did not detect corrupted archive bytes.' }
    } finally {
        [System.IO.File]::WriteAllBytes($archive, $partBytes)
    }
    Write-Host 'PASS synthetic ZA archive / resume / manifest / verify / restore / corruption test.'
} finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
