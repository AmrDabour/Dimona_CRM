<#
.SYNOPSIS
  Fast Recycle Bin restore: reads $I/$R pairs under $Recycle.Bin (no Shell COM).

.DESCRIPTION
  Parses Windows 10+ style $I metadata (version 2). Works regardless of UI language.
  Default: items deleted on the same local calendar day as -OnDate (default: today).

.PARAMETER PathFilter
  Original path must contain this substring (recommended: dimora or part of project path).

.PARAMETER OnDate
  Calendar day to match (local). Default: today.

.PARAMETER Restore
  Copy $R back to original path and remove $I/$R. Without -Restore: list only.

.PARAMETER Force
  Overwrite destination if file already exists.

.PARAMETER ExcludeNodeModules
  Skip paths containing \node_modules\ (default: true). Set -ExcludeNodeModules:$false to include them.

.PARAMETER ShowAllPaths
  Print every matching path. Default: first 40 + summary (much faster on huge bins).

.EXAMPLE
  .\scripts\restore-recycle-today.ps1 -PathFilter "X:\AI\dimora crm"
.EXAMPLE
  .\scripts\restore-recycle-today.ps1 -PathFilter "dimora" -ExcludeNodeModules:$false -ShowAllPaths
.EXAMPLE
  .\scripts\restore-recycle-today.ps1 -PathFilter "X:\AI\dimora crm" -Restore
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$PathFilter = "",
    [DateTime]$OnDate = (Get-Date).Date,
    [switch]$Restore,
    [switch]$Force,
    [switch]$ShowAllPaths,
    [bool]$ExcludeNodeModules = $true
)

$ErrorActionPreference = "Stop"
$targetDay = $OnDate.Date

function Find-V2HeaderOffset {
    param([byte[]]$Bytes)
    $lim = [Math]::Min(72, [Math]::Max(0, $Bytes.Length - 28))
    for ($i = 0; $i -le $lim; $i++) {
        if ($Bytes[$i] -ne 2) { continue }
        $pc = [BitConverter]::ToInt32($Bytes, $i + 24)
        if ($pc -gt 0 -and $pc -lt 40000 -and ($i + 28 + $pc * 2) -le $Bytes.Length) {
            return $i
        }
    }
    return -1
}

function Parse-RecycleIMetadata {
    param([string]$IFilePath)
    try {
        $bytes = [System.IO.File]::ReadAllBytes($IFilePath)
    } catch {
        return $null
    }
    if ($bytes.Length -lt 32) { return $null }

    $off = Find-V2HeaderOffset -Bytes $bytes
    if ($off -lt 0) { return $null }

    try {
        $ft = [BitConverter]::ToInt64($bytes, $off + 16)
        if ($ft -le 0) { return $null }
        $deletedLocal = [DateTime]::FromFileTimeUtc($ft).ToLocalTime()
        $pathChars = [BitConverter]::ToInt32($bytes, $off + 24)
        if ($pathChars -lt 1 -or $pathChars -gt 40000) { return $null }
        $pathStart = $off + 28
        $need = $pathChars * 2
        if ($pathStart + $need -gt $bytes.Length) { return $null }
        $pathBytes = New-Object byte[] $need
        [Array]::Copy($bytes, $pathStart, $pathBytes, 0, $need)
        $orig = [System.Text.Encoding]::Unicode.GetString($pathBytes).TrimEnd([char]0)
        if ([string]::IsNullOrWhiteSpace($orig)) { return $null }
        return [PSCustomObject]@{
            DeletedLocal = $deletedLocal
            OriginalPath = $orig
        }
    } catch {
        return $null
    }
}

function Get-RecycleBinRootPaths {
    $roots = [System.Collections.Generic.List[string]]::new()
    foreach ($di in [System.IO.DriveInfo]::GetDrives()) {
        if ($di.DriveType -ne [System.IO.DriveType]::Fixed) { continue }
        if (-not $di.IsReady) { continue }
        $rb = Join-Path $di.RootDirectory.FullName '$Recycle.Bin'
        if (Test-Path -LiteralPath $rb) {
            [void]$roots.Add($rb)
        }
    }
    return $roots
}

function Get-RFileForI {
    param([string]$IPath)
    $dir = [System.IO.Path]::GetDirectoryName($IPath)
    $name = [System.IO.Path]::GetFileName($IPath)
    if ($name.Length -lt 3 -or -not $name.StartsWith('$I')) { return $null }
    $rName = '$R' + $name.Substring(2)
    $rPath = Join-Path $dir $rName
    if (Test-Path -LiteralPath $rPath) { return $rPath }
    return $null
}

$rbRoots = Get-RecycleBinRootPaths
if ($rbRoots.Count -eq 0) {
    Write-Warning 'No $Recycle.Bin folder found on fixed drives.'
    exit 1
}

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$candidates = [System.Collections.Generic.List[object]]::new()

foreach ($root in $rbRoots) {
    [string[]]$sidDirs = @()
    try {
        $sidDirs = [System.IO.Directory]::GetDirectories($root)
    } catch {
        continue
    }
    foreach ($sidDir in $sidDirs) {
        [string[]]$iFiles = @()
        try {
            $iFiles = [System.IO.Directory]::EnumerateFiles($sidDir, '$I*', [System.IO.SearchOption]::TopDirectoryOnly)
        } catch {
            continue
        }
        foreach ($iPath in $iFiles) {
            $meta = Parse-RecycleIMetadata -IFilePath $iPath
            if (-not $meta) { continue }
            if ($meta.DeletedLocal.Date -ne $targetDay) { continue }
            $orig = $meta.OriginalPath
            if ($PathFilter -and ($orig -notlike "*$PathFilter*")) { continue }
            if ($ExcludeNodeModules -and ($orig -like '*\node_modules\*' -or $orig -like '*\node_modules')) { continue }
            $rPath = Get-RFileForI -IPath $iPath
            if (-not $rPath) { continue }
            [void]$candidates.Add([PSCustomObject]@{
                    IPath        = $iPath
                    RPath        = $rPath
                    DeletedLocal = $meta.DeletedLocal
                    OriginalPath = $orig
                })
        }
    }
}

$sw.Stop()

if ($candidates.Count -eq 0) {
    Write-Host "No matching items (delete day = $($targetDay.ToString('yyyy-MM-dd')) local)." -ForegroundColor Yellow
    if ($PathFilter) { Write-Host "PathFilter: '$PathFilter'" -ForegroundColor DarkGray }
    Write-Host ("Scanned in {0:n0} ms." -f $sw.ElapsedMilliseconds) -ForegroundColor DarkGray
    exit 0
}

Write-Host ""
Write-Host ("Found {0} item(s) in {1:n0} ms." -f $candidates.Count, $sw.ElapsedMilliseconds) -ForegroundColor Cyan
$preview = 40
if ($ShowAllPaths) {
    $candidates | ForEach-Object { Write-Host ("  {0}" -f $_.OriginalPath) }
} else {
    $n = 0
    foreach ($x in $candidates) {
        if ($n -ge $preview) { break }
        Write-Host ("  {0}" -f $x.OriginalPath)
        $n++
    }
    if ($candidates.Count -gt $preview) {
        Write-Host ("  ... and {0} more (add -ShowAllPaths to list all)" -f ($candidates.Count - $preview)) -ForegroundColor DarkGray
    }
}

if (-not $Restore) {
    Write-Host ""
    Write-Host "Add -Restore to copy back and remove from Recycle Bin (use -PathFilter to limit scope)." -ForegroundColor DarkYellow
    exit 0
}

$ok = 0
$fail = 0
foreach ($c in $candidates) {
    $dest = $c.OriginalPath
    if (-not $PSCmdlet.ShouldProcess($dest, "Restore from Recycle Bin")) { continue }
    try {
        $destDir = [System.IO.Path]::GetDirectoryName($dest)
        if (-not [string]::IsNullOrEmpty($destDir) -and -not (Test-Path -LiteralPath $destDir)) {
            [System.IO.Directory]::CreateDirectory($destDir) | Out-Null
        }
        $isDir = Test-Path -LiteralPath $c.RPath -PathType Container
        if (Test-Path -LiteralPath $dest) {
            if (-not $Force) {
                Write-Warning "Skip (exists): $dest  (use -Force to overwrite)"
                $fail++
                continue
            }
            if ((Get-Item -LiteralPath $dest) -is [System.IO.DirectoryInfo]) {
                Remove-Item -LiteralPath $dest -Recurse -Force
            } else {
                Remove-Item -LiteralPath $dest -Force
            }
        }
        if ($isDir) {
            Copy-Item -LiteralPath $c.RPath -Destination $dest -Recurse -Force
        } else {
            Copy-Item -LiteralPath $c.RPath -Destination $dest -Force
        }
        Remove-Item -LiteralPath $c.IPath -Force -ErrorAction Stop
        Remove-Item -LiteralPath $c.RPath -Force -Recurse -ErrorAction Stop
        $ok++
    } catch {
        $fail++
        Write-Warning ("Failed: {0} - {1}" -f $dest, $_.Exception.Message)
    }
}

Write-Host ""
Write-Host ("Done: restored {0} | skipped/failed {1}" -f $ok, $fail) -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Yellow" })
