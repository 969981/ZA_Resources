# Export-PokemonZAInventory.ps1
# PowerShell 5.1+; recursively inventories the files already extracted under v2.0.2.
# Does NOT unpack Trinity data.trpfs or Wwise audio banks.
[CmdletBinding()]
param(
    [string]$Root = '.\v2.0.2',
    [string]$OutCsv = '',
    [switch]$IncludeSHA1,
    [switch]$SkipHash
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$rootPath = (Resolve-Path -LiteralPath $Root).ProviderPath.TrimEnd([char[]]@('\','/'))
if (-not (Test-Path -LiteralPath $rootPath -PathType Container)) {
    throw "Not a directory: $rootPath"
}
if (-not $OutCsv) {
    $OutCsv = Join-Path (Get-Location).Path ((Split-Path -Leaf $rootPath) + '_file_inventory.csv')
}
$outFull = [System.IO.Path]::GetFullPath($ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutCsv))

function HexBytes([byte[]]$data) {
    if ($null -eq $data -or $data.Length -eq 0) { return '' }
    return [BitConverter]::ToString($data).Replace('-', '')
}
function ReadBytes([System.IO.Stream]$stream, [int]$length) {
    if ($length -le 0) { return ,([byte[]]@()) }
    $buf = New-Object byte[] $length
    $got = 0
    while ($got -lt $length) {
        $n = $stream.Read($buf, $got, $length - $got)
        if ($n -le 0) { break }
        $got += $n
    }
    if ($got -eq $length) { return ,$buf }
    if ($got -eq 0) { return ,([byte[]]@()) }
    $res = New-Object byte[] $got
    [Array]::Copy($buf, $res, $got)
    return ,$res
}
function ToAscii([byte[]]$data) {
    $builder = New-Object System.Text.StringBuilder
    foreach ($b in $data) {
        if ($b -ge 32 -and $b -le 126) { [void]$builder.Append([char]$b) }
        else { [void]$builder.Append('.') }
    }
    return $builder.ToString()
}
function HashStream([System.IO.Stream]$stream, [string]$algorithm) {
    [void]$stream.Seek(0, [System.IO.SeekOrigin]::Begin)
    $algo = [System.Security.Cryptography.HashAlgorithm]::Create($algorithm)
    if ($null -eq $algo) { throw "Hash algorithm unavailable: $algorithm" }
    try { return (HexBytes ($algo.ComputeHash($stream))) }
    finally { $algo.Dispose() }
}

$rows = [System.Collections.Generic.List[object]]::new()
$files = @(Get-ChildItem -LiteralPath $rootPath -Recurse -File | Sort-Object FullName)
$index = 0
foreach ($file in $files) {
    $index++
    $relative = $file.FullName.Substring($rootPath.Length).TrimStart([char[]]@('\','/')).Replace('\', '/')
    $parts = $relative.Split('/')
    $region = 'Other'
    for ($i = 0; $i -lt $parts.Length - 1; $i++) {
        if ($parts[$i] -eq '0') { $region = 'ExeFS'; break }
        if ($parts[$i] -eq '1') { $region = 'RomFS'; break }
    }
    $head = [byte[]]@(); $tail = [byte[]]@(); $moduleId = ''
    $sha256 = ''; $sha1 = ''; $errorText = ''
    try {
        $fs = [System.IO.File]::Open($file.FullName, [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            # Avoid Math.Min/Max Int32 overloads: Trinity archives can exceed 2 GiB.
            $headCount = if ($fs.Length -ge 64) { 64 } else { [int]$fs.Length }
            $tailCount = if ($fs.Length -ge 32) { 32 } else { [int]$fs.Length }
            $tailOffset = if ($fs.Length -gt 32) { [long]($fs.Length - 32) } else { [long]0 }
            $head = ReadBytes $fs $headCount
            [void]$fs.Seek($tailOffset, [System.IO.SeekOrigin]::Begin)
            $tail = ReadBytes $fs $tailCount
            if ($head.Length -ge 4 -and (ToAscii $head[0..3]) -eq 'NSO0' -and $fs.Length -ge 96) {
                [void]$fs.Seek(64, [System.IO.SeekOrigin]::Begin)
                $moduleId = HexBytes (ReadBytes $fs 32)
            }
            if (-not $SkipHash) {
                $sha256 = HashStream $fs 'SHA256'
                if ($IncludeSHA1) { $sha1 = HashStream $fs 'SHA1' }
            }
        }
        finally { $fs.Dispose() }
    }
    catch { $errorText = $_.Exception.Message }

    $magicBytes = [byte[]]@()
    if ($head.Length -gt 0) {
        $magicBytes = [byte[]]$head[0..([Math]::Min(4, $head.Length) - 1)]
    }
    $magic = ToAscii $magicBytes
    $kind = switch ($magic) {
        'NSO0' { 'Nintendo Switch NSO'; break }
        'META' { 'Nintendo Switch NPDM'; break }
        'BKHD' { 'Wwise SoundBank'; break }
        'AKPK' { 'Wwise File Package'; break }
        default { 'Unknown (see extension)' }
    }
    $rows.Add([PSCustomObject][ordered]@{
        RelativePath       = $relative
        Region             = $region
        Extension          = $file.Extension.ToLowerInvariant()
        SizeBytes          = $file.Length
        SizeMiB            = [Math]::Round($file.Length / 1MB, 3)
        Magic4Hex          = HexBytes $magicBytes
        Magic4ASCII        = $magic
        Header64Hex        = HexBytes $head
        Tail32Hex          = HexBytes $tail
        FileTypeByMagic    = $kind
        NSO_ModuleId_0x40  = $moduleId
        SHA256             = $sha256
        SHA1               = $sha1
        ModifiedUTC        = $file.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')
        Error              = $errorText
    })
    Write-Progress -Activity 'ZA file inventory' -Status "$index / $($files.Length): $relative" -PercentComplete ([int](100 * $index / [Math]::Max(1, $files.Length)))
}
Write-Progress -Activity 'ZA file inventory' -Completed

$parent = Split-Path -Parent $outFull
if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
    [void](New-Item -ItemType Directory -Path $parent -Force)
}
if ($rows.Count -eq 0) {
    'RelativePath,Region,Extension,SizeBytes,SizeMiB,Magic4Hex,Magic4ASCII,Header64Hex,Tail32Hex,FileTypeByMagic,NSO_ModuleId_0x40,SHA256,SHA1,ModifiedUTC,Error' | Set-Content -LiteralPath $outFull -Encoding UTF8
}
else {
    $rows | Export-Csv -LiteralPath $outFull -NoTypeInformation -Encoding UTF8
}
Write-Host "Exported $($rows.Count) files -> $outFull"