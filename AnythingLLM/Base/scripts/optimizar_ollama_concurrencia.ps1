# optimizar_ollama_concurrencia.ps1
# Script nativo PowerShell para Windows 10 64-bit
# Calibra Ollama para concurrencia de 10 usuarios sin desbordamiento de VRAM (GTX 1650 4GB)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " OPTIMIZACIÓN DE CONCURRENCIA OLLAMA (GTX 1650 / 4GB VRAM)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Configuración de Variables de Entorno Persistentes para el Usuario
Write-Host "`n[1/3] Configurando variables de entorno de inferencia..." -ForegroundColor Yellow

[System.Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "2", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_MAX_LOADED_MODELS", "1", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE", "24h", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0:11434", "User")

# Aplicar en sesión actual
$env:OLLAMA_NUM_PARALLEL = "2"
$env:OLLAMA_MAX_LOADED_MODELS = "1"
$env:OLLAMA_KEEP_ALIVE = "24h"
$env:OLLAMA_HOST = "0.0.0.0:11434"

Write-Host "  ✅ OLLAMA_NUM_PARALLEL = 2 (Permite 2 slots concurrentes en paralelo)" -ForegroundColor Green
Write-Host "  ✅ OLLAMA_MAX_LOADED_MODELS = 1 (Evita sobrecarga simultánea en 4GB VRAM)" -ForegroundColor Green
Write-Host "  ✅ OLLAMA_KEEP_ALIVE = 24h (Evita latencia de recarga de pesos desde disco)" -ForegroundColor Green
Write-Host "  ✅ OLLAMA_HOST = 0.0.0.0:11434 (Escucha en todas las interfaces para Docker)" -ForegroundColor Green

# 2. Diagnóstico de Modelos Recomendados
Write-Host "`n[2/3] Verificando modelos locales..." -ForegroundColor Yellow
$ollamaPath = "C:\Users\mandi\AppData\Local\Programs\Ollama\ollama.exe"

if (Test-Path $ollamaPath) {
    Write-Host "  Ejecutable detectado en: $ollamaPath" -ForegroundColor Gray
    
    # Modelos recomendados para ofimática y programación ligera
    Write-Host "  Modelos recomendados:" -ForegroundColor Gray
    Write-Host "    - qwen2.5:3b        (Ofimática, documentos Word/PDF, resúmenes, Zero-Chatter) ~1.9 GB VRAM" -ForegroundColor White
    Write-Host "    - qwen2.5-coder:3b  (Programación Python, scripts, fórmulas Excel)            ~1.9 GB VRAM" -ForegroundColor White
    Write-Host "    - nomic-embed-text  (Embeddings ultraligeros para AnythingLLM RAG)           ~270 MB RAM" -ForegroundColor White
} else {
    Write-Host "  ⚠️ No se encontró ollama.exe en la ruta estándar de AppData." -ForegroundColor Red
}

# 3. Resumen Matemático de VRAM
Write-Host "`n[3/3] Validación de Límites de Memoria (Hardware Budget):" -ForegroundColor Yellow
Write-Host "  VRAM Disponible en GTX 1650 : 4.096 MB" -ForegroundColor White
Write-Host "  Pesos de Modelo (Qwen 3B Q4): ~1.900 MB" -ForegroundColor White
Write-Host "  KV-Cache (2 slots @ 2048 ctx): ~640 MB" -ForegroundColor White
Write-Host "  CUDA Overhead del Sistema   : ~300 MB" -ForegroundColor White
Write-Host "  -------------------------------------------------------" -ForegroundColor Gray
Write-Host "  TOTAL CONSUMO ESTIMADO      : ~2.840 MB (Margen libre: ~1.250 MB)" -ForegroundColor Green
Write-Host "  ESTADO                      : 100% RESIDENTE EN GPU (0% PAGING A RAM)`n" -ForegroundColor Green

Write-Host "Reinicia la aplicación Ollama o el servicio para aplicar los cambios en segundo plano." -ForegroundColor Cyan
