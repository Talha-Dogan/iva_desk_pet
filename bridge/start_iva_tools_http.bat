@echo off
cd /d "%~dp0"
echo Iva araclari (HTTP modu) baslatiliyor... Kapatmak icin pencereyi kapat.
venv\Scripts\python.exe tools_http.py
pause
