<#
    Iva - tek komutluk kurulum

    Kullanim (repo klasorunde):
        powershell -ExecutionPolicy Bypass -File setup.ps1

    Secenekler:
        -SkipServer      kendi sunucuyu (Docker) kurma, sadece araclari kur
        -WithServer      Docker sunucusunu da hazirla ve baslat
        -NoAutostart     Windows acilisinda otomatik baslatmayi kurma
        -Mode http       kendi sunucunu kullaniyorsan (varsayilan: bridge)
#>
param(
    [switch]$WithServer,
    [switch]$SkipServer,
    [switch]$NoAutostart,
    [ValidateSet("bridge", "http", "both")]
    [string]$Mode = "bridge"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bridge = Join-Path $root "bridge"
$server = Join-Path $root "server"

function Step($msg) { Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "   [tamam] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "   [dikkat] $msg" -ForegroundColor Yellow }

Write-Host "=== Iva masa robotu - kurulum ===" -ForegroundColor Cyan

# ---------------------------------------------------------------- Python
Step "Python kontrol ediliyor"
$py = $null
foreach ($c in @("py -3", "python")) {
    try {
        $parts = $c.Split(" ")
        $v = & $parts[0] $parts[1..($parts.Length - 1)] --version 2>&1
        if ($LASTEXITCODE -eq 0) { $py = $c; Ok "$v ($c)"; break }
    } catch { }
}
if (-not $py) {
    Write-Error "Python bulunamadi. https://www.python.org/downloads/ adresinden kur (3.10+)."
}

# ---------------------------------------------------------------- venv
Step "Sanal ortam (venv) hazirlaniyor"
$venvPy = Join-Path $bridge "venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    Ok "venv zaten var"
} else {
    Push-Location $bridge
    $parts = $py.Split(" ")
    & $parts[0] $parts[1..($parts.Length - 1)] -m venv venv
    Pop-Location
    Ok "venv olusturuldu"
}

Step "Bagimliliklar kuruluyor (mcp, websockets, requests)"
& $venvPy -m pip install --quiet --upgrade pip
& $venvPy -m pip install --quiet -r (Join-Path $bridge "requirements.txt")
Ok "kuruldu"

# ---------------------------------------------------------------- .env
Step "Ayar dosyasi (.env)"
$envFile = Join-Path $bridge ".env"
if (Test-Path $envFile) {
    Ok ".env zaten var, dokunulmadi"
} else {
    Copy-Item (Join-Path $bridge ".env.example") $envFile
    Ok ".env olusturuldu"
    Warn "Simdi bridge\.env dosyasini ac ve doldur:"
    Warn "  MCP_ENDPOINT       xiaozhi.me -> Extensions -> MCP Endpoint"
    Warn "  TELEGRAM_BOT_TOKEN @BotFather -> /newbot"
    Warn "  TELEGRAM_CHAT_ID   getUpdates ile bulunur (bridge/README.md)"
}

# ---------------------------------------------------------------- sunucu
if ($WithServer -and -not $SkipServer) {
    Step "Kendi sunucun hazirlaniyor (Docker)"
    $dataDir = Join-Path $server "data"
    if (-not (Test-Path $dataDir)) { New-Item -ItemType Directory -Path $dataDir | Out-Null }

    $cfg = Join-Path $dataDir ".config.yaml"
    if (-not (Test-Path $cfg)) {
        Copy-Item (Join-Path $server "config.example.yaml") $cfg
        Ok "data\.config.yaml olusturuldu"
        Warn "Icindeki GROQ_API_ANAHTARIN (2 yer) ve SENIN_YEREL_IP degerlerini duzenle."
    } else {
        Ok "data\.config.yaml zaten var"
    }

    $mcpCfg = Join-Path $dataDir ".mcp_server_settings.json"
    if (-not (Test-Path $mcpCfg)) {
        Copy-Item (Join-Path $server "mcp_server_settings.example.json") $mcpCfg
        Ok "data\.mcp_server_settings.json olusturuldu"
    }

    try {
        docker info --format "{{.ServerVersion}}" | Out-Null
        Push-Location $server
        docker compose up -d
        Pop-Location
        Ok "sunucu baslatildi (docker: iva-server)"
    } catch {
        Warn "Docker calismiyor. Docker Desktop'i ac, sonra: cd server; docker compose up -d"
    }
}

# ---------------------------------------------------------------- autostart
if (-not $NoAutostart) {
    Step "Windows acilisinda otomatik baslatma"
    & (Join-Path $root "scripts\install_autostart.ps1") -BridgeDir $bridge -Mode $Mode
}

# ---------------------------------------------------------------- ozet
Write-Host "`n=== Kurulum bitti ===" -ForegroundColor Cyan
Write-Host @"

Siradaki adimlar:
  1. bridge\.env dosyasini doldur (MCP endpoint + Telegram)
  2. Araclari baslat:  bridge\start_iva_bridge.bat
  3. Firmware icin:    firmware\README.md
  4. Kendi sunucun:    server\README.md

Otomatik baslatma kuruldu; bilgisayari yeniden baslattiginda Iva araclari
arka planda kendiliginden calisacak.
"@
