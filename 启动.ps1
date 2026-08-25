$dir = $PSScriptRoot
$script = Join-Path $dir 'window_opacity.py'
$pythonw = Get-Command pythonw -ErrorAction SilentlyContinue
$python = Get-Command python -ErrorAction SilentlyContinue
$exe = $null
$argsList = @()
if ($pythonw) {
    $exe = $pythonw.Source
    $argsList = @($script)
} elseif ($python) {
    $exe = $python.Source
    $argsList = @($script)
}
if (-not $exe) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show('未找到 Python。请先安装 Python 3，并勾选 Add python.exe to PATH。', '窗口透明度')
    exit 1
}
Start-Process -FilePath $exe -ArgumentList $argsList -WorkingDirectory $dir -WindowStyle Hidden

$ahk = 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe'
if (-not (Test-Path $ahk)) {
    $ahk = 'C:\Program Files\AutoHotkey\v2\AutoHotkey.exe'
}
$ahkScript = Join-Path $dir 'wallpaper_click_passthrough.ahk'
if ((Test-Path $ahk) -and (Test-Path $ahkScript)) {
    Start-Process -FilePath $ahk -ArgumentList "`"$ahkScript`"" -WorkingDirectory $dir
}