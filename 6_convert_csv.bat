@echo off
chcp 65001 >nul
echo ============================================================
echo Convert CSV Database Schema to Markdown
echo ============================================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Converting CSV to Markdown format...
python convert_csv_to_md.py

if %errorlevel% neq 0 (
    echo.
    echo [X] Conversion failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [OK] Conversion complete!
echo ============================================================
echo.
echo Next step: Run 3_build_db.bat to rebuild knowledge base
echo.
pause
