# lanzar_frontend_visual.ps1
# Script nativo PowerShell para Windows 10/11 64-bit
# Lanza el Frontend Visual e Interfaz Web de la Plataforma IA Local con Servidor API

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " LANZANDO FRONTEND VISUAL Y SERVIDOR API (IA LOCAL)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$Raiz = (Get-Item $PSScriptRoot).Parent.FullName
$PythonExe = Join-Path $Raiz ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "❌ No se encontró el entorno virtual en .venv" -ForegroundColor Red
    Write-Host "👉 Ejecuta primero: uv venv .venv --python 3.13" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n🌐 Interfaz Web Visual disponible en: http://localhost:8000" -ForegroundColor Green
Write-Host "📊 Telemetría GPU y API REST activa en: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Presiona Ctrl+C para detener el servidor.`n" -ForegroundColor Gray

# Iniciar el servidor API y Frontend
& $PythonExe (Join-Path $Raiz "servidor_api.py")
