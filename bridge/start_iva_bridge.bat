@echo off
cd /d "%~dp0"
echo Iva MCP koprusu baslatiliyor... Kapatmak icin bu pencereyi kapat.
venv\Scripts\python.exe mcp_pipe.py tools.py
pause
