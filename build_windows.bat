@echo off
REM ============================================================
REM  Build script for Stock AI Screener — Windows
REM  Run this on your Windows machine inside the project folder
REM ============================================================

echo.
echo ============================================================
echo  Stock AI Screener - Windows Build
echo ============================================================
echo.

REM Step 1: Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Step 2: Create venv if it doesn't exist
IF NOT EXIST "venv_win" (
    echo [1/5] Creating virtual environment...
    python -m venv venv_win
) ELSE (
    echo [1/5] Virtual environment already exists, skipping...
)

REM Step 3: Activate venv and install dependencies
echo [2/5] Installing dependencies...
call venv_win\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

REM Step 4: Create data directories if they don't exist
echo [3/5] Preparing data directories...
IF NOT EXIST "data\cache" mkdir data\cache
IF NOT EXIST "data\models" mkdir data\models
IF NOT EXIST "logs" mkdir logs

REM Step 5: Run PyInstaller
echo [4/5] Building executable with PyInstaller...
pyinstaller StockAIScreener.spec --clean --noconfirm

REM Step 6: Copy .env.example into dist folder
echo [5/5] Copying config files...
copy ".env.example" "dist\StockAIScreener\.env.example" >nul 2>&1
copy ".env" "dist\StockAIScreener\.env" >nul 2>&1
IF NOT EXIST "dist\StockAIScreener\data\cache" mkdir dist\StockAIScreener\data\cache
IF NOT EXIST "dist\StockAIScreener\data\models" mkdir dist\StockAIScreener\data\models
IF NOT EXIST "dist\StockAIScreener\logs" mkdir dist\StockAIScreener\logs

echo.
echo ============================================================
echo  BUILD COMPLETE!
echo  Executable location: dist\StockAIScreener\StockAIScreener.exe
echo ============================================================
echo.
pause
