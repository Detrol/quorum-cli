@echo off
REM Quorum launcher for Windows
setlocal

set "SCRIPT_DIR=%~dp0"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"

REM Check if Python venv exists (install.bat must be run first)
if not exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    echo.
    echo [ERROR] Quorum is not installed.
    echo.
    echo Please run install.bat first:
    echo   install.bat
    echo.
    pause
    exit /b 1
)

REM Check if compiled JS exists
if not exist "%FRONTEND_DIR%\dist\index.js" (
    echo Building frontend...
    cd /d "%FRONTEND_DIR%"
    call npm run build
    cd /d "%SCRIPT_DIR%"
)

REM Tell Node where Python is (so frontend can spawn backend)
set "QUORUM_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe"

REM Set signal file for spinner coordination
set "QUORUM_SIGNAL_FILE=%TEMP%\quorum-ready-%RANDOM%"

echo Starting Quorum...

REM Run Node
node "%FRONTEND_DIR%\dist\index.js"

REM Check for error
if errorlevel 1 (
    echo.
    echo [ERROR] Quorum exited with an error.
    pause
)

REM Cleanup signal file if it exists
if exist "%QUORUM_SIGNAL_FILE%" del "%QUORUM_SIGNAL_FILE%"

endlocal
