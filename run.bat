@echo off
REM Запуск игры в виртуальном окружении

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    python main.py
) else (
    echo [ERROR] Virtual environment not found at .venv
    echo Please create it with: python -m venv .venv
    pause
)
