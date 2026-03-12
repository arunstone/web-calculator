@echo off
setlocal

cd /d "%~dp0"

if exist ".ngrok.pid" (
    set /p NGROK_PID=<.ngrok.pid
    if not "%NGROK_PID%"=="" (
        echo Stopping ngrok...
        taskkill /PID %NGROK_PID% /F >nul 2>&1
    )
    del /f /q ".ngrok.pid" >nul 2>&1
)

echo Stopping containers...
docker compose down

echo Stopping Docker Desktop...
taskkill /IM "Docker Desktop.exe" /F >nul 2>&1
taskkill /IM "com.docker.backend.exe" /F >nul 2>&1
taskkill /IM "com.docker.proxy.exe" /F >nul 2>&1
taskkill /IM "vpnkit.exe" /F >nul 2>&1

echo Stack is down.
endlocal
