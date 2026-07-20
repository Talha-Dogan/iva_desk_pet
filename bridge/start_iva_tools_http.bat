@echo off
cd /d "%~dp0"
if not exist logs mkdir logs
echo Iva araclari (HTTP modu) baslatiliyor... Kayitlar: logs\tools_http.log
echo. >> logs\tools_http.log
echo ===== %date% %time% baslatildi ===== >> logs\tools_http.log
venv\Scripts\python.exe tools_http.py >> logs\tools_http.log 2>&1
echo Servis durdu. Ayrinti icin logs\tools_http.log dosyasina bak.
pause
