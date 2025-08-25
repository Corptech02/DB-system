@echo off
echo Starting FMCSA Demo System...
echo.

REM Start API server in new window
start "FMCSA API" cmd /k "cd /d D:\context-engineering-intro && venv_windows\Scripts\activate && python -m uvicorn fmcsa_system.api.main_simple:app --reload --host 0.0.0.0 --port 8000"

REM Wait a bit for API to start
timeout /t 5 /nobreak > nul

REM Start frontend in new window
start "FMCSA Frontend" cmd /k "cd /d D:\context-engineering-intro\fmcsa_dashboard && npm run dev"

echo.
echo =========================================
echo FMCSA Demo System Starting...
echo =========================================
echo.
echo API Server: http://localhost:8000
echo API Docs:   http://localhost:8000/docs
echo Dashboard:  http://localhost:3000
echo.
echo Opening dashboard in browser...
timeout /t 5 /nobreak > nul
start http://localhost:3000
echo.
echo Both services are running in separate windows.
echo Close those windows to stop the services.
pause