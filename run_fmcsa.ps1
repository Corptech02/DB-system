# FMCSA System Startup Script for Windows PowerShell
# This script sets up and runs the FMCSA Database Management System

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "FMCSA Database Management System" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running for the first time
$firstRun = $false
if (-not (Test-Path ".env")) {
    $firstRun = $true
    Write-Host "First time setup detected..." -ForegroundColor Yellow
}

# Step 1: Environment Setup
if ($firstRun) {
    Write-Host ""
    Write-Host "Step 1: Creating .env file..." -ForegroundColor Green
    
    $envContent = @"
# Database
DATABASE_URL=postgresql://localhost:5432/fmcsa_db
DB_MIN_CONNECTIONS=5
DB_MAX_CONNECTIONS=20

# FMCSA API
FMCSA_API_URL=https://mobile.fmcsa.dot.gov/qc/services/carriers

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
ENABLE_CORS=true
CORS_ORIGINS=["http://localhost:3000"]

# Scheduler
ENABLE_SCHEDULER=false
REFRESH_SCHEDULE_HOUR=2
REFRESH_SCHEDULE_MINUTE=0

# Export Settings
EXPORT_MAX_ROWS_CSV=1000000
EXPORT_MAX_ROWS_EXCEL=1048576
EXPORT_CHUNK_SIZE=50000
EXPORT_TEMP_DIR=C:\temp\fmcsa_exports

# Features
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
ENABLE_API_KEY_AUTH=false
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✓ .env file created" -ForegroundColor Green
}

# Step 2: Python Environment
Write-Host ""
Write-Host "Step 2: Setting up Python environment..." -ForegroundColor Green

if (-not (Test-Path "venv_windows")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv_windows
}

Write-Host "Activating virtual environment..."
& ".\venv_windows\Scripts\Activate.ps1"

Write-Host "Installing Python dependencies..."
pip install -q -r fmcsa_system\requirements.txt
Write-Host "✓ Python dependencies installed" -ForegroundColor Green

# Step 3: Frontend Setup
Write-Host ""
Write-Host "Step 3: Setting up React dashboard..." -ForegroundColor Green

Set-Location fmcsa_dashboard

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Node.js dependencies..."
    npm install
    Write-Host "✓ Node dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✓ Node dependencies already installed" -ForegroundColor Green
}

if (-not (Test-Path ".env")) {
    Write-Host "Creating frontend .env file..."
    "VITE_API_URL=http://localhost:8000/api" | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✓ Frontend .env created" -ForegroundColor Green
}

Set-Location ..

# Step 4: Create temp directory for exports
if (-not (Test-Path "C:\temp\fmcsa_exports")) {
    New-Item -ItemType Directory -Path "C:\temp\fmcsa_exports" -Force | Out-Null
}

# Step 5: Start Services
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Starting FMCSA System Services" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Start API server in new PowerShell window
Write-Host "Starting API server on http://localhost:8000..." -ForegroundColor Yellow
$apiScript = @"
Write-Host 'FMCSA API Server' -ForegroundColor Cyan
Set-Location '$PWD'
& '.\venv_windows\Scripts\Activate.ps1'
uvicorn fmcsa_system.api.main:app --host 0.0.0.0 --port 8000 --reload
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiScript

# Wait for API to start
Start-Sleep -Seconds 5

# Start frontend in new PowerShell window
Write-Host "Starting React dashboard on http://localhost:3000..." -ForegroundColor Yellow
$frontendScript = @"
Write-Host 'FMCSA Dashboard' -ForegroundColor Cyan
Set-Location '$PWD\fmcsa_dashboard'
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "✓ FMCSA System is running!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  • API Server: http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host ""

if ($firstRun) {
    Write-Host "IMPORTANT: This is your first run!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To load initial data (2.2M records, ~1-2 hours):" -ForegroundColor White
    Write-Host "  python -m fmcsa_system.ingestion.initial_load" -ForegroundColor Gray
    Write-Host ""
    Write-Host "For a quick test with limited data (1000 records):" -ForegroundColor White
    Write-Host "  python -m fmcsa_system.ingestion.initial_load --limit 1000" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "Opening dashboard in browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "To stop services, close the API Server and Dashboard windows." -ForegroundColor Yellow
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")