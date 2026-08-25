$dir = $PSScriptRoot
$programs = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
if (-not (Test-Path $programs)) {
    New-Item -ItemType Directory -Path $programs | Out-Null
}
$lnkPath = Join-Path $programs '窗口透明度.lnk'
$script = Join-Path $dir 'window_opacity.py'
$vbs = Join-Path $dir '启动.vbs'

function Get-PreferredPythonW {
    $candidates = @()
    $anaconda = 'F:\anaconda\pythonw.exe'
    if (Test-Path $anaconda) { $candidates += $anaconda }
    $localPy = Join-Path $env:LOCALAPPDATA 'Programs\Python'
    if (Test-Path $localPy) {
        $candidates += @(Get-ChildItem -Path $localPy -Filter pythonw.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
    }
    $pathHits = @(Get-Command pythonw -All -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
    foreach ($hit in $pathHits) {
        if ($hit -match '\\Inkscape\\' ) { continue }
        if ($hit -match '\\.venv\\' ) { continue }
        if ($hit -match '\\venv\\' ) { continue }
        $candidates += $hit
    }
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }
    return $null
}

$pythonw = Get-PreferredPythonW
$w = New-Object -ComObject WScript.Shell
$lnk = $w.CreateShortcut($lnkPath)
if ($pythonw) {
    $lnk.TargetPath = $pythonw
    $lnk.Arguments = '"' + $script + '"'
} else {
    $lnk.TargetPath = $vbs
    $lnk.Arguments = ''
}
$lnk.WorkingDirectory = $dir
$lnk.WindowStyle = 7
$lnk.Description = 'Alt+滚轮调节窗口透明度，最大化时透视桌面'
$ico = Join-Path $dir 'icons\window-opacity.ico'
if (Test-Path -LiteralPath $ico) {
    $lnk.IconLocation = $ico
} else {
    $lnk.IconLocation = (Join-Path $env:SystemRoot 'System32\imageres.dll') + ',109'
}
$lnk.Save()
Write-Output $lnkPath