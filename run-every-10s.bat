@echo off
setlocal

rem Always run from the folder containing this script.
cd /d "%~dp0"

echo Running "uv run python3 main.py" every 10 seconds.
echo Press Ctrl+C to stop.

:loop
echo.
echo [%date% %time%] Starting...

call uv run python3 main.py
set "exit_code=%errorlevel%"

if not "%exit_code%"=="0" (
    echo Command exited with code %exit_code%. It will be retried.
)

echo Waiting 10 seconds...
timeout /t 10 /nobreak >nul
goto loop
