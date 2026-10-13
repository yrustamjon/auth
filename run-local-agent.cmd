@echo off
setlocal
set "ADBIOGUARD_ENV=development"
set "ADBIOGUARD_API_BASE=http://127.0.0.1:8000"
cd /d "%~dp0..\agent"
if errorlevel 1 exit /b 1
if not exist "venv\Scripts\python.exe" (
    echo Agent Python environment not found: venv\Scripts\python.exe
    pause
    exit /b 1
)
echo Starting BioGuard Agent with backend %ADBIOGUARD_API_BASE%
"venv\Scripts\python.exe" main.py
if errorlevel 1 pause
endlocal
