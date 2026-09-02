# Guía Operativa y Manual de Uso: Plataforma IA Local

## 1. Requisitos Previos

1. **Windows 10 64-bit** con PowerShell 5.1 o PowerShell 7+.
2. **Python 3.13 64-bit** o `py.exe` disponible.
3. **Gestor `uv`** (ubicado en `~/.local/bin/uv.exe` o instalado globalmente).
4. **Ollama para Windows** instalado y configurado.

---

## 2. Preparación del Entorno Virtual

Si se clona o despliega el proyecto en una nueva ubicación, se inicializa el entorno virtual aislado en segundos mediante `uv`:

```powershell
# 1. Forzar codificación UTF-8 en PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

# 2. Crear entorno virtual aislado (forma portable — recomendada)
uv venv .venv --python 3.13

# Alternativa con ruta absoluta (fallback de diagnóstico en esta máquina):
# & "C:\Users\mandi\.local\bin\uv.exe" venv .venv --python "C:\Users\mandi\AppData\Local\Programs\Python\Python313\python.exe"

# 3. Instalar dependencias exactas (dentro del venv)
uv pip install --python .venv -r requirements.txt
```

---

## 3. Puesta en Marcha de Ollama

Antes de lanzar un lote de producción, Ollama debe estar en ejecución y el modelo descargado:

```powershell
# Descargar el modelo óptimo para 8-12 GB VRAM
ollama pull qwen2.5:7b

# Iniciar el servicio local
ollama serve
```

---

## 4. Ejecución del Procesador por Lotes (`procesador_lote.py`)

### Sintaxis Básica
```powershell
.\.venv\Scripts\python.exe procesador_lote.py --origen "datos/entrada" --destino "datos/salida" --tipo "general"
```

### Argumentos de Línea de Comandos (CLI)

| Argumento | Tipo | Valor por Defecto | Descripción |
|---|---|---|---|
| `--origen` | `str` | `datos/entrada` | Carpeta raíz donde se ubican los documentos a procesar. |
| `--destino` | `str` | `datos/salida` | Carpeta donde se depositarán los documentos corregidos. |
| `--tipo` | `str` | `general` | Estilo y prompt: `general`, `legal`, `tecnico`, `academico`, `comercial`. |
| `--modelo` | `str` | `qwen2.5:7b` | Nombre del modelo en Ollama (`llama3.1:8b`, `qwen2.5:14b`). |
| `--url` | `str` | `http://localhost:11434` | Endpoint de la API local de Ollama. |

### Ejemplo: Corrección de Contratos Legales
```powershell
.\.venv\Scripts\python.exe procesador_lote.py `
    --origen "C:\Documentos\Contratos" `
    --destino "C:\Documentos\Contratos_Corregidos" `
    --tipo "legal" `
    --modelo "qwen2.5:7b"
```

---

## 5. Auditoría, Ledger y Reanudación de Fallos

- **Ledger `historial_procesados.json`:** Se genera automáticamente dentro de la carpeta de salida. Almacena el hash SHA-256 de cada archivo completado con su tamaño, modelo y fecha. Si el proceso se detiene a la mitad, al volver a ejecutar omitirá instantáneamente los documentos ya finalizados.
- **Aislamiento de Errores (`datos/errores/`):** Si un documento está corrupto o protegido con contraseña y falla la conversión o inferencia, se copia automáticamente a la carpeta de errores sin alterar el archivo original, permitiendo la continuidad ininterrumpida del lote.

---

## 6. Troubleshooting y Solución de Problemas Comunes

### 1. `InferenciaError: No fue posible obtener respuesta de Ollama`
- **Causa:** El servicio Ollama no está iniciado o la GPU se quedó sin memoria (OOM).
- **Solución:**
  1. Verificar que Ollama responda: `Invoke-RestMethod -Uri "http://localhost:11434/api/tags"`.
  2. Si hubo CUDA OOM, reducir el tamaño de chunk a 2.500 caracteres en `config.py` o usar un modelo más ligero cuantizado a 4 bits.

### 2. Mojibakes en la Consola de PowerShell
- **Causa:** PowerShell ejecutándose con página de códigos CP1252 o terminal heredada.
- **Solución:** Ejecutar siempre en el encabezado del script o sesión:
  ```powershell
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  $OutputEncoding = [System.Text.Encoding]::UTF8
  $env:PYTHONUTF8 = "1"
  ```

### 3. Error `MissingDependencyException` al procesar Word o PDF
- **Causa:** Faltan las extensiones completas de `MarkItDown`.
- **Solución:** Ejecutar:
  ```powershell
  uv pip install --python .venv "markitdown[all]"
  # Fallback ruta absoluta: & "C:\Users\mandi\.local\bin\uv.exe" pip install --python ".\.venv\Scripts\python.exe" "markitdown[all]"
  ```
