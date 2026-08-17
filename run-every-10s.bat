@echo off
setlocal

rem Always run from the folder containing this script.
cd /d "%~dp0"

:loop
echo [%date% %time%]
uv run python main.py
timeout /t 10 /nobreak >nul
goto loop
