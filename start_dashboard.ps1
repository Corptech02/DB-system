# PowerShell script to start both servers

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting FMCSA Dashboard" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start the API server in a new window
Write-Host "Starting API server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\context-engineering-intro'; python demo_real_api.py"

# Wait a bit for the API to start
Write-Host "Waiting for API server to start (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Start the frontend in a new window
Write-Host "Starting frontend dashboard..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\context-engineering-intro\fmcsa_dashboard'; npm run dev"

# Wait a bit for the frontend to start
Start-Sleep -Seconds 5

# Open the browser
Write-Host ""
Write-Host "Opening dashboard in browser..." -ForegroundColor Green
Start-Process "http://localhost:3002"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Dashboard should now be running!" -ForegroundColor Green
Write-Host "API Server: http://localhost:8000" -ForegroundColor White
Write-Host "Dashboard: http://localhost:3002" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit this window (servers will keep running)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")