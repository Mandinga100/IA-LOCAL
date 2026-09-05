# Guía Operativa y Manual de Uso: Plataforma IA Local

**Versión:** 1.0.0 (Consolidada Multiplataforma y Monorepo)  
**Entorno Operativo:** Windows 10 / 11 Pro 64-bit | GNU/Linux (Ubuntu, Debian, Fedora) | Python 3.13.14  
**Modelos Homologados:** `qwen2.5:3b`, `qwen2.5-coder:3b`, `qwen2.5-coder:32b`, `deepseek-r1:14b/32b`, `qwen2.5vl:7b`  
**Formatos Soportados:** `.pdf`, `.docx`, `.doc`, `.odt`, `.rtf`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.csv`, `.html`, `.txt`, `.md`

---

## 1. Requisitos del Sistema

1. **Sistema Operativo:** Windows 10 / 11 64-bit (PowerShell 5.1 / Core 7+) o GNU/Linux (kernel 5.15+).
2. **Python:** Versión 3.13 64-bit.
3. **Gestor de Paquetes:** `uv` (recomendado) o `pip`.
4. **Ollama:** Instalado y ejecutándose localmente (`http://localhost:11434`).
5. **Docker Engine / Desktop:** Necesario para AnythingLLM multi-usuario (opcional si se usa AnythingLLM Desktop).

---

## 2. Preparación del Entorno de Ejecución

### En Windows 10 / 11 (PowerShell):
```powershell
# 1. Configurar codificación UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

# 2. Navegar a la carpeta base del motor
cd "c:\Users\mandi\Documents\Proyectos\Plataforma IA local\AnythingLLM\Base"

# 3. Crear entorno virtual con Python 3.13
uv venv .venv --python 3.13

# 4. Instalar dependencias completas
uv pip install -r requirements.txt
```

### En GNU/Linux (Bash):
```bash
export PYTHONUTF8=1
cd AnythingLLM/Base
uv venv .venv --python 3.13
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## 3. Puesta en Marcha de Ollama y Perfiles de Hardware

### A. Perfil Desarrollo y MVP Local (NVIDIA GeForce GTX 1650 4 GB VRAM)
```powershell
# Windows
.\scripts\optimizar_ollama_concurrencia.ps1
ollama pull qwen2.5:3b
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5vl:3b
```
```bash
# Linux
chmod +x scripts/*.sh
./scripts/optimizar_ollama_concurrencia.sh
ollama pull qwen2.5:3b
ollama pull qwen2.5-coder:3b
```

### B. Perfil Producción / Workstation (PNY Quadro RTX PRO 4000 24 GB Blackwell + i9-14900)
```powershell
# Windows
.\produccion\scripts\optimizar_ollama_produccion.ps1
ollama pull qwen2.5-coder:32b
ollama pull deepseek-r1:32b
ollama pull qwen2.5vl:7b
```
```bash
# Linux
chmod +x produccion/scripts/*.sh
./produccion/scripts/optimizar_ollama_produccion.sh
ollama pull qwen2.5-coder:32b
ollama pull deepseek-r1:32b
```

---

## 4. Modos Operativos de la Plataforma

### Modo 1: Dashboard Visual 360° (Consola Web con 5 Pestañas y Telemetría)
Permite procesar arrastrando archivos, monitorear la VRAM/GPU en tiempo real, comparar documentos y auditar el protocolo Zero-Chatter.

```powershell
# En Windows:
.\scripts\lanzar_frontend_visual.ps1
```
```bash
# En Linux:
./scripts/lanzar_frontend_visual.sh
```
- URL de acceso: `http://localhost:8080` (o `http://localhost:8000/dashboard`).

---

### Modo 2: Servidor API Gateway y Compatibilidad OpenAI (`/v1`)
Inicia el backend FastAPI compatible con la especificación de OpenAI para conectar con AnythingLLM y Open WebUI.

```powershell
# En Windows:
.\.venv\Scripts\python.exe servidor_api.py
```
```bash
# En Linux:
python servidor_api.py
```
- Documentación Swagger interactiva: `http://localhost:8000/docs`
- Endpoint OpenAI chat: `http://localhost:8000/v1/chat/completions`
- Endpoint Telemetría 360°: `http://localhost:8000/api/telemetria/360`

---

### Modo 3: AnythingLLM Multi-Usuario en Docker (10 Usuarios Concurrentes)
Despliega el contenedor de AnythingLLM con 4 workspaces preconfigurados y aislamiento departamental.

```powershell
# En Windows:
.\scripts\desplegar_anythingllm_docker.ps1
```
```bash
# En Linux:
./scripts/desplegar_anythingllm_docker.sh
```
- Acceso a AnythingLLM: `http://localhost:3001`

---

### Modo 4: Procesamiento por Lotes CLI (`procesador_lote.py`)
Ideal para procesamiento automatizado desatendido en carpetas locales o unidades de red.

```powershell
.\.venv\Scripts\python.exe procesador_lote.py `
    --origen "datos/entrada" `
    --destino "datos/salida" `
    --tipo "tecnico" `
    --modelo "qwen2.5-coder:3b" `
    --fallback "qwen2.5:3b" `
    --chunk-size 1800
```

#### Argumentos CLI Completos:
| Argumento | Tipo | Default | Descripción |
|---|---|---|---|
| `--origen` | `str` | `datos/entrada` | Carpeta origen con documentos a procesar. |
| `--destino` | `str` | `datos/salida` | Carpeta destino para documentos reconstruidos. |
| `--tipo` | `str` | `general` | Estilo: `general`, `legal`, `tecnico`, `academico`, `comercial`. |
| `--modelo` | `str` | `qwen2.5:7b` | Modelo principal en Ollama (usar `qwen2.5:3b` para 4GB). |
| `--fallback` | `str` | `None` | Modelo alternativo si el principal falla. |
| `--chunk-size` | `int` | `3500` | Límite de caracteres por chunk (1800 para GTX 1650). |
| `--url` | `str` | `http://localhost:11434` | Endpoint HTTP de Ollama. |

---

### Modo 5: Verificación de Gobernanza del Arnés /ECC
Valida criptográficamente los permisos de modificación de las carpetas protegidas (`ECC/` y `ai-harness/ecc/`).

```powershell
# En Windows:
.\scripts\verificar_permisos_ecc.ps1
```
```bash
# En Linux:
./scripts/verificar_permisos_ecc.sh "Nombre Candidato"
```

---

## 5. Ejecución de la Suite de Pruebas Automatizadas (TDD)

Para certificar la integridad del sistema y validar la suite completa de **176 pruebas automatizadas**:

```powershell
# En Windows:
.\.venv\Scripts\python.exe -m pytest tests/ -q
```
```bash
# En Linux:
pytest tests/ -q
```

---

## 6. Generación de Backups Consolidados

Para crear una copia de seguridad compactada del estado del proyecto:

```powershell
.\.venv\Scripts\python.exe scripts\generar_backup.py
```
```bash
python scripts/generar_backup.py
```
El archivo ZIP consolidado se generará en la carpeta `backup/`.
