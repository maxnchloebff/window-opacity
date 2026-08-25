$dir = $PSScriptRoot
$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$lnkPath = Join-Path $startup '窗口透明度.lnk'
$vbs = Join-Path $dir '启动.vbs'
$w = New-Object -ComObject WScript.Shell
$lnk = $w.CreateShortcut($lnkPath)
$lnk.TargetPath = $vbs
$lnk.WorkingDirectory = $dir
$lnk.WindowStyle = 7
$lnk.Description = 'Alt+滚轮调节窗口透明度，最大化时透视桌面'
$ico = Join-Path $dir 'icons\window-opacity.ico'
if (Test-Path -LiteralPath $ico) {
    $lnk.IconLocation = $ico
}
$lnk.Save()
Write-Host "已添加到开机启动: $lnkPath"