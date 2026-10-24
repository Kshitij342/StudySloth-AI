#!/usr/bin/env bash
# StudySloth AI - Local Bridge Launcher for macOS and Linux

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo "  Sloth Study Helper: Starting StudySloth AI Local Bridge       "
echo "================================================================"
echo ""

# 1. Detect Python 3
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python 3 was not found in your PATH."
    echo "Please install Python 3.10+ from https://www.python.org/ or via your package manager."
    exit 1
fi

# 2. Check virtual environment
if [ -f ".venv/bin/python" ]; then
    VENV_PYTHON=".venv/bin/python"
else
    echo "[*] Setting up virtual environment (.venv)..."
    if $PYTHON_CMD -m venv .venv 2>/dev/null; then
        VENV_PYTHON=".venv/bin/python"
    else
        echo "[WARNING] Could not create .venv; running with system Python."
        VENV_PYTHON="$PYTHON_CMD"
    fi
fi

# 3. Check / install dependencies
echo "[*] Checking bridge dependencies..."
if ! "$VENV_PYTHON" -c "import requests, pypdf, docx" &>/dev/null; then
    echo "[*] Installing minimal dependencies from requirements-bridge.txt..."
    "$VENV_PYTHON" -m pip install -r requirements-bridge.txt
fi

# 4. Check if Ollama is running
if curl -s -m 2 http://127.0.0.1:11434/api/tags &>/dev/null; then
    echo "[OK] Ollama is active on 127.0.0.1:11434"
else
    echo "[NOTE] Ollama does not appear to be running on 127.0.0.1:11434."
    echo "       Make sure Ollama is started on your computer (run 'ollama serve')."
fi

echo ""
echo "[*] Starting StudySloth Local Bridge with Companion App..."
echo "[*] Keep this terminal OPEN while using StudySloth AI."
echo ""

exec "$VENV_PYTHON" bridge/bridge.py --open "$@"
