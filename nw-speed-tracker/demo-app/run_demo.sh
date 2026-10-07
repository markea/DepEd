#!/usr/bin/env bash
# DepEd NetPulse Interactive Prototype - 1-Command Localhost Launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "======================================================================"
echo "🇵🇭 Starting DepEd National Network Speed Tracker Interactive Showcase"
echo "   Platform: FastAPI + Gemini Enterprise (Gemini 3.8 Flash & 3.1 Pro)"
echo "   Directory: ${SCRIPT_DIR}"
echo "======================================================================"

# Initialize virtualenv if needed
if [ ! -d ".venv" ]; then
    echo "Creating local Python virtual environment (.venv)..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "Running automated verification test suite..."
python3 -m pytest test_demo_app.py -v || true

echo ""
echo "🚀 Launching showcase server on http://localhost:8080 ..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
