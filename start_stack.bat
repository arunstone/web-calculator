@echo off
setlocal

cd /d "%~dp0"

if exist ".ngrok.pid" del /f /q ".ngrok.pid" >nul 2>&1

echo Starting Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

echo Waiting for Docker engine...
:wait_for_docker
docker info >nul 2>&1
if errorlevel 1 (
    timeout /t 5 /nobreak >nul
    goto wait_for_docker
)

echo Building frontend...
call npm --prefix frontend install
if errorlevel 1 exit /b 1

call npm --prefix frontend run build
if errorlevel 1 exit /b 1

echo Starting containers...
docker compose up -d --build
if errorlevel 1 exit /b 1

echo Starting ngrok tunnel...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process -FilePath 'uv' -ArgumentList 'run','python','start_ngrok.py' -WorkingDirectory '%cd%' -PassThru; Set-Content -Path '.ngrok.pid' -Value $p.Id"
if errorlevel 1 exit /b 1

echo Stack is up.
echo Open http://localhost
endlocal
