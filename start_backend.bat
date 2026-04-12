@echo off
echo ========================================
echo  Golden Carriere - Backend FastAPI
echo  http://127.0.0.1:8000
echo  Documentation: http://127.0.0.1:8000/docs
echo ========================================
set PYTHONPATH=%~dp0Backend
cd /d "%~dp0Backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
