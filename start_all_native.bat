@echo off
title HopeStack - Master Native Launcher
color 0B

echo ==============================================
echo       Starting HopeStack Microservices      
echo ==============================================
echo.
echo NOTE: Since Docker is not installed on your machine,
echo this script opens separate terminals to launch each service natively.
echo.

echo [1/6] Starting Unified Emotion (Port 8080)...
start "Unified Emotion Service (8080)" cmd /k "cd LiveEmotion\UnifiedEmotion && pip install -r requirements.txt -q && python app.py"

echo [2/6] Starting Face Emotion (Port 8001)...
start "Face Emotion Service (8001)" cmd /k "cd faceEmotion && pip install -r requirements.txt -q && python app.py"

echo [3/6] Starting Voice Emotion (Port 8002)...
start "Voice Emotion Service (8002)" cmd /k "cd voiceEmotion && pip install -r requirements.txt -q && python -m uvicorn app:app --host 0.0.0.0 --port 8002"

echo [4/6] Starting Speech To Text (Port 8003)...
start "Speech To Text Service (8003)" cmd /k "cd speechToText && pip install -r requirements.txt -q && python -m uvicorn main:app --host 0.0.0.0 --port 8003"

echo [5/6] Starting User Login Server (Port 8004)...
start "User Login Portal (8004)" cmd /k "cd userLogin && python -m http.server 8004"

echo [6/6] Starting Central Gateway (Port 80)...
start "HopeStack Gateway (80)" cmd /k "cd gateway && python -m http.server 80"

echo.
echo ==============================================
echo  [SUCCESS] All sub-systems are initializing!  
echo  Access your Dashboard at: http://localhost  
echo ==============================================
echo.
pause
