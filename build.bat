@echo off
echo ============================================================
echo Building Stock AI Screener Windows Executable...
echo ============================================================

IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo Installing build requirements...
pip install -r requirements.txt

echo Running PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --name "StockAI_Screener" ^
    --add-data ".env.example;." ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "PySide6.QtWidgets" ^
    --hidden-import "pyqtgraph" ^
    --hidden-import "scikit-learn" ^
    --hidden-import "sklearn.ensemble._forest" ^
    app/main.py

echo ============================================================
echo Build Complete! Output executable folder located at: dist\StockAI_Screener
echo ============================================================
pause
