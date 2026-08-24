$programs = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
$lnkPath = Join-Path $programs '窗口透明度.lnk'
if (Test-Path $lnkPath) {
    Remove-Item $lnkPath -Force
    Write-Output "removed:$lnkPath"
} else {
    Write-Output "missing:$lnkPath"
}