@echo off
chcp 65001 >nul
echo ============================================================
echo HMRV RAG System - Environment Installation
echo ============================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python not found!
    echo.
    echo Please install Python 3.8 or above first
    echo Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed
python --version
echo.

REM Create virtual environment
if not exist "venv" (
    echo [1/3] Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [X] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [2/3] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install packages
echo [3/3] Installing Python packages (this may take a few minutes)...

REM Set UTF-8 encoding to avoid Chinese comment errors
set PYTHONUTF8=1

python -m pip install --upgrade pip

REM Core packages (use latest stable version)
python -m pip install langchain
python -m pip install langchain-core
python -m pip install langchain-community
python -m pip install langchain-chroma
python -m pip install langchain-text-splitters
python -m pip install langchain-ollama
python -m pip install langchain-openai

REM Vector database (use latest version)
python -m pip install chromadb

REM Document processing
python -m pip install chardet
python -m pip install tiktoken

REM Config file parser
python -m pip install PyYAML

REM Web UI
python -m pip install gradio

REM Utility packages
python -m pip install tqdm
python -m pip install requests
python -m pip install colorama

if %errorlevel% neq 0 (
    echo [X] Package installation failed
    pause
    exit /b 1
)
echo.

echo ============================================================
echo [OK] Installation complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Make sure Ollama is installed (https://ollama.com)
echo   2. Run 2_setup_ollama.bat to download Embedding model
echo   3. Edit config.yaml to set your LAN LLM API address
echo   4. Run 3_build_db.bat to build knowledge base
echo.
pause
