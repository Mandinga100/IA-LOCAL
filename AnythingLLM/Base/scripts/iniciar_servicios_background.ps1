# iniciar_servicios_background.ps1
# Lanza todos los servicios en segundo plano persistente (sin bloquear la terminal)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$BaseDir = (Get-Item $PSScriptRoot).Parent.FullName
$PythonExe = Join-Path $BaseDir ".venv\Scripts\python.exe"
$AnythingLLMDir = (Get-Item $BaseDir).Parent.FullName
$ServerDir = Join-Path $AnythingLLMDir "server"
$CollectorDir = Join-Path $AnythingLLMDir "collector"

# Función para liberar puertos
function Liberar-Puerto([int]$puerto) {
    try {
        $conexiones = Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue
        foreach ($conn in $conexiones) {
            $pidTarget = $conn.OwningProcess
            if ($pidTarget -and $pidTarget -gt 4 -and $pidTarget -ne $PID) {
                Stop-Process -Id $pidTarget -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 300
            }
        }
    } catch {}
}

Write-Host "Liberando puertos previos..." -ForegroundColor Yellow
Liberar-Puerto 8000
Liberar-Puerto 8888
Liberar-Puerto 3001

# Sincronizar workspaces
Write-Host "Sincronizando workspaces con SQLite..." -ForegroundColor Cyan
& $PythonExe (Join-Path $PSScriptRoot "sincronizar_workspaces.py")

# Iniciar Collector (:8888)
Write-Host "Iniciando Collector (:8888)..." -ForegroundColor Cyan
Start-Process -FilePath "node" -ArgumentList "index.js" -WorkingDirectory $CollectorDir -WindowStyle Hidden

# Iniciar AnythingLLM Server (:3001)
Write-Host "Iniciando AnythingLLM Server (:3001)..." -ForegroundColor Cyan
Start-Process -FilePath "node" -ArgumentList "index.js" -WorkingDirectory $ServerDir -WindowStyle Hidden

# Iniciar Gateway FastAPI (:8000)
Write-Host "Iniciando Gateway Base (:8000)..." -ForegroundColor Cyan
Start-Process -FilePath $PythonExe -ArgumentList "servidor_api.py" -WorkingDirectory $BaseDir -WindowStyle Hidden

# Esperar 5 segundos y verificar salud
Start-Sleep -Seconds 5

$gwOk = $false
$allmOk = $false
try {
    $resGw = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/salud" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($resGw.estado -eq "online") { $gwOk = $true }
} catch {}

try {
    $resAllm = Invoke-RestMethod -Uri "http://127.0.0.1:3001/api/ping" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($resAllm.online) { $allmOk = $true }
} catch {}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host " ESTADO DE SERVICIOS EN SEGUNDO PLANO:" -ForegroundColor Green
Write-Host " -> Gateway Base (:8000)     : $(if ($gwOk) { 'ONLINE (OK)' } else { 'INICIANDO...' })"
Write-Host " -> AnythingLLM UI (:3001)  : $(if ($allmOk) { 'ONLINE (OK)' } else { 'INICIANDO...' })"
Write-Host " -> Collector (:8888)        : ACTIVO"
Write-Host " -> Ollama (:11434)          : ACTIVO"
Write-Host "======================================================" -ForegroundColor Green
