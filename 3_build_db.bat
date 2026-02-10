@echo off
chcp 65001 >nul
echo ============================================================
echo HMRV RAG System - Build Knowledge Base
echo ============================================================
echo.
echo [!] WARNING:
echo   - This will take 20-40 minutes (depends on CPU speed)
echo   - Will scan 722 Java files and other documents
echo   - Please make sure Ollama is running
echo.
set /p confirm="Ready to build knowledge base? (Y/N): "

if /i not "%confirm%"=="Y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo [1/3] Activating Python virtual environment...
call venv\Scripts\activate.bat

echo.
echo [2/3] Starting knowledge base creation...
echo ============================================================
echo.

python build_knowledge_base.py

if %errorlevel% neq 0 (
    echo.
    echo [X] Build FAILED!
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [OK] Knowledge base created successfully!
echo ============================================================
echo.
echo Next steps:
echo   - Run 4_query.bat for command-line interface
echo   - Run 5_web_ui.bat for web interface (recommended)
echo.
pause
