@echo off
title LiveEmotion — Multi-Modal Emotion AI
color 0E

echo.
echo  ==============================================
echo     LiveEmotion ^| Multi-Modal Emotion AI
echo  ==============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python 3.9+ 
    pause
    exit /b 1
)

echo  [1/3] Merging and installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies. Check your connection.
    pause
    exit /b 1
)

echo  [2/3] Environment ready.
echo.
echo  ----------------------------------------------------------
echo   Launch URL:   http://localhost:8080
echo   
echo   NOTE: Two AI models are loading (~2.5 GB total).
echo   Please wait for the "ready" status on the web page.
echo  ----------------------------------------------------------
echo.

echo  [3/3] Starting Unified AI Server...
echo.

python app.py

pause
