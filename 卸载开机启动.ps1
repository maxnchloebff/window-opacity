$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$lnkPath = Join-Path $startup '窗口透明度.lnk'
if (Test-Path $lnkPath) {
    Remove-Item $lnkPath -Force
    Write-Host "已取消开机启动"
} else {
    Write-Host "未找到开机启动项，无需卸载"
}