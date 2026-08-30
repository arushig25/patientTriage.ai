$localIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*", "Ethernet*" -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1).IPAddress
if (-not $localIP) { $localIP = "localhost" }

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Starting PatientTriage.ai - Hospital Emergency Command Center" -ForegroundColor Cyan
Write-Host "  > Local URL:   http://localhost:8000" -ForegroundColor Green
Write-Host "  > Network URL: http://$($localIP):8000" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Start-Process "http://localhost:8000"
python server.py
