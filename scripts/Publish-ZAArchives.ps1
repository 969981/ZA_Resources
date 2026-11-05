[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$Version = 'v2.0.2',
    [string]$NcaDirectory = '4a70b3ff963bfe412681185cea68bf55_NCA',
    [string]$SevenZip = '',
    [ValidateRange(100,650)][int]$BatchMiB = 500,
    [switch]$Commit,
    [switch]$Push,
    [string]$Remote = 'origin',
    [string]$Branch = 'master'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($Push -and -not $Commit) { throw '-Push requires -Commit. Default behavior is plan-only.' }
$repoRoot = (Resolve-Path -LiteralPath $RepositoryRoot).ProviderPath.TrimEnd([char[]]@('\','/'))
$manifestRel = "manifests/$Version/transfer_manifest.json"
$manifestPath = Join-Path $repoRoot ($manifestRel.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw "Manifest missing: $manifestPath" }
$manifest = Get-Content -LiteralPath $manifestPath -Encoding UTF8 -Raw | ConvertFrom-Json
if ($manifest.schemaVersion -ne 1 -or $manifest.version -cne $Version -or $manifest.ncaDirectory -cne $NcaDirectory) {
    throw 'Manifest schema, version or NCA mismatch.'
}
function Git([string[]]$GitArgs) {
    $output = @(& git -C $repoRoot @GitArgs)
    if ($LASTEXITCODE -ne 0) { throw "git $($GitArgs -join ' ') failed with exit code $LASTEXITCODE" }
    return $output
}
function RemoteHead {
    $result = @(Git @('ls-remote', '--heads', $Remote, $Branch))
    if ($result.Count -ne 1) { throw "Cannot read remote branch $Remote/$Branch" }
    return ($result[0] -split '\s+')[0]
}
function Save-Batch([object[]]$Items, [int]$BatchNo, [int]$Total) {
    if ($Items.Count -eq 0) { return }
    $label = "data: ZA $Version RomFS archive batch $BatchNo/$Total"
    if (-not $Commit) { return }
    & git -C $repoRoot add -- @Items
    if ($LASTEXITCODE -ne 0) { throw "git add failed for batch $BatchNo" }
    $staged = @(Git @('diff', '--cached', '--name-only'))
    if ($staged.Count -eq 0) { return }
    $previousHead = @(Git @('rev-parse', 'HEAD'))[0]
    & git -C $repoRoot commit -m $label
    if ($LASTEXITCODE -ne 0) { throw "git commit failed for batch $BatchNo" }
    if ($Push) {
        if ((RemoteHead) -cne $previousHead) {
            throw 'Remote branch moved; refusing push. Local commit is preserved. Inspect and reconcile manually.'
        }
        & git -C $repoRoot push $Remote ("HEAD:refs/heads/" + $Branch)
        if ($LASTEXITCODE -ne 0) { throw 'git push failed. Local commit is preserved; no force push was attempted.' }
    }
}
$gitTop = @(Git @('rev-parse','--show-toplevel'))[0]
if (-not [System.IO.Path]::GetFullPath($gitTop).Equals([System.IO.Path]::GetFullPath($repoRoot), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'RepositoryRoot must be the actual Git worktree root.'
}
$currentBranch = @(Git @('symbolic-ref','--short','HEAD'))[0]
if ($currentBranch -cne $Branch) { throw "Current branch is $currentBranch, expected $Branch" }
$stagedBefore = @(Git @('diff', '--cached', '--name-only'))
if ($stagedBefore.Count -gt 0) { throw 'Git index already has staged changes; refusing to mix them with ZA files.' }

# Verify all artifact hashes and archives before staging any bytes.
& (Join-Path $PSScriptRoot 'Verify-ZAArchives.ps1') -RepositoryRoot $repoRoot -Version $Version -NcaDirectory $NcaDirectory -SevenZip $SevenZip

$ordered = New-Object System.Collections.Generic.List[string]
$sizeByPath = @{}
foreach ($record in @($manifest.files)) {
    foreach ($artifact in @($record.artifacts)) {
        $path = [string]$artifact.path
        if ($path -match '(^|/)\.\.?(/|$)' -or $path.StartsWith('/') -or $path.Contains('\') -or
            [System.IO.Path]::IsPathRooted($path)) {
            throw "Unsafe artifact path: $path"
        }
        $full = [System.IO.Path]::GetFullPath((Join-Path $repoRoot ($path.Replace('/', [System.IO.Path]::DirectorySeparatorChar))))
        if (-not $full.StartsWith(($repoRoot + [System.IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) {
            throw "Artifact escapes repo: $path"
        }
        $size = [long]$artifact.sizeBytes
        if ($size -ge 100000000) { throw "Artifact is larger than GitHub's 100 MB limit: $path" }
        if ($sizeByPath.ContainsKey($path)) { throw "Duplicate artifact path in manifest: $path" }
        $ordered.Add($path)
        $sizeByPath[$path] = $size
    }
}
$allowed = @{}
foreach ($path in $ordered) { $allowed[$path] = $true }
$allowed[$manifestRel] = $true
$status = @(Git @('status','--porcelain=v1','-uall'))
$pending = @{}
foreach ($line in $status) {
    if ($line.Length -lt 4) { continue }
    $path = $line.Substring(3)
    if ($path.StartsWith('"')) { throw "Quoted Git status path needs manual review: $path" }
    if (-not $allowed.ContainsKey($path)) {
        if ($Commit) { throw "Unrelated working-tree change; refusing commit: $path" }
        Write-Warning "Unrelated change (not included): $path"
        continue
    }
    $pending[$path] = $true
}
$maxBatch = [long]$BatchMiB * 1MB
$batches = New-Object System.Collections.Generic.List[object]
$items = New-Object System.Collections.Generic.List[string]
$bytes = [long]0
foreach ($path in $ordered) {
    if (-not $pending.ContainsKey($path)) { continue }
    $size = [long]$sizeByPath[$path]
    if ($items.Count -gt 0 -and ($bytes + $size) -gt $maxBatch) {
        $batches.Add(@($items.ToArray()))
        $items = New-Object System.Collections.Generic.List[string]
        $bytes = [long]0
    }
    $items.Add($path)
    $bytes += $size
}
if ($items.Count -gt 0) { $batches.Add(@($items.ToArray())) }
for ($i=0; $i -lt $batches.Count; $i++) {
    $batch = @($batches[$i])
    $batchBytes = [long]0
    foreach ($path in $batch) { $batchBytes += [long]$sizeByPath[$path] }
    Write-Host ("BATCH {0}/{1}: {2} files, {3:N1} MiB" -f ($i+1), $batches.Count, $batch.Count, ($batchBytes / 1MB))
}
if ($pending.ContainsKey($manifestRel)) { Write-Host 'FINAL: commit manifest after all artifact batches.' }
if (-not $Commit) {
    Write-Host 'PLAN ONLY. Nothing staged, committed or pushed. Supply -Commit and optionally -Push to execute.'
    return
}
if ($Push) {
    $localHead = @(Git @('rev-parse','HEAD'))[0]
    if ((RemoteHead) -cne $localHead) {
        throw 'Local HEAD and remote HEAD differ. Refusing to push or rebase automatically.'
    }
}
for ($i=0; $i -lt $batches.Count; $i++) {
    Save-Batch -Items @($batches[$i]) -BatchNo ($i+1) -Total $batches.Count
}
if ($pending.ContainsKey($manifestRel)) {
    Save-Batch -Items @($manifestRel) -BatchNo ($batches.Count+1) -Total ($batches.Count+1)
}
Write-Host ("DONE. Commit={0}; Push={1}; artifact batches={2}" -f [bool]$Commit, [bool]$Push, $batches.Count)
