<#
    Calisma klasorundeki guncel dosyalari bu repoya kopyalar.

    Repo, calisma klasorunun (1 GB'lik firmware agaci) kopyasidir; baglantili degildir.
    Firmware veya araclarda degisiklik yaptiktan sonra bu betigi calistir, sonra commit at.

    Kullanim:
        powershell -ExecutionPolicy Bypass -File scripts\sync_from_workspace.ps1
        powershell -ExecutionPolicy Bypass -File scripts\sync_from_workspace.ps1 -Workspace "D:\iva"
#>
param(
    [string]$Workspace = "C:\Users\Talha\Desktop\iva"
)

$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..")

$fw = Join-Path $Workspace "xiaozhi-esp32-main"
$br = Join-Path $Workspace "mcp-bridge"
$sv = Join-Path $Workspace "iva-server"

if (-not (Test-Path $fw)) { Write-Error "Firmware klasoru bulunamadi: $fw" }

$map = @(
    @{ src = "$fw\main\display\face_engine.h";        dst = "firmware\main\display\" },
    @{ src = "$fw\main\display\face_engine.cc";       dst = "firmware\main\display\" },
    @{ src = "$fw\main\display\oled_display.h";       dst = "firmware\main\display\" },
    @{ src = "$fw\main\display\oled_display.cc";      dst = "firmware\main\display\" },
    @{ src = "$fw\main\audio\audio_service.cc";       dst = "firmware\main\audio\" },
    @{ src = "$fw\main\audio\audio_service.h";        dst = "firmware\main\audio\" },
    @{ src = "$fw\main\application.cc";               dst = "firmware\main\" },
    @{ src = "$fw\main\CMakeLists.txt";               dst = "firmware\main\" },
    @{ src = "$fw\main\boards\bread-compact-wifi\config.h";              dst = "firmware\main\boards\bread-compact-wifi\" },
    @{ src = "$fw\main\boards\bread-compact-wifi\compact_wifi_board.cc"; dst = "firmware\main\boards\bread-compact-wifi\" },
    @{ src = "$br\mcp_pipe.py";              dst = "bridge\" },
    @{ src = "$br\tools.py";                 dst = "bridge\" },
    @{ src = "$br\tools_http.py";            dst = "bridge\" },
    @{ src = "$br\start_iva_bridge.bat";     dst = "bridge\" },
    @{ src = "$br\start_iva_tools_http.bat"; dst = "bridge\" },
    @{ src = "$sv\docker-compose.yml";       dst = "server\" },
    @{ src = "$sv\data\test_turkish.py";     dst = "server\tests\" },
    @{ src = "$sv\data\test_mcp.py";         dst = "server\tests\" }
)

$copied = 0
foreach ($m in $map) {
    if (Test-Path $m.src) {
        Copy-Item $m.src (Join-Path $repo $m.dst) -Force
        $copied++
    } else {
        Write-Warning "atlandi (bulunamadi): $($m.src)"
    }
}

# sdkconfig ozel: adi degisiyor ve gizli bilgi icermemeli
$sdk = Join-Path $fw "sdkconfig"
if (Test-Path $sdk) {
    Copy-Item $sdk (Join-Path $repo "firmware\sdkconfig.iva") -Force
    $copied++
}

Write-Host "$copied dosya guncellendi."

# Guvenlik: gizli bilgi taramasi (kalip parcali yazildi ki bu betik kendini
# yanlislikla "sizinti" olarak yakalamasin)
$patterns = ('gsk' + '_[A-Za-z0-9]{20,}') + '|' + ('\d{9,10}:' + 'AA[A-Za-z0-9_-]{30,}') + '|' + ('token=' + 'eyJ')
$selfName = Split-Path -Leaf $MyInvocation.MyCommand.Path
$hits = Get-ChildItem $repo -Recurse -File |
        Where-Object { $_.FullName -notmatch "\\\.git\\" -and $_.Name -ne $selfName } |
        Select-String -Pattern $patterns -List -ErrorAction SilentlyContinue

if ($hits) {
    Write-Host ""
    Write-Host "!! DIKKAT: gizli bilgi bulundu, COMMIT ATMA:" -ForegroundColor Red
    $hits | ForEach-Object { Write-Host "   $($_.Path)" -ForegroundColor Red }
    exit 1
}

Write-Host "Gizli bilgi taramasi temiz. Simdi commit atabilirsin:" -ForegroundColor Green
Write-Host "   git add -A; git commit -m 'guncelleme'; git push"
