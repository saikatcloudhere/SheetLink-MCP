@echo off
title SheetLink-MCP Visual Manager
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" chat_app.py
) else (
    python chat_app.py
)
if errorlevel 1 (
    echo An error occurred while opening the manager.
    pause
)
