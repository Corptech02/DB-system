# Quick script to kill process on port 8000

Write-Host "Checking for process on port 8000..." -ForegroundColor Yellow

$connection = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($connection) {
    $processId = $connection[0].OwningProcess
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    
    if ($process) {
        Write-Host "Found process: $($process.ProcessName) (PID: $processId)" -ForegroundColor Red
        Write-Host "Killing process..." -ForegroundColor Yellow
        Stop-Process -Id $processId -Force
        Write-Host "Process killed successfully!" -ForegroundColor Green
    }
} else {
    Write-Host "No process found on port 8000" -ForegroundColor Green
}

Write-Host ""
Write-Host "You can now start the API server with:" -ForegroundColor Cyan
Write-Host "  python demo_real_api.py" -ForegroundColor White