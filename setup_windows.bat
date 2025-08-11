@echo off
echo 🛒 Grocery Automation System - Windows Setup Helper
echo ===============================================

echo.
echo 🔧 Phase 1: Checking Prerequisites...
echo.

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Python is installed
    python --version
) else (
    echo ❌ Python not found - Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Node.js is installed
    node --version
) else (
    echo ❌ Node.js not found - Please install from https://nodejs.org
    pause
    exit /b 1
)

REM Check Java
java -version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Java is installed
    java -version
) else (
    echo ❌ Java not found - Please install JDK 11+ from https://adoptium.net
    pause
    exit /b 1
)

REM Check ADB
adb version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ ADB is available
    adb version
) else (
    echo ⚠️  ADB not found - Please install Android SDK or Android Studio
)

echo.
echo 🔧 Phase 2: Installing Dependencies...
echo.

echo Installing Python packages...
cd backend
pip install -r requirements.txt
if %ERRORLEVEL% EQU 0 (
    echo ✅ Backend dependencies installed
) else (
    echo ❌ Backend installation failed
    pause
    exit /b 1
)

echo.
echo Installing Node.js packages...
cd ..\frontend
npm install
if %ERRORLEVEL% EQU 0 (
    echo ✅ Frontend dependencies installed
) else (
    echo ❌ Frontend installation failed
    pause
    exit /b 1
)

echo.
echo Installing Appium...
npm install -g appium
appium driver install uiautomator2

echo.
echo 🔧 Phase 3: Setting up environment...
echo.

REM Create backend .env file
cd ..\backend
if not exist .env (
    echo Creating backend .env file...
    echo MONGO_URL=mongodb://localhost:27017 > .env
    echo DB_NAME=grocery_automation >> .env
    echo CORS_ORIGINS=* >> .env
    echo ✅ Backend .env created
)

REM Create frontend .env file
cd ..\frontend
if not exist .env (
    echo Creating frontend .env file...
    echo REACT_APP_BACKEND_URL=http://localhost:8001 > .env
    echo ✅ Frontend .env created
)

echo.
echo 🎉 SETUP COMPLETE!
echo.
echo 📋 Next Steps:
echo 1. Make sure MongoDB is running
echo 2. Connect your Android phone via USB
echo 3. Run start_system.bat to launch everything
echo.
pause