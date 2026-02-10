@echo off
chcp 65001 >nul
title HMRV RAG Web UI

echo ============================================================
echo Starting HMRV RAG Web UI...
echo ============================================================
echo.
echo Browser will open automatically
echo Default URL: http://localhost:7860
echo.
echo Press Ctrl+C to stop server
echo ============================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Web UI
python web_ui.py

pause
