# desplegar_anythingllm_produccion.ps1
# Script nativo PowerShell para Windows 10/11 / Windows Server
# Despliega AnythingLLM Multi-User en la máquina de producción

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " DESPLIEGUE ANYTHINGLLM MULTI-USER PRODUCCIÓN (Workstation 24GB) " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Comprobación de Docker
Write-Host "`n[1/4] Verificando motor Docker..." -ForegroundColor Yellow
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue

if (-not $dockerCmd) {
    Write-Host "❌ Docker no está instalado en el PATH del sistema." -ForegroundColor Red
    Write-Host "👉 Instala Docker Desktop con backend WSL2 o Docker Engine en Windows Server." -ForegroundColor Yellow
    exit 1
}

# 2. Preparación de Directorio de Persistencia
Write-Host "`n[2/4] Verificando almacenamiento persistente de producción..." -ForegroundColor Yellow
$prodStorage = Join-Path $PSScriptRoot "..\..\docker_storage_prod"
if (-not (Test-Path $prodStorage)) {
    New-Item -ItemType Directory -Path $prodStorage -Force | Out-Null
    Write-Host "  Carpeta creada: $prodStorage" -ForegroundColor Gray
} else {
    Write-Host "  Carpeta verificada: $prodStorage" -ForegroundColor Gray
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
Write-Host "`n[4/4] Levantando contenedor AnythingLLM Multi-User de Producción..." -ForegroundColor Yellow
$composeFile = Join-Path $PSScriptRoot "..\docker-compose.yml"

if (Test-Path $composeFile) {
    & docker compose -f $composeFile up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n🎉 ¡AnythingLLM Multi-User Producción Activo!" -ForegroundColor Green
        Write-Host "🌐 URL de Acceso Local : http://localhost:3001" -ForegroundColor Cyan
        Write-Host "🌐 URL para Red Local  : http://<IP-WORKSTATION>:3001" -ForegroundColor Cyan
        Write-Host "⚙️ Pasos de Configuración en Producción:" -ForegroundColor White
        Write-Host "   1. Crea la cuenta de Administrador institucional." -ForegroundColor Gray
        Write-Host "   2. En Ajustes -> LLM Provider -> Ollama, ingresa:" -ForegroundColor Gray
        Write-Host "      URL: http://host.docker.internal:11434" -ForegroundColor White
        Write-Host "      Modelo por defecto: qwen2.5:14b" -ForegroundColor White
        Write-Host "   3. En Embeddings Provider -> Ollama, selecciona: bge-m3" -ForegroundColor White
        Write-Host "   4. Da de alta a los 10 usuarios y vincula los 4 workspaces de produccion/workspaces/." -ForegroundColor Gray
    } else {
        Write-Host "❌ Error al ejecutar docker compose." -ForegroundColor Red
    }
} else {
    Write-Host "❌ No se encontró el archivo docker-compose.yml." -ForegroundColor Red
}
