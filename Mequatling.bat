@echo off
set PROJECT=C:\Users\User\mequatling
set HOST=127.0.0.1
set PORT=8001

pushd "%PROJECT%"
start "Mequatling Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.main:app --host %HOST% --port %PORT%"
timeout /t 2 /nobreak >nul
start "" "http://%HOST%:%PORT%"
popd