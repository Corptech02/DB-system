@echo off
REM Quick Demo Script - No Database Required
REM This runs a simplified version for testing

echo =========================================
echo FMCSA System - Demo Mode (No Database)
echo =========================================
echo.

REM Install minimal dependencies
echo Installing minimal dependencies...
pip install fastapi uvicorn python-dotenv pydantic

REM Start simplified API
echo.
echo Starting demo API server...
python -m uvicorn fmcsa_system.api.main_simple:app --reload --host 0.0.0.0 --port 8000