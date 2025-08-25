@echo off
REM FMCSA System Startup Script for Windows
REM This script sets up and runs the FMCSA Database Management System

echo =========================================
echo FMCSA Database Management System
echo =========================================
echo.

REM Check if running for the first time
set FIRST_RUN=false
if not exist ".env" (
    set FIRST_RUN=true
    echo First time setup detected...
)

REM Step 1: Environment Setup
if %FIRST_RUN%==true (
    echo.
    echo Step 1: Creating .env file...
    (
        echo # Database
        echo DATABASE_URL=postgresql://localhost:5432/fmcsa_db
        echo DB_MIN_CONNECTIONS=5
        echo DB_MAX_CONNECTIONS=20
        echo.
        echo # FMCSA API
        echo FMCSA_API_URL=https://mobile.fmcsa.dot.gov/qc/services/carriers
        echo.
        echo # API Configuration
        echo API_HOST=0.0.0.0
        echo API_PORT=8000
        echo API_WORKERS=4
        echo ENABLE_CORS=true
        echo CORS_ORIGINS=["http://localhost:3000"]
        echo.
        echo # Scheduler
        echo ENABLE_SCHEDULER=false
        echo REFRESH_SCHEDULE_HOUR=2
        echo REFRESH_SCHEDULE_MINUTE=0
        echo.
        echo # Export Settings
        echo EXPORT_MAX_ROWS_CSV=1000000
        echo EXPORT_MAX_ROWS_EXCEL=1048576
        echo EXPORT_CHUNK_SIZE=50000
        echo EXPORT_TEMP_DIR=C:\temp\fmcsa_exports
        echo.
        echo # Features
        echo ENABLE_RATE_LIMITING=true
        echo RATE_LIMIT_REQUESTS=100
        echo RATE_LIMIT_PERIOD=60
        echo ENABLE_API_KEY_AUTH=false
    ) > .env
    echo √ .env file created
)

REM Step 2: Python Environment
echo.
echo Step 2: Setting up Python environment...

if not exist "venv_windows" (
    echo Creating virtual environment...
    python -m venv venv_windows
)

echo Activating virtual environment...
call venv_windows\Scripts\activate.bat

echo Installing Python dependencies...
pip install -q -r fmcsa_system\requirements.txt
echo √ Python dependencies installed

REM Step 3: Frontend Setup
echo.
echo Step 3: Setting up React dashboard...

cd fmcsa_dashboard

if not exist "node_modules" (
    echo Installing Node.js dependencies...
    call npm install
    echo √ Node dependencies installed
) else (
    echo √ Node dependencies already installed
)

if not exist ".env" (
    echo Creating frontend .env file...
    echo VITE_API_URL=http://localhost:8000/api > .env
    echo √ Frontend .env created
)

cd ..

REM Step 4: Create temp directory for exports
if not exist "C:\temp\fmcsa_exports" (
    mkdir C:\temp\fmcsa_exports
)

REM Step 5: Start Services
echo.
echo =========================================
echo Starting FMCSA System Services
echo =========================================
echo.

REM Start API server in new window
echo Starting API server on http://localhost:8000...
start "FMCSA API Server" cmd /k "venv_windows\Scripts\activate && uvicorn fmcsa_system.api.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for API to start
timeout /t 5 /nobreak > nul

REM Start frontend in new window
echo Starting React dashboard on http://localhost:3000...
start "FMCSA Dashboard" cmd /k "cd fmcsa_dashboard && npm run dev"

echo.
echo =========================================
echo √ FMCSA System is running!
echo =========================================
echo.
echo Services:
echo   • API Server: http://localhost:8000
echo   • API Docs: http://localhost:8000/docs
echo   • Dashboard: http://localhost:3000
echo.

if %FIRST_RUN%==true (
    echo IMPORTANT: This is your first run!
    echo.
    echo To load initial data ^(2.2M records, ~1-2 hours^):
    echo   python -m fmcsa_system.ingestion.initial_load
    echo.
    echo For a quick test with limited data ^(1000 records^):
    echo   python -m fmcsa_system.ingestion.initial_load --limit 1000
    echo.
)

echo Press any key to open the dashboard in your browser...
pause > nul
start http://localhost:3000

echo.
echo To stop services, close the API Server and Dashboard windows.
echo.
pause