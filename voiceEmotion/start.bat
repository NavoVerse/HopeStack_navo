@echo off
title VoiceEmo — Voice Emotion Recognizer
color 0B

echo.
echo  ==========================================
echo   VoiceEmo ^| Voice Emotion Recognizer
echo  ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo  [1/3] Checking / installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies. Check your internet connection.
    pause
    exit /b 1
)

echo  [2/3] Dependencies ready.
echo.
echo  [3/3] Starting server...
echo.
echo  ----------------------------------------------------------
echo   Open your browser at:   http://localhost:8000
echo   (The AI model downloads ~1 GB on first run — be patient)
echo  ----------------------------------------------------------
echo.

python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

pause
