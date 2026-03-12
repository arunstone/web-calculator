$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$logFile = Join-Path $PSScriptRoot "stack-status.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Add-Section {
    param(
        [string]$Title,
        [string]$Content
    )

    Add-Content -Path $logFile -Value "===== $Title ====="
    Add-Content -Path $logFile -Value $Content
    Add-Content -Path $logFile -Value ""
}

function Get-CommandOutput {
    param(
        [string]$Command
    )

    return (cmd /c $Command | Out-String)
}

Set-Content -Path $logFile -Value "Stack snapshot generated at $timestamp"
Add-Content -Path $logFile -Value ""

$composePs = Get-CommandOutput "docker compose ps"
Add-Section -Title "docker compose ps" -Content $composePs

$health = Invoke-WebRequest -UseBasicParsing http://localhost:8080/api/health 2>&1 | Select-Object -ExpandProperty Content
Add-Section -Title "nginx /api/health" -Content $health

$backendLogs = Get-CommandOutput "docker logs local-backend --tail 80 2>&1"
Add-Section -Title "backend logs" -Content $backendLogs

$workerLogs = Get-CommandOutput "docker logs local-worker --tail 80 2>&1"
Add-Section -Title "worker logs" -Content $workerLogs

$nginxLogs = Get-CommandOutput "docker logs local-nginx --tail 80 2>&1"
Add-Section -Title "nginx logs" -Content $nginxLogs

$redisLogs = Get-CommandOutput "docker logs local-redis --tail 40 2>&1"
Add-Section -Title "redis logs" -Content $redisLogs

$postgresLogs = Get-CommandOutput "docker logs local-postgres --tail 40 2>&1"
Add-Section -Title "postgres logs" -Content $postgresLogs
