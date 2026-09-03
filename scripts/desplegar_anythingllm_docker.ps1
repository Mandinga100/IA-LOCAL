# desplegar_anythingllm_docker.ps1
# Script nativo PowerShell para Windows 10 64-bit
# Despliega y valida AnythingLLM Multi-User en Docker

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " DESPLIEGUE ANYTHINGLLM MULTI-USER DOCKER (Windows 10)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Comprobación de Docker
Write-Host "`n[1/4] Verificando motor Docker..." -ForegroundColor Yellow
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue

if (-not $dockerCmd) {
    Write-Host "❌ Docker no está instalado o no se encuentra en el PATH del sistema." -ForegroundColor Red
    Write-Host "👉 Por favor, asegúrate de instalar Docker Desktop para Windows:" -ForegroundColor Yellow
    Write-Host "   https://docs.docker.com/desktop/setup/install/windows-install/" -ForegroundColor Gray
    Write-Host "   Una vez instalado y en ejecución, vuelve a ejecutar este script.`n" -ForegroundColor Gray
    exit 1
}

try {
    $dockerInfo = & docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Docker está instalado pero el demonio (Docker Desktop) no parece estar en ejecución." -ForegroundColor Red
        Write-Host "👉 Inicia Docker Desktop desde el menú Inicio y reintenta.`n" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  ✅ Demonio Docker activo y respondiendo." -ForegroundColor Green
} catch {
    Write-Host "❌ Error al comunicarse con Docker: $_" -ForegroundColor Red
    exit 1
}

# 2. Preparar Almacenamiento Persistente
Write-Host "`n[2/4] Preparando almacenamiento local..." -ForegroundColor Yellow
$storageDir = Join-Path $PSScriptRoot "..\docker_storage"
if (-not (Test-Path $storageDir)) {
    New-Item -ItemType Directory -Path $storageDir -Force | Out-Null
    Write-Host "  Carpeta creada: $storageDir" -ForegroundColor Gray
} else {
    Write-Host "  Carpeta existente verificada: $storageDir" -ForegroundColor Gray
}

# 3. Comprobar Puerto 3001
Write-Host "`n[3/4] Verificando disponibilidad de puerto 3001..." -ForegroundColor Yellow
$portCheck = netstat -ano | findstr ":3001"
if ($portCheck) {
    Write-Host "  ⚠️ Advertencia: El puerto 3001 ya tiene actividad:" -ForegroundColor Yellow
    Write-Host "  $portCheck" -ForegroundColor Gray
} else {
    Write-Host "  ✅ Puerto 3001 libre." -ForegroundColor Green
}

# 4. Despliegue con Docker Compose
Write-Host "`n[4/4] Levantando contenedor AnythingLLM Multi-User..." -ForegroundColor Yellow
$composeFile = Join-Path $PSScriptRoot "..\docker-compose.yml"

if (Test-Path $composeFile) {
    & docker compose -f $composeFile up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n🎉 ¡Contenedor desplegado con éxito!" -ForegroundColor Green
        Write-Host "🌐 URL de Acceso Local : http://localhost:3001" -ForegroundColor Cyan
        Write-Host "🌐 URL para Red Local  : http://<IP-DE-TU-PC>:3001" -ForegroundColor Cyan
        Write-Host "⚙️ Primeros Pasos:" -ForegroundColor White
        Write-Host "   1. Abre http://localhost:3001 en tu navegador." -ForegroundColor Gray
        Write-Host "   2. Crea la cuenta de Administrador principal." -ForegroundColor Gray
        Write-Host "   3. En Ajustes -> LLM Provider, selecciona 'Ollama' con URL:" -ForegroundColor Gray
        Write-Host "      http://host.docker.internal:11434" -ForegroundColor White
        Write-Host "   4. En Ajustes -> Multi-User, habilita el registro de los 10 usuarios y crea los 4 workspaces." -ForegroundColor Gray
    } else {
        Write-Host "❌ Error al levantar el contenedor con Docker Compose." -ForegroundColor Red
    }
} else {
    Write-Host "❌ No se encontró docker-compose.yml en el directorio raíz." -ForegroundColor Red
}
