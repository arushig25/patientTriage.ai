@echo off
echo ======================================================================
echo Starting PatientTriage.ai - Hospital Emergency Command Center
echo   ^> Local URL:   http://localhost:8000
echo   ^> Network URL: (check console below or run 'ipconfig')
echo ======================================================================
start http://localhost:8000
python server.py
pause
