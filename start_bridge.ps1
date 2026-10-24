<#
.SYNOPSIS
    StudySloth AI - Local Bridge PowerShell Launcher
.DESCRIPTION
    Checks Python, verifies minimal bridge dependencies, checks Ollama status,
    and runs the secure local bridge with the browser companion app enabled.
#>

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Sloth Study Helper: Starting StudySloth AI Local Bridge       " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Detect Python
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py -3"
}

if (-not $pythonCmd) {
    Write-Host "[ERROR] Python 3 was not found in your PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org/downloads/ and ensure 'Add to PATH' is checked." -ForegroundColor Yellow
    exit 1
}

# 2. Check virtual environment
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[*] Setting up virtual environment (.venv)..." -ForegroundColor Gray
    try {
        & $pythonCmd -m venv .venv
    } catch {
        Write-Host "[WARNING] Could not create .venv; running with system Python." -ForegroundColor Yellow
        $venvPython = $pythonCmd
    }
}

# 3. Check / install dependencies
Write-Host "[*] Checking bridge dependencies..." -ForegroundColor Gray
$depCheck = & $venvPython -c "import requests, pypdf, docx; print('OK')" 2>$null
if ($depCheck -ne "OK") {
    Write-Host "[*] Installing minimal dependencies from requirements-bridge.txt..." -ForegroundColor Yellow
    & $venvPython -m pip install -r requirements-bridge.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install dependencies." -ForegroundColor Red
        exit 1
    }
}

# 4. Check if Ollama is running
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 2 -ErrorAction Stop
    $models = $ollamaCheck.models | ForEach-Object { $_.name }
    Write-Host "[OK] Ollama is active on 127.0.0.1:11434" -ForegroundColor Green
    if ($models) {
        Write-Host "[*] Installed Ollama models: $($models -join ', ')" -ForegroundColor Gray
    }
} catch {
    Write-Host "[NOTE] Ollama does not appear to be running on 127.0.0.1:11434." -ForegroundColor Yellow
    Write-Host "       Make sure Ollama is started on your computer (run 'ollama serve' or open the Ollama desktop app)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[*] Starting StudySloth Local Bridge with Companion App..." -ForegroundColor Cyan
Write-Host "[*] Keep this window OPEN while using StudySloth AI." -ForegroundColor Gray
Write-Host ""

& $venvPython bridge/bridge.py --open @args
