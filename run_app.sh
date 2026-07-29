#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "============================================"
echo "  JD/CV Analysis Tool — Setup"
echo "============================================"

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
echo "[2/3] Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt -q

# Launch
echo "[3/3] Starting Streamlit App..."
streamlit run app.py --server.port 8501
