# Plataforma de Procesamiento y Corrección de Documentos con IA Local

![Python](https://img.shields.io/badge/Python-3.13.14-blue.svg)
![OS](https://img.shields.io/badge/Platform-Windows%2010%2064--bit-0078D6.svg)
![Tests](https://img.shields.io/badge/Tests-60%20passed%20%7C%201%20skipped-success.svg)
![Coverage](https://img.shields.io/badge/Coverage-92%25-brightgreen.svg)
![Ollama](https://img.shields.io/badge/Inference-Ollama%20Local-black.svg)
![ECC](https://img.shields.io/badge/Governance-ECC%20v2.0.0-purple.svg)

Sistema industrial y desacoplado para el procesamiento masivo, normalización, corrección de estilo/ortografía con **Modelos de Lenguaje Locales (LLM)** y reconstrucción de documentos en múltiples formatos ofimáticos, operando **100% desconectado de la nube (offline)** sobre **Windows 10 / 11 64-bit**.

---

## 🌟 Características Principales

1. **Soberanía y Privacidad Total:** Cero transmisión de datos a APIs externas. Inferencia ejecutada 100% en la GPU/CPU local vía Ollama.
2. **Compatibilidad Universal de Formatos:** Ingestión y reconstrucción nativa para:
   - **Documentos de Texto:** `.docx`, `.doc`, `.odt`, `.rtf`, `.txt`, `.md`, `.html`
   - **Hojas de Cálculo y Datos:** `.csv` (a tablas Markdown), `.xlsx`, `.xls`
   - **Presentaciones y Publicaciones:** `.pptx`, `.ppt`, `.pdf`
3. **Decodificación Adaptativa Anti-Mojibakes:** Detección en cascada (UTF-8 $\rightarrow$ Windows CP1252 $\rightarrow$ Latin-1) para garantizar que ningún documento presente caracteres rotos.
4. **Chunking Semántico Jerárquico:** Respeto estricto a párrafos dobles (`\n\n`) con subdivisión automática por oraciones en bloques continuos, previniendo desbordamientos de contexto (`num_ctx`).
5. **Seguridad y Fronteras de Ingestión:** Sniffer de Magic Bytes contra ejecutables maliciosos (`MZ`, `ELF`), guardias de Path Traversal y límite de tamaño preventivo (50 MB).
6. **Ledger de Idempotencia:** Reanudación instantánea por hash SHA-256 a más de **2.900 documentos/segundo**.
7. **Aislamiento Seguro:** Cuarentena automática con `shutil.copy2` en `datos/errores/` ante cualquier documento malformado sin interrumpir el lote.
8. **Sistema de Backup Consolidado:** Mantiene un único archivo comprimido en `backup/` con GZIP nivel 9 y rotación automática.

---

## 🏗️ Arquitectura del Pipeline

```
 [Directorio Entrada]
         │
         ▼
 ┌───────────────┐
 │ explorador.py │ ◄── Filtro Office (~$*), Path Traversal, Magic Bytes y Límite 50 MB
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ conversor.py  │ ◄── Auto-Encoding UTF-8/CP1252, MarkItDown, odfpy, striprtf, csv.Sniffer
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ corrector.py  │ ◄── Chunking jerárquico, Prompts especializados, Reintentos y Fallback
 └───────┬───────┘
         │
         ▼
 ┌──────────────────┐
 │ reconstructor.py │ ──► DOCX, ODT, RTF, CSV, HTML, TXT, MD y exportación .PDF
 └───────┬──────────┘
         │
         ▼
 ┌────────────────────┐
 │ procesador_lote.py │ ──► Salida con Ledger SHA-256 / Cuarentena en datos/errores/
 └────────────────────┘
```

---

## 🚀 Inicio Rápido en Windows 10 / 11

### 1. Preparar Entorno Virtual
```powershell
# Configurar UTF-8 en PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

# Crear venv e instalar dependencias con uv
uv venv .venv --python 3.13
uv pip install --python .venv -r requirements.txt
```

### 2. Iniciar Ollama y Descargar Modelo
```powershell
# Para GPUs de 4 GB VRAM (GTX 1650 / Laptops):
ollama pull qwen2.5:3b
ollama pull qwen2.5-coder:3b

# Para GPUs de 8-16 GB VRAM (RTX 3060 / 4060):
ollama pull qwen2.5:7b
```

### 3. Ejecutar Procesamiento por Lotes
```powershell
.\.venv\Scripts\python.exe procesador_lote.py `
    --origen "datos/entrada" `
    --destino "datos/salida" `
    --tipo "general" `
    --modelo "qwen2.5:3b" `
    --chunk-size 1800
```

---

## 🧪 Suite de Pruebas y Cobertura (TDD)

```powershell
.\.venv\Scripts\pytest.exe --cov=. --cov-report=term-missing
```
- **60 pruebas unitarias e integración PASADAS** (1 omitida por entorno).
- **Cobertura global certificada del 92%**.

---

## 💾 Generar / Actualizar Backup Consolidado

```powershell
.\.venv\Scripts\python.exe scripts/generar_backup.py
```
*Genera un archivo `.tar.gz` optimizado (27 MB) en `backup/` y elimina versiones anteriores automáticamente.*

---

## 📚 Estructura Documental

- [docs/contexto_proyecto.md](docs/contexto_proyecto.md): Alcance, restricciones y stack técnico.
- [docs/planificacion_y_arquitectura.md](docs/planificacion_y_arquitectura.md): Arquitectura detallada, principios ECC y flujos.
- [docs/guia_operativa.md](docs/guia_operativa.md): Manual operativo de comandos, perfiles de GPU y troubleshooting.
- [docs/especificacion_tdd_y_pruebas.md](docs/especificacion_tdd_y_pruebas.md): Matriz de pruebas y certificación de cobertura.
- [docs/reportes_ejecucion_mvp/](docs/reportes_ejecucion_mvp/README.md): Informes ejecutivos, telemetría de GTX 1650 y calidad de inferencia.
- [docs/auditoria_360_y_transformaciones/](docs/auditoria_360_y_transformaciones/README.md): Auditorías forenses y especificación de 14 formatos.
- [MVP/](MVP/README.md): Laboratorio de pruebas parciales en hardware restringido.
