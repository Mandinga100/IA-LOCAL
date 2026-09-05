# Política de Backup — Asistente Integral 360

**Clasificación:** GOBERNANZA OPERATIVA  
**Versión:** 1.0  
**Fecha:** 2026-07-04  
**Próxima revisión:** 2026-10-04  

---

## Principio: Backup Único Rotativo

> **REGLA CRÍTICA:** Solo existe **UN backup activo** en todo momento.  
> Antes de generar un nuevo backup, el anterior **DEBE ser eliminado**.  
> El objetivo es mantener el proyecto liviano y evitar el colapso por peso acumulado.

---

## Ubicación

```
landing360/
└── backup/
    └── backup-asistente360-YYYY-MM-DD.zip   ← único archivo permitido
```

- La carpeta `backup/` está en `.gitignore` — **nunca se versiona**.
- El nombre sigue el formato fijo: `backup-asistente360-YYYY-MM-DD.zip`.

---

## Contenido del Backup

El backup comprimido incluye **todo el proyecto excepto**:

| Excluido | Razón |
|:---------|:------|
| `node_modules/` | Regenerable con `npm install` |
| `functions/node_modules/` | Regenerable con `npm install` en `/functions` |
| `.next/` | Regenerable con `npm run build` |
| `.git/` | El historial completo está en GitHub |
| `backup/` | Evitar backup del backup |

---

## Procedimiento de Backup (Protocolo Obligatorio)

### Paso 1 — Verificar estado limpio
```powershell
git status    # debe estar limpio y pusheado
git log --oneline origin/main..HEAD   # debe ser vacío
```

### Paso 2 — Eliminar backup anterior
```powershell
# Verificar existencia del backup anterior
Get-ChildItem "backup\" -Filter "*.zip"

# Eliminar
Remove-Item "backup\backup-asistente360-*.zip" -Force
```

### Paso 3 — Generar nuevo backup
```powershell
$date = Get-Date -Format "yyyy-MM-dd"
$backupName = "backup-asistente360-$date.zip"
$sourceDir = "C:\Users\mandi\Documents\Proyectos\Web\landing360"
$backupDir = "$sourceDir\backup"
if (-not (Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir | Out-Null }

$excludeDirs = @(".next", "node_modules", ".git", "functions\node_modules", "backup")
$files = Get-ChildItem -Path $sourceDir -Recurse | Where-Object {
    $fp = $_.FullName
    -not ($excludeDirs | Where-Object { $fp -like "*\$_\*" -or $fp -like "*\$_" })
}
Compress-Archive -Path $files.FullName -DestinationPath "$backupDir\$backupName" -Force
$size = [math]::Round((Get-Item "$backupDir\$backupName").Length / 1MB, 2)
Write-Output "✅ Backup: $backupName ($size MB)"
```

### Paso 4 — Registrar en history.md
Agregar entrada en `ai-harness/progress/history.md` con fecha, tamaño y motivo.

---

## Cuándo Hacer Backup

| Evento | Acción |
|:-------|:-------|
| Después de build + tests verdes | ✅ Hacer backup |
| Antes de cambio arquitectónico mayor | ✅ Hacer backup |
| Después de purga o limpieza masiva | ✅ Hacer backup |
| Sin cambios significativos | ❌ No hacer backup innecesario |
| En cada sesión de trabajo | ❌ No obligatorio — git es la fuente de verdad |

---

## Verificación Post-Backup

```powershell
# Verificar que solo existe un backup
$backups = Get-ChildItem "backup\" -Filter "*.zip"
if ($backups.Count -gt 1) { Write-Warning "ALERTA: Más de un backup detectado. Eliminar el anterior." }
if ($backups.Count -eq 1) { Write-Output "✅ Política de backup único cumplida. Archivo: $($backups.Name)" }
```

---

## Jerarquía de Autoridad

Esta política está referenciada en:
- `HARNESS.md §8` — Sección de backup en el protocolo del agente
- `AGENTS.md` — Reglas operativas del repositorio

---

*Política establecida: 2026-07-04 · Autor: Agente IA · Revisión: 2026-10-04*
