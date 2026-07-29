@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   JD/CV Analysis Tool — Setup
echo ============================================

:: Create venv if missing
if not exist "venv\" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
)

:: Activate
echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

:: Launch
echo [3/3] Starting Streamlit App...
streamlit run app.py --server.port 8501

pause
