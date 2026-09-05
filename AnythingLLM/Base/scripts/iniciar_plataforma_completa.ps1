# iniciar_plataforma_completa.ps1
# Script maestro nativo PowerShell para Windows 10/11 64-bit
# Orquesta la plataforma completa: Ollama, Collector (:8888), AnythingLLM (:3001) y Gateway Base (:8000)

param (
    [ValidateSet("Local", "Dev", "Docker", "SoloBase")]
    [string]$Modo = "Local",
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  PLATAFORMA IA LOCAL & ANYTHINGLLM - ORQUESTADOR MAESTRO UNIFICADO" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Modo de ejecucion: $Modo" -ForegroundColor Yellow
Write-Host ""

$BaseDir = (Get-Item $PSScriptRoot).Parent.FullName
$PythonExe = Join-Path $BaseDir ".venv\Scripts\python.exe"
$AnythingLLMDir = (Get-Item $BaseDir).Parent.FullName
$ServerDir = Join-Path $AnythingLLMDir "server"
$CollectorDir = Join-Path $AnythingLLMDir "collector"
$FrontendDir = Join-Path $AnythingLLMDir "frontend"
$PublicDir = Join-Path $ServerDir "public"

# 1. Comprobacion de Entorno Virtual Python
if (-not (Test-Path $PythonExe)) {
    Write-Host "[ERROR] Entorno virtual no encontrado en: $PythonExe" -ForegroundColor Red
    Write-Host "Ejecuta primero: cd AnythingLLM/Base; uv venv .venv; .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# 2. Comprobacion de Node.js
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host "[ERROR] Node.js no encontrado en el PATH del sistema." -ForegroundColor Red
    exit 1
}

# 3. Optimizacion y Verificacion de Ollama
Write-Host "[1/5] Verificando servicio Ollama..." -ForegroundColor Yellow
$ollamaActivo = $false
try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($resp) { $ollamaActivo = $true }
} catch {
    $ollamaActivo = $false
}

if (-not $ollamaActivo) {
    Write-Host "  Ollama no esta en ejecucion. Intentando arrancar con optimizaciones..." -ForegroundColor Yellow
    $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($ollamaCmd) {
        $env:OLLAMA_NUM_PARALLEL = "4"
        $env:OLLAMA_MAX_LOADED_MODELS = "2"
        $env:OLLAMA_KEEP_ALIVE = "24h"
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        Write-Host "  [OK] Ollama iniciado en segundo plano." -ForegroundColor Green
    } else {
        Write-Host "  [AVISO] Comando 'ollama' no encontrado en el PATH." -ForegroundColor DarkYellow
    }
} else {
    Write-Host "  [OK] Ollama detectado y activo en http://127.0.0.1:11434" -ForegroundColor Green
}

# 4. Sincronizar Workspaces y Flujos Documentales
Write-Host ""
Write-Host "[2/5] Sincronizando workspaces y carpetas de documentos..." -ForegroundColor Yellow
$syncScript = Join-Path $PSScriptRoot "sincronizar_workspaces.py"
& $PythonExe $syncScript

# 5. Verificacion de Frontend Compilado (Modo Unificado)
Write-Host ""
Write-Host "[3/5] Verificando compilacion de frontend AnythingLLM..." -ForegroundColor Yellow
$indexHtml = Join-Path $PublicDir "_index.html"
if (-not (Test-Path $indexHtml)) {
    Write-Host "  Frontend no compilado en server/public. Compilando ahora..." -ForegroundColor Cyan
    Push-Location $FrontendDir
    try {
        npm run build
        if (-not (Test-Path $PublicDir)) { New-Item -ItemType Directory -Path $PublicDir -Force | Out-Null }
        Copy-Item -Recurse -Force (Join-Path $FrontendDir "dist\*") $PublicDir
        Write-Host "  [OK] Frontend compilado y desplegado en server/public." -ForegroundColor Green
    } catch {
        Write-Host "  [AVISO] No se pudo compilar el frontend automaticamente: $($_.Exception.Message)" -ForegroundColor DarkYellow
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  [OK] Frontend listo en server/public." -ForegroundColor Green
}

# 6. Preparacion y Liberacion de Puertos
function Liberar-Puerto([int]$puerto) {
    try {
        $conexiones = Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue
        if ($conexiones) {
            foreach ($conn in $conexiones) {
                $pidTarget = $conn.OwningProcess
                if ($pidTarget -and $pidTarget -gt 4 -and $pidTarget -ne $PID) {
                    Write-Host "  [Auto-Recovery] Liberando puerto $puerto ocupado previamente (PID: $pidTarget)..." -ForegroundColor Yellow
                    Stop-Process -Id $pidTarget -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 300
                }
            }
        }
    } catch {
        $netstatOut = netstat -ano | findstr ":$puerto " | findstr "LISTENING"
        foreach ($line in $netstatOut) {
            $parts = $line.Trim() -split "\s+"
            $pidVal = $parts[-1]
            if ($pidVal -match "^\d+$" -and [int]$pidVal -gt 4 -and [int]$pidVal -ne $PID) {
                Write-Host "  [Auto-Recovery] Liberando puerto $puerto ocupado previamente (PID: $pidVal)..." -ForegroundColor Yellow
                Stop-Process -Id [int]$pidVal -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 300
            }
        }
    }
}

Liberar-Puerto 8000
if ($Modo -ne "SoloBase") {
    Liberar-Puerto 8888
    Liberar-Puerto 3001
}

# 7. Lanzamiento de Servicios segun Modo
$CollectorProcess = $null
$AnythingProcess = $null
$ViteProcess = $null

try {
    Write-Host ""
    Write-Host "[4/5] Inicializando servidores de la plataforma..." -ForegroundColor Yellow

    if ($Modo -eq "Docker") {
        Write-Host "  Modo Docker seleccionado. Desplegando AnythingLLM en contenedor..." -ForegroundColor Cyan
        $dockerScript = Join-Path $PSScriptRoot "desplegar_anythingllm_docker.ps1"
        & $dockerScript
    } elseif ($Modo -ne "SoloBase") {
        # 6.1 Iniciar Collector (Procesador de Documentos en puerto 8888)
        Write-Host "  Iniciando Collector (API de Procesamiento de Documentos en puerto 8888)..." -ForegroundColor Cyan
        $CollectorProcess = Start-Process -FilePath "node" -ArgumentList "index.js" -WorkingDirectory $CollectorDir -WindowStyle Hidden -PassThru

        $esperaCollector = 15
        $collectorListo = $false
        for ($i = 0; $i -lt $esperaCollector; $i++) {
            Start-Sleep -Seconds 1
            try {
                $accepts = Invoke-RestMethod -Uri "http://127.0.0.1:8888/accepts" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($accepts) {
                    $collectorListo = $true
                    break
                }
            } catch {}
        }

        if ($collectorListo) {
            Write-Host "  [OK] Collector API activo en http://localhost:8888 (PID: $($CollectorProcess.Id))" -ForegroundColor Green
        } else {
            Write-Host "  [AVISO] Collector API tardando en responder. Verificando ejecucion..." -ForegroundColor DarkYellow
        }

        # 6.2 Iniciar AnythingLLM Server en segundo plano (puerto 3001)
        Write-Host "  Iniciando AnythingLLM Server en segundo plano (puerto 3001)..." -ForegroundColor Cyan
        $AnythingProcess = Start-Process -FilePath "node" -ArgumentList "index.js" -WorkingDirectory $ServerDir -WindowStyle Hidden -PassThru
        
        # Esperar a que AnythingLLM Server responda
        $esperaMax = 20
        $servidorListo = $false
        for ($i = 0; $i -lt $esperaMax; $i++) {
            Start-Sleep -Seconds 1
            try {
                $ping = Invoke-RestMethod -Uri "http://127.0.0.1:3001/api/ping" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($ping -and $ping.online) {
                    $servidorListo = $true
                    break
                }
            } catch {}
        }

        if ($servidorListo) {
            Write-Host "  [OK] AnythingLLM Server activo en http://localhost:3001 (PID: $($AnythingProcess.Id))" -ForegroundColor Green
        } else {
            Write-Host "  [AVISO] AnythingLLM Server tardando en responder. Verificando ejecucion..." -ForegroundColor DarkYellow
        }

        if ($Modo -eq "Dev") {
            Write-Host "  Iniciando Vite Frontend Dev Server (puerto 3000)..." -ForegroundColor Cyan
            $ViteProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" -WorkingDirectory $FrontendDir -WindowStyle Minimized -PassThru
            Write-Host "  [OK] Vite Dev Server activo en http://localhost:3000" -ForegroundColor Green
        }
    }

    # 7. Apertura Automatica en el Navegador
    if (-not $NoBrowser) {
        Write-Host ""
        Write-Host "  Abriendo navegadores predeterminados..." -ForegroundColor Gray
        Start-Process "http://localhost:3001"
        Start-Process "http://localhost:8000"
    }

    # 8. Lanzar Gateway Base (FastAPI + Dashboard 360) en primer plano
    Write-Host ""
    Write-Host "[5/5] Levantando Servidor Gateway Base y Dashboard 360 en http://localhost:8000..." -ForegroundColor Green
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host "  ACCESO A LA PLATAFORMA:" -ForegroundColor Yellow
    Write-Host "  -> AnythingLLM (Interfaz Web & Chat) : http://localhost:3001" -ForegroundColor Cyan
    Write-Host "  -> Dashboard 360 & Telemetria        : http://localhost:8000" -ForegroundColor Green
    Write-Host "  -> Collector (Ingesta Documental)    : http://localhost:8888" -ForegroundColor DarkGray
    Write-Host "  -> Gateway OpenAI Compatible (/v1)   : http://localhost:8000/v1" -ForegroundColor White
    Write-Host "  -> Documentacion Swagger API         : http://localhost:8000/docs" -ForegroundColor Gray
    if ($Modo -eq "Dev") {
        Write-Host "  -> Frontend Vite Dev Hot-Reload      : http://localhost:3000" -ForegroundColor Magenta
    }
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host "Presiona Ctrl+C para detener todos los servicios de la plataforma." -ForegroundColor Gray
    Write-Host ""

    Set-Location $BaseDir
    $ServidorScript = Join-Path $BaseDir "servidor_api.py"
    & $PythonExe $ServidorScript
}
finally {
    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Yellow
    Write-Host "  Cerrando servicios de la plataforma..." -ForegroundColor Yellow
    Write-Host "======================================================================" -ForegroundColor Yellow
    
    if ($CollectorProcess -and -not $CollectorProcess.HasExited) {
        Write-Host "  Deteniendo Collector API (PID: $($CollectorProcess.Id))..." -ForegroundColor Gray
        Stop-Process -Id $CollectorProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($AnythingProcess -and -not $AnythingProcess.HasExited) {
        Write-Host "  Deteniendo AnythingLLM Server (PID: $($AnythingProcess.Id))..." -ForegroundColor Gray
        Stop-Process -Id $AnythingProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($ViteProcess -and -not $ViteProcess.HasExited) {
        Write-Host "  Deteniendo Vite Dev Server (PID: $($ViteProcess.Id))..." -ForegroundColor Gray
        Stop-Process -Id $ViteProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  [OK] Todos los servicios detenidos correctamente." -ForegroundColor Green
}
