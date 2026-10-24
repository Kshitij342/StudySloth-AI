@echo off
setlocal enabledelayedexpansion

title StudySloth AI - Local Bridge Launcher
cd /d "%~dp0"

echo ================================================================
echo   Sloth Study Helper: Starting StudySloth AI Local Bridge
echo ================================================================
echo.

:: Detect Python
set "PYTHON_CMD="
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python"
) else (
    py -3 --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=py -3"
    )
)

if "!PYTHON_CMD!"=="" (
    echo [ERROR] Python was not found in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Check or set up virtual environment
if exist ".venv\Scripts\python.exe" (
    set "VENV_PYTHON=.venv\Scripts\python.exe"
) else (
    echo [*] Setting up lightweight virtual environment (.venv)...
    !PYTHON_CMD! -m venv .venv
    if !errorlevel! neq 0 (
        echo [WARNING] Could not create .venv; running with system Python.
        set "VENV_PYTHON=!PYTHON_CMD!"
    ) else (
        set "VENV_PYTHON=.venv\Scripts\python.exe"
    )
)

:: Install minimal bridge dependencies if needed
echo [*] Checking bridge dependencies...
"%VENV_PYTHON%" -c "import requests, pypdf, docx" >nul 2>&1
if !errorlevel! neq 0 (
    echo [*] Installing minimal bridge dependencies from requirements-bridge.txt...
    "%VENV_PYTHON%" -m pip install -r requirements-bridge.txt
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

:: Check if Ollama is running
curl.exe -s -m 2 http://127.0.0.1:11434/api/tags >nul 2>&1
if !errorlevel! neq 0 (
    echo [NOTE] Ollama does not appear to be running on 127.0.0.1:11434.
    echo        Make sure Ollama is started on your computer (run 'ollama serve' or open the Ollama app).
)

echo.
echo [*] Launching StudySloth Local Bridge with Companion App...
echo [*] Keep this window OPEN while studying.
echo.

"%VENV_PYTHON%" bridge/bridge.py --open %*

if !errorlevel! neq 0 (
    echo.
    echo Bridge stopped or encountered an error.
    pause
)
