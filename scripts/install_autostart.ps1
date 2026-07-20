<#
    Iva'yi Windows acilisinda otomatik baslatir.

    Kullanim:
        powershell -ExecutionPolicy Bypass -File scripts\install_autostart.ps1
        powershell -ExecutionPolicy Bypass -File scripts\install_autostart.ps1 -BridgeDir "C:\yol\mcp-bridge"
        powershell -ExecutionPolicy Bypass -File scripts\install_autostart.ps1 -Mode http

    Mode:
        bridge  -> resmi sunucu (xiaozhi.me) icin websocket koprusu   [varsayilan]
        http    -> kendi sunucun icin HTTP arac servisi
        both    -> ikisi birden
#>
param(
    [string]$BridgeDir = "",
    [ValidateSet("bridge", "http", "both")]
    [string]$Mode = "bridge"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $BridgeDir) {
    $BridgeDir = Resolve-Path (Join-Path $scriptDir "..\bridge")
}

if (-not (Test-Path (Join-Path $BridgeDir "tools.py"))) {
    Write-Error "tools.py bulunamadi: $BridgeDir  (-BridgeDir ile dogru klasoru ver)"
}
if (-not (Test-Path (Join-Path $BridgeDir "venv\Scripts\python.exe"))) {
    Write-Warning "venv yok. Once setup.ps1 calistir, sonra bu betigi tekrar cagir."
}

$vbs = Join-Path $scriptDir "iva_start_hidden.vbs"
$startup = [Environment]::GetFolderPath("Startup")
$wsh = New-Object -ComObject WScript.Shell

function New-IvaShortcut($name, $batName) {
    $lnkPath = Join-Path $startup "$name.lnk"
    $lnk = $wsh.CreateShortcut($lnkPath)
    $lnk.TargetPath = "wscript.exe"
    $lnk.Arguments = "`"$vbs`" `"$BridgeDir`" `"$batName`""
    $lnk.WorkingDirectory = $BridgeDir
    $lnk.Description = "Iva masa robotu - $batName"
    $lnk.Save()
    Write-Host "  eklendi: $lnkPath"
}

Write-Host "Iva otomatik baslatma kuruluyor..."
Write-Host "  klasor: $BridgeDir"

if ($Mode -eq "bridge" -or $Mode -eq "both") {
    New-IvaShortcut "Iva Bridge" "start_iva_bridge.bat"
}
if ($Mode -eq "http" -or $Mode -eq "both") {
    New-IvaShortcut "Iva Tools HTTP" "start_iva_tools_http.bat"
}

Write-Host ""
Write-Host "Tamam. Bilgisayar her acildiginda Iva araclari arka planda baslayacak."
Write-Host "Kaldirmak icin: scripts\uninstall_autostart.ps1"
Write-Host ""
Write-Host "Kendi sunucunu kullaniyorsan Docker Desktop ayarlarindan"
Write-Host "'Start Docker Desktop when you sign in' secenegini de ac."
