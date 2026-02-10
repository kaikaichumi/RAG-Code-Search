@echo off
chcp 65001 >nul
cls
echo ============================================================
echo        HMRV RAG System - Quick Start Guide
echo ============================================================
echo.
echo [FIXED] Windows encoding issues have been resolved!
echo [FIXED] Model name updated to qwen3-embedding:0.6b
echo.
echo ============================================================
echo.
echo You already pulled: qwen3-embedding:0.6b (Good!)
echo.
echo Your config.yaml already has:
echo   - LLM API: http://100.89.19.74:8000/v1
echo   - Embedding: qwen3-embedding:0.6b
echo.
echo ============================================================
echo                   NEXT STEP
echo ============================================================
echo.
echo Double-click: 3_build_db.bat
echo.
echo This will:
echo   - Scan 722 Java files and other documents
echo   - Create vector database (takes 20-40 minutes)
echo   - Save to ./chroma_db/ directory
echo.
echo After that:
echo   - Run 5_web_ui.bat for web interface (recommended)
echo   - Run 4_query.bat for command-line interface
echo.
echo ============================================================
echo.
pause
