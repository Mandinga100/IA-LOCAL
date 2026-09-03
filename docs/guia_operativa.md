# Guía Operativa y Manual de Uso: Plataforma IA Local

**Versión:** 0.3.0 (Consolidada)  
**Entorno Operativo:** Windows 10 Pro 64-bit | PowerShell 5.1 / 7+ | Python 3.13  
**Modelos Homologados:** `qwen2.5:3b`, `qwen2.5-coder:3b`, `qwen2.5:7b`, `llama3.1:8b`  
**Formatos Soportados:** `.pdf`, `.docx`, `.doc`, `.odt`, `.rtf`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.csv`, `.html`, `.txt`, `.md`

---

## 1. Requisitos Previos

1. **Windows 10 / 11 64-bit** con PowerShell 5.1 o PowerShell Core 7+.
2. **Python 3.13 64-bit** instalado en el sistema.
3. **Gestor de paquetes `uv`** (recomendado para instalación ultrarrápida de dependencias).
4. **Ollama para Windows** instalado y corriendo como servicio (`http://localhost:11434`).

---

## 2. Preparación e Instalación del Entorno

```powershell
# 1. Configurar codificación UTF-8 en PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

# 2. Crear entorno virtual con Python 3.13
uv venv .venv --python 3.13

# 3. Instalar dependencias completas del pipeline
uv pip install --python .venv -r requirements.txt
```

---

## 3. Puesta en Marcha de Ollama y Perfiles de Hardware

### A. Perfil Desarrollo y MVP Local (NVIDIA GeForce GTX 1650 4 GB VRAM)
```powershell
# Modelos textuales compactos (consumo VRAM ~2.0 - 2.4 GB, contexto 2048)
ollama pull qwen2.5:3b
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5:1.5b   # Fallback ligero

# Modelo visual multimodal (VLM) para pruebas MVP locales
ollama pull qwen2.5vl:3b
```

### B. Perfil Producción / Workstation (PNY Quadro RTX PRO 4000 24 GB Blackwell + i9-14900 + 128 GB RAM)
```powershell
# Modelos de producción de alta fidelidad y contexto largo (32K - 65K)
ollama pull qwen2.5-coder:32b   # Ancla principal para doc_main, chat_ui y code_ui (~19.5 GB)
ollama pull deepseek-r1:32b     # Razonamiento profundo y auditoría crítica (doc_deep)
ollama pull qwen2.5:14b         # Procesador intermedio de alto rendimiento
ollama pull qwen2.5:7b          # Ingesta masiva ultra-rápida (doc_fast)

# Modelos visuales multimodales (VLM) para producción
ollama pull qwen2.5vl:7b        # Comprensión de diagramas, layouts y tablas complejas (doc_vlm)
ollama pull gemma3:4b           # Fallback multimodal ligero y documentos multilingües
```

---

## 4. Ejecución del Procesador por Lotes (`procesador_lote.py`)

### Sintaxis Básica
```powershell
.\.venv\Scripts\python.exe procesador_lote.py --origen "datos/entrada" --destino "datos/salida" --tipo "general"
```

### Argumentos CLI Completos

| Argumento | Tipo | Default | Descripción |
|---|---|---|---|
| `--origen` | `str` | `datos/entrada` | Directorio raíz donde se ubican los documentos a procesar. |
| `--destino` | `str` | `datos/salida` | Directorio destino para documentos corregidos y reconstruidos. |
| `--tipo` | `str` | `general` | Estilo y prompt: `general`, `legal`, `tecnico`, `academico`, `comercial`. |
| `--modelo` | `str` | `qwen2.5:7b` | Modelo principal en Ollama (ej. `qwen2.5:3b` para GTX 1650). |
| `--fallback` | `str` | `None` | Modelo secundario alternativo si el principal agota reintentos. |
| `--chunk-size` | `int` | `3500` | Límite máximo de caracteres por chunk semántico (usar 1800 para 4 GB VRAM). |
| `--url` | `str` | `http://localhost:11434` | Endpoint local de la API de Ollama. |

### Ejemplos Prácticos de Ejecución

#### Ejemplo 1: Lote Técnico en GPU GTX 1650 (Presupuesto 4 GB)
```powershell
.\.venv\Scripts\python.exe procesador_lote.py `
    --origen "datos/entrada_mvp/lote_c_tecnico" `
    --destino "datos/salida_mvp" `
    --tipo "tecnico" `
    --modelo "qwen2.5-coder:3b" `
    --chunk-size 1800
```

#### Ejemplo 2: Lote Ofimático Multiformato con Fallback
```powershell
.\.venv\Scripts\python.exe procesador_lote.py `
    --origen "C:\Documentos\Ofimatica" `
    --destino "C:\Documentos\Corregidos" `
    --tipo "comercial" `
    --modelo "qwen2.5:3b" `
    --fallback "qwen2.5:1.5b"
```

---

## 5. Auditoría, Ledger y Aislamiento de Errores

- **Ledger `historial_procesados.json`:** Registra el hash SHA-256 de cada documento procesado. Las re-ejecuciones son idempotentes y omiten archivos idénticos a más de **2.900 docs/segundo**.
- **Aislamiento `datos/errores/`:** Los documentos corruptos, protegidos o malformados se archivan automáticamente en la carpeta de errores sin abortar el procesamiento del resto del lote.
- **Sniffer de Magic Bytes:** Rechaza proactivamente ejecutables camuflados (`MZ`, `ELF`) evitando ataques o conversiones erróneas.
- **Detección Anti-Mojibake:** Lectura multicapa UTF-8 -> CP1252 -> Latin-1 garantizando preservación de tildes y eñes en cualquier archivo Windows.

---

## 6. Servidor API Web Local y Compatibilidad con Open WebUI

La plataforma expone un servidor FastAPI de alto rendimiento que incluye endpoints REST nativos y una pasarela compatible con OpenAI (`/v1`):

### Puesta en Marcha del Servidor
```powershell
.\.venv\Scripts\python.exe servidor_api.py
```
- **Frontend Web Local:** `http://localhost:8000` (Interfaz gráfica integrada).
- **API Health Check:** `http://localhost:8000/api/salud`.
- **Catálogo de Perfiles Activos:** `http://localhost:8000/api/perfiles`.

### Configuración en Open WebUI
Para utilizar la suite completa de perfiles lógicos desde Open WebUI:
1. En Open WebUI, ir a **Configuración > Conexiones > Proveedores OpenAI**.
2. Configurar la URL base: `http://localhost:8000/v1` (o la IP local de la máquina).
3. Clave API: Cualquier valor simulado (ej. `local-key`).
4. Los modelos aparecerán automáticamente listados por perfil operativo (`doc_fast`, `doc_main`, `doc_deep`, `chat_ui`, `code_ui`).

---

## 7. Gestión del Sistema de Backups

El proyecto cuenta con un generador automatizado que mantiene **un único backup consolidado y optimizado** en `backup/`:

```powershell
# Actualizar el backup consolidado al estado actual
.\.venv\Scripts\python.exe scripts/generar_backup.py
```

---

## 8. Ejecución de la Suite de Pruebas Automatizadas (TDD)

```powershell
# Ejecutar todas las 84 pruebas unitarias e integración
.\.venv\Scripts\pytest.exe -v
```
