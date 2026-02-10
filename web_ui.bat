@echo off
chcp 65001 >nul
echo ======================================================================
echo RAG 系統 - Web UI 啟動中...
echo ======================================================================
echo.
call venv\Scripts\activate.bat
python rag_web_ui.py
pause
