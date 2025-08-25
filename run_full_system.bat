@echo off
echo =========================================
echo FMCSA Full System Setup
echo =========================================
echo.

echo This script will:
echo 1. Download ALL 2.2M+ real FMCSA carriers
echo 2. Set up the database
echo 3. Start the API server
echo 4. Start the React dashboard
echo.

echo Step 1: Downloading all carriers (45-90 minutes)...
python fetch_all_carriers.py

if errorlevel 1 (
    echo Download failed or cancelled.
    pause
    exit /b 1
)

echo.
echo Step 2: Starting API server with full data...
start "FMCSA API - Full Data" cmd /k "python demo_real_api.py"

timeout /t 5 /nobreak > nul

echo Step 3: Starting React dashboard...
start "FMCSA Dashboard" cmd /k "cd fmcsa_dashboard && npm run dev"

echo.
echo =========================================
echo System is running!
echo =========================================
echo.
echo API Server: http://localhost:8000
echo Dashboard: http://localhost:3000
echo.
echo The system is now serving ALL 2.2M+ real FMCSA carriers!
echo.
pause