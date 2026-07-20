<#
    Iva otomatik baslatma kisayollarini kaldirir.
    Kullanim: powershell -ExecutionPolicy Bypass -File scripts\uninstall_autostart.ps1
#>
$startup = [Environment]::GetFolderPath("Startup")
$names = @("Iva Bridge.lnk", "Iva Tools HTTP.lnk")
$removed = 0

foreach ($n in $names) {
    $p = Join-Path $startup $n
    if (Test-Path $p) {
        Remove-Item $p -Force
        Write-Host "kaldirildi: $p"
        $removed++
    }
}

if ($removed -eq 0) {
    Write-Host "Kaldirilacak kisayol bulunamadi."
} else {
    Write-Host "$removed kisayol kaldirildi. Calisan servisler kapatilmadi;"
    Write-Host "istersen gorev yoneticisinden python.exe surecini kapatabilirsin."
}
