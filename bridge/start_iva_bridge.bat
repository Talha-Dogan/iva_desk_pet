@echo off
cd /d "%~dp0"
if not exist logs mkdir logs
echo Iva koprusu baslatiliyor... Kayitlar: logs\bridge.log
echo. >> logs\bridge.log
echo ===== %date% %time% baslatildi ===== >> logs\bridge.log
venv\Scripts\python.exe mcp_pipe.py tools.py >> logs\bridge.log 2>&1
echo Kopru durdu. Ayrinti icin logs\bridge.log dosyasina bak.
pause
