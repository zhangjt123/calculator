@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [1/2] First run: creating environment and installing dependencies...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo Python not found. Please install Python 3.10+ and check "Add to PATH".
        pause
        exit /b 1
    )
    .venv\Scripts\python.exe -m pip install -q -r backend\requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies. Check your network and try again.
        pause
        exit /b 1
    )
)

echo [2/2] Starting calculator... browser will open automatically.
echo Close this window or press Ctrl+C to stop.
.venv\Scripts\python.exe backend\main.py

pause
