@echo off
chcp 65001 >nul
echo ============================================================
echo HMRV RAG System - Ollama Model Setup
echo ============================================================
echo.

REM Check if Ollama is installed
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Ollama not found!
    echo.
    echo Please install Ollama first:
    echo   1. Go to https://ollama.com
    echo   2. Download and install Windows version
    echo   3. Run this batch file again
    echo.
    pause
    exit /b 1
)

echo [OK] Ollama is installed
ollama --version
echo.

echo Preparing to download Embedding model (about 1.2 GB, CPU-friendly)
echo.
echo Choose model:
echo   1. qwen3-embedding:0.6b (Recommended: Best for Chinese + Code)
echo   2. nomic-embed-text (Lightweight: Faster)
echo   3. Download both
echo.
set /p choice="Enter 1, 2 or 3: "

if "%choice%"=="1" (
    echo.
    echo Downloading qwen3-embedding:0.6b...
    ollama pull qwen3-embedding:0.6b
    echo [OK] qwen3-embedding:0.6b downloaded
) else if "%choice%"=="2" (
    echo.
    echo Downloading nomic-embed-text...
    ollama pull nomic-embed-text
    echo [OK] nomic-embed-text downloaded
) else if "%choice%"=="3" (
    echo.
    echo Downloading qwen3-embedding:0.6b...
    ollama pull qwen3-embedding:0.6b
    echo.
    echo Downloading nomic-embed-text...
    ollama pull nomic-embed-text
    echo [OK] Both models downloaded
) else (
    echo [X] Invalid choice
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [OK] Ollama model setup complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Edit config.yaml and set your LAN LLM API address
echo   2. Run 3_build_db.bat to build knowledge base
echo.
pause
