@echo off
echo ============================================
echo  Port Manager - Starting Application
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% == 0 (
    echo Running as Administrator - Full access enabled
) else (
    echo Warning: Not running as Administrator
    echo Some processes may not be killable
)
echo.

REM Install dependencies if needed
echo Checking dependencies...
pip show flask psutil flask-cors >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting server at http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

REM Check if port 5000 is in use and kill it
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    echo Killing existing process on port 5000 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

python app.py

pause
