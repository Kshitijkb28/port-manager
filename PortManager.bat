@echo off
:: Port Manager - Run as Administrator
:: This script will request admin privileges and start the Port Manager

:: Check for admin rights and request if needed
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else (
    goto gotAdmin
)

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

echo ============================================
echo  Port Manager - Running as Administrator
echo  Mode: WebSocket (Real-time Updates)
echo ============================================
echo.

:: Check if port 5000 is in use and kill it
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    echo Killing existing process on port 5000 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

:: Install dependencies if needed
echo Checking dependencies...
pip install flask flask-cors psutil flask-socketio eventlet -q

echo.
echo Starting Port Manager...
echo URL: http://localhost:5000
echo.

:: Start browser
start http://localhost:5000

:: Run Python app
python app.py

pause
