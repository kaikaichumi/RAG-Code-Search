@echo off
chcp 65001 >nul
title HMRV RAG Query System

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting query interface...
python query.py

pause
