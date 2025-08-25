# PowerShell script to check and manage ports

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Checking Port Usage" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check port 8000
Write-Host "Checking port 8000 (API Server)..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "Port 8000 is in use by process:" -ForegroundColor Red
    $processId = $port8000[0].OwningProcess
    $process = Get-Process -Id $processId
    Write-Host "  Process: $($process.ProcessName) (PID: $processId)" -ForegroundColor White
    
    $response = Read-Host "Do you want to kill this process? (y/n)"
    if ($response -eq 'y') {
        Stop-Process -Id $processId -Force
        Write-Host "Process killed!" -ForegroundColor Green
    }
} else {
    Write-Host "Port 8000 is free!" -ForegroundColor Green
}

Write-Host ""

# Check port 3002
Write-Host "Checking port 3002 (Frontend)..." -ForegroundColor Yellow
$port3002 = Get-NetTCPConnection -LocalPort 3002 -ErrorAction SilentlyContinue
if ($port3002) {
    Write-Host "Port 3002 is in use by process:" -ForegroundColor Yellow
    $processId = $port3002[0].OwningProcess
    $process = Get-Process -Id $processId
    Write-Host "  Process: $($process.ProcessName) (PID: $processId)" -ForegroundColor White
} else {
    Write-Host "Port 3002 is free!" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Port check complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")