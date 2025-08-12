@echo off
pushd %~dp0
start "Mequatling Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.main:app --port 8000"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8000"
popd