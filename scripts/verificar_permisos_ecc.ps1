# scripts/verificar_permisos_ecc.ps1
# Validación criptográfica de inmutabilidad para el arnés /ecc (raíz y ai-harness/ecc)
# Windows 10 64-bit PowerShell

param (
    [string]$NombreCandidato = ""
)

$HASH_SELLADO_DEFAULT = "b42c3725f996d2937b402298812f10ac4207c47992d73f0bd81d5eea07d1e8dd"
$hashEsperado = if ($env:CEO_AUTH_HASH) { $env:CEO_AUTH_HASH } else { $HASH_SELLADO_DEFAULT }

function Normalizar-Texto ([string]$t) {
    if (-not $t) { return "" }
    $t = $t.Trim().ToLower()
    $normalizado = [System.Text.Encoding]::ASCII.GetString([System.Text.Encoding]::GetEncoding("Cyrillic").GetBytes($t))
    # Colapsar espacios
    return ($t -replace '\s+', ' ').Trim()
}

function Calcular-HashSHA256 ([string]$texto) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($texto)
    $hasher = [System.Security.Cryptography.SHA256]::Create()
    $hashBytes = $hasher.ComputeHash($bytes)
    return [System.BitConverter]::ToString($hashBytes).Replace("-", "").ToLower()
}

# 1. Solicitar nombre si no fue suministrado por argumento o entorno
if (-not $NombreCandidato) {
    if ($env:CEO_AUTH_SESSION_NAME) {
        $NombreCandidato = $env:CEO_AUTH_SESSION_NAME
    } else {
        Write-Host "🛡️ GOBERNANZA /ECC: Acceso a Zonas Inmutables (raíz o ai-harness)" -ForegroundColor Yellow
        $NombreCandidato = Read-Host "Ingrese el nombre de CEO autorizado para continuar"
    }
}

$norm = Normalizar-Texto $NombreCandidato
$hashCalc = Calcular-HashSHA256 $norm

if ($hashCalc -eq $hashEsperado.ToLower()) {
    Write-Host "✅ Identidad de CEO verificada criptográficamente. Permiso de modificación concedido." -ForegroundColor Green
    $env:CEO_AUTH_SESSION_TOKEN = $norm
    exit 0
} else {
    Write-Host "⛔ ACCESO DENEGADO: El nombre ingresado no coincide con el CEO autorizado." -ForegroundColor Red
    Write-Host "Las carpetas 'ECC/' y 'ai-harness/ecc/' permanecen inmutables y protegidas contra escritura." -ForegroundColor Red
    exit 1
}
