Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Starting PatientTriage.ai - Hospital Emergency Command Center" -ForegroundColor Cyan
Write-Host "Web Interface: http://localhost:8000" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Start-Process "http://localhost:8000"
python server.py
