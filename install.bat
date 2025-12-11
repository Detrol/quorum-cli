@echo off
REM Quorum installation script for Windows
setlocal

echo Installing Quorum...
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found. Please install Python 3.11 or higher.
    pause
    exit /b 1
)
echo [OK] Python found
python --version

REM Check Node.js
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Node.js not found. Please install Node.js 18 or higher.
    pause
    exit /b 1
)
echo [OK] Node.js found
node --version

REM Check npm
echo Checking npm...
call npm --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] npm not found. Please install npm.
    pause
    exit /b 1
)
echo [OK] npm found
call npm --version

echo.

REM Check/install uv
echo Checking uv...
call uv --version >nul 2>&1
if errorlevel 1 (
    echo Installing uv...
    call pip install uv
    if errorlevel 1 (
        echo [FAIL] Failed to install uv. Please install manually: pip install uv
        pause
        exit /b 1
    )
)
echo [OK] uv found
call uv --version

echo.

REM Remove incompatible venv if it exists (e.g., from WSL)
if exist .venv (
    if not exist .venv\Scripts\python.exe (
        echo Removing incompatible virtual environment...
        rmdir /s /q .venv
    )
)

REM Install Python dependencies with uv
echo Installing Python dependencies...
call uv sync
if errorlevel 1 (
    echo [FAIL] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed

echo.

REM Install and build frontend
echo Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo [FAIL] Failed to install frontend dependencies
    cd ..
    pause
    exit /b 1
)
echo [OK] Frontend dependencies installed

echo Building frontend...
call npm run build
if errorlevel 1 (
    echo [FAIL] Failed to build frontend
    cd ..
    pause
    exit /b 1
)
echo [OK] Frontend built
cd ..

echo.

REM Create .env if not exists
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo [NOTE] Please edit .env and add your API keys
) else (
    echo .env already exists
)

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit .env with your API keys
echo   2. Run: quorum.bat
echo.

pause
endlocal
