@echo off
title Grocery Automation System
echo 🚀 Starting Grocery Automation System...
echo =========================================

echo.
echo Starting all services...
echo.

REM Kill any existing processes on our ports
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start Appium Server
echo Starting Appium Server...
start "Appium Server" cmd /k "appium --port 4723"
timeout /t 3 /nobreak >nul

REM Start Backend
echo Starting Backend API...
cd backend
start "Backend API" cmd /k "python server.py"
timeout /t 3 /nobreak >nul

REM Start Frontend
echo Starting Frontend...
cd ..\frontend
start "Frontend" cmd /k "npm start"
timeout /t 3 /nobreak >nul

echo.
echo 🎯 System Starting Up...
echo.
echo Services will open in separate windows:
echo - Appium Server (Mobile automation)
echo - Backend API (http://localhost:8001)
echo - Frontend UI (http://localhost:3000)
echo.
echo 📱 Connect your Android phone and ensure USB debugging is enabled
echo.
echo ⏳ Wait for all services to fully load, then open:
echo http://localhost:3000
echo.

REM Test device connection after a delay
echo Testing device connection in 10 seconds...
timeout /t 10 /nobreak >nul

echo.
echo 📱 Android Device Status:
adb devices
echo.

if exist backend\test_device_connection.py (
    echo Running device connection test...
    cd backend
    python test_device_connection.py
    cd ..
)

echo.
echo 🎉 System is ready! Open http://localhost:3000
echo.
pause