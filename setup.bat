@echo off
chcp 65001 >nul
echo ======================================================================
echo RAG 系統 - 環境安裝
echo ======================================================================
echo.

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 Python
    echo 請先安裝 Python 3.8 或以上版本
    echo 下載位址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 建立虛擬環境...
python -m venv venv
if errorlevel 1 (
    echo [錯誤] 建立虛擬環境失敗
    pause
    exit /b 1
)

echo.
echo [2/3] 啟動虛擬環境...
call venv\Scripts\activate.bat

echo.
echo [3/3] 安裝 Python 套件...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [錯誤] 安裝套件失敗
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo ✅ 環境安裝完成！
echo ======================================================================
echo.
echo 下一步：
echo   1. 安裝 Ollama: https://ollama.com
echo   2. 下載模型: ollama pull qwen3-embedding:0.6b
echo   3. 下載模型: ollama pull qwen2.5:14b
echo   4. 編輯 config.yaml 設定專案路徑
echo   5. 執行 build.bat 建立知識庫
echo.
pause
