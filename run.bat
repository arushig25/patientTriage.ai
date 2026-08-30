@echo off
echo ======================================================================
echo Starting PatientTriage.ai - Hospital Emergency Command Center
echo Web Interface: http://localhost:8000
echo ======================================================================
start http://localhost:8000
python server.py
pause
