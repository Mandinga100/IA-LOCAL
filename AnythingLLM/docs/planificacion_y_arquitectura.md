# Planificación y Arquitectura Técnica del Sistema

**Versión:** 1.0.0 (Consolidada Multiplataforma y Monorepo)  
**Entorno Operativo:** Windows 10 / 11 Pro 64-bit | GNU/Linux | Python 3.13  
**Estándar de Gobernanza:** Enterprise Coding Constitution (ECC v2.0.0) con Guardia Criptográfica SHA-256

---

## 1. Principios de Arquitectura bajo Gobernanza ECC

La arquitectura de la plataforma responde a los principios rectores del marco **ECC v2.0.0**:
- **Agent-First y Especialización:** Desacoplamiento funcional entre agentes de diseño, seguridad, rendimiento y calidad.
- **Inmutabilidad de Estructuras Compartidas:** Modelado sistemático con `@dataclass(frozen=True)` para todas las estructuras compartidas (`Config`, `DocumentoTarea`, `ChunkTexto`, `TaskProfile`).
- **Tolerancia Cero a Fallos Silenciosos (`silent-failure-hunter`):** Prohibición terminante de bloques `except: pass` o retornos nulos sin registro estructurado ni aislamiento preventivo del documento afectado en `datos/errores/`.
- **Seguridad Criptográfica y Fronteras (`security-reviewer`):**
  - Blindaje contra *Path Traversal* mediante `Path.resolve().is_relative_to()`.
  - Sniffer de firmas ejecutables (`MZ` de Windows y `\x7FELF` de Linux).
  - Límite preventivo de tamaño por documento (50 MB) y contra bombas de descompresión gráfica (*Pixel Flood DoS*, max 50M px).
  - Protección de arneses `/ECC` mediante verificación unidireccional SHA-256 autorizada exclusivamente por el CEO sin nombres en texto claro.
- **Resiliencia Lingüística:** Decodificación adaptativa en cascada UTF-8 -> CP1252 -> Latin-1 para erradicar mojibakes en terminales y archivos legados.

---

## 2. Diagrama de Flujo del Pipeline de Procesamiento Integral

```
                     [Directorio de Entrada / Carga Web Drag-and-Drop]
                                            │
                                            ▼
                             ┌─────────────────────────────┐
                             │       explorador.py         │ ◄── Omitir temporales Office (~$*)
                             │  (Hash SHA-256 + Tarea)     │ ◄── Guardia Path Traversal (is_relative_to)
                             │                             │ ◄── Sniffer Magic Bytes (MZ / ELF)
                             │                             │ ◄── Límite máx 50MB / Prevención DoS
                             └──────────────┬──────────────┘
                                            │
                                            ▼
                             ┌─────────────────────────────┐
                             │   ¿Hash ya en Ledger?       │ ──► [Omitir: ya procesado a >2.900 docs/s]
                             └──────────────┬──────────────┘
                                            │ NO
                                            ▼
                             ┌─────────────────────────────┐
                             │        conversor.py         │ ◄── Auto-encoding (UTF-8, CP1252, Latin-1)
                             │   (Markdown UTF-8 limpio)   │ ◄── MarkItDown (DOCX/PDF/PPTX/XLSX/HTML)
                             │                             │ ◄── odfpy (ODT), striprtf (RTF), xlrd (XLS)
                             │                             │ ◄── csv.Sniffer (CSV a tablas Markdown)
                             └──────────────┬──────────────┘
                                            │
                      ┌─────────────────────┴─────────────────────┐
                      │                                           │
                      ▼ (Documento con imágenes)                  ▼ (Flujo textual puro)
        ┌───────────────────────────┐               ┌───────────────────────────┐
        │    extractor_visual.py    │               │       corrector.py        │
        │ - Extracción bitmap pypdf │               │ - Chunking jerárquico     │
        │ - Hash SHA-256 por asset  │               │ - Inferencia Ollama HTTP  │
        │ - Downscaling protect VRAM│               │ - Reintentos exponenciales│
        │ - Anclas posicionales     │               │ - Fallback automático     │
        └─────────────┬─────────────┘               └─────────────┬─────────────┘
                      │                                           │
                      └─────────────────────┬─────────────────────┘
                                            │
                                            ▼
                             ┌─────────────────────────────┐
                             │  core/pureza_documental.py  │ ◄── Poda de preámbulos/cortesías
                             │   (Filtro Zero-Chatter)     │ ◄── Aislamiento trazas <think>
                             │                             │ ◄── Poda de despedidas/firmas
                             └──────────────┬──────────────┘
                                            │
                                            ▼
                             ┌─────────────────────────────┐
                             │       reconstructor.py      │ ──► Generación fiel (.docx, .odt, .rtf,
                             │                             │     .csv, .html, .txt, .md, .pdf)
                             └──────────────┬──────────────┘
                                            │
                                            ▼
                             ┌─────────────────────────────┐
                             │      procesador_lote.py     │ ──► [Directorio Salida] (Ledger JSON)
                             │       / servidor_api.py     │ ──► [Directorio Errores] (shutil.copy2)
                             │                             │ ──► [Descarga Web / Visor Interactivo]
                             └─────────────────────────────┘
```

---

## 3. Desglose Modular de Componentes

### 3.1. `config.py` (Configuración Inmutable)
- **Responsabilidad:** Define la clase `Config` con `@dataclass(frozen=True)`. Centraliza rutas relativas/absolutas, parámetros de inferencia (`temperature=0.2`, `top_p=0.9`, `num_ctx=4096`), tamaño de chunk, extensiones soportadas y modelos primario y fallback.

### 3.2. `explorador.py` (Escaneo Seguro y Sniffer)
- **Responsabilidad:** Escaneo de archivos excluyendo temporales de Office (`~$*`) y archivos ocultos (`.*`). Valida la contención dentro del directorio de trabajo mediante `is_relative_to()`, descarta binarios ejecutables Windows (`MZ`/`PE`) y Linux (`\x7FELF`), y limita el tamaño por archivo a 50 MB.

### 3.3. `conversor.py` (Ingestión Multiformato y Anti-Mojibake)
- **Responsabilidad:** Normalización universal a Markdown. Incorpora `_leer_texto_auto_encoding` en cascada (UTF-8 estricto -> CP1252 -> Latin-1 -> UTF-8 replace). Despacha a librerías especializadas (`MarkItDown`, `odfpy`, `striprtf`, `csv.Sniffer`, `xlrd`).

### 3.4. `corrector.py` (Chunking Jerárquico e Inferencia Resiliente)
- **Responsabilidad:** Chunking jerárquico dividiendo por párrafos dobles `\n\n`. Si un bloque excede `max_chars`, se subdivide automáticamente por oraciones (`. `, `? `, `! `) o saltos simples (`\n`). Reintentos exponenciales con timeout de 120s y fallback transparente a modelo alternativo.

### 3.5. `core/pureza_documental.py` (Protocolo Zero-Chatter)
- **Responsabilidad:** Filtro determinista que remueve preámbulos de cortesía de LLMs, encabezados espurios, despedidas y bloques de razonamiento `<think>`, emitiendo el índice porcentual de pureza.

### 3.6. `extractor_visual.py` (Extracción Pixel-Perfect)
- **Responsabilidad:** Extracción de imágenes nativas en PDF (`pypdfium2`/`pdfplumber`) y DOCX (`python-docx`). Aplica hash SHA-256 único por activo, límite de descompresión anti-DoS (50M píxeles) y genera anclas en el Markdown.

### 3.7. `reconstructor.py` (Ensamblador Físico Fiel)
- **Responsabilidad:** Generación de archivos de salida en sus formatos nativos: `.docx` con jerarquía de títulos e imágenes, `.odt` con ODF nativo, `.rtf` con escapes Unicode, `.csv` RFC 4180, `.html` semántico y exportación a `.pdf` mediante ReportLab.

### 3.8. `core/ecc_guard.py` (Guardia Criptográfica CEO)
- **Responsabilidad:** Intercepta intentos de modificación en las zonas protegidas (`ECC/` y `ai-harness/ecc/`). Exige verificación de identidad mediante hash SHA-256 sin almacenar el nombre en texto claro en repositorios ni logs.

### 3.9. `servidor_api.py` (Gateway FastAPI y Telemetría 360°)
- **Responsabilidad:** Gateway compatible con la especificación de OpenAI (`/v1/chat/completions`) para AnythingLLM y Open WebUI. Expone endpoints de telemetría de hardware en tiempo real (`/api/telemetria/360`), visor web de documentos (`/api/ver/{nombre}`) y descarga directa (`/api/descargar/{nombre}`).

---

## 4. Matriz de Estado y Cierre de Gaps de Arquitectura

| ID | Requerimiento / Gap | Estado | Solución Implementada |
|---|---|---|---|
| **G-01** | Soporte CLI para `modelo_fallback` | ✅ CERRADO | Añadido flag `--fallback` en `procesador_lote.py`. |
| **G-02** | Detección de binarios ejecutables camuflados | ✅ CERRADO | Sniffer de Magic Bytes `MZ` y `ELF` en `explorador.py`. |
| **G-03** | Límite preventivo de tamaño por documento | ✅ CERRADO | Guardia `max_tamano_bytes` (50 MB) en `explorador.py`. |
| **G-04** | Prevención de mojibakes en archivos ANSI/CP1252 | ✅ CERRADO | Decodificación en cascada UTF-8 -> CP1252 -> Latin-1 en `conversor.py`. |
| **G-05** | Chunking de párrafos gigantes continuos | ✅ CERRADO | Subdivisión jerárquica por oraciones en `corrector.py`. |
| **G-06** | Soporte de formatos extendidos (.odt, .rtf, .csv) | ✅ CERRADO | Integración completa en `conversor.py` y `reconstructor.py`. |
| **G-07** | Compatibilidad multiplataforma simétrica | ✅ CERRADO | Scripts duales `.ps1` y `.sh` + suite `test_compatibilidad_linux.py`. |
| **G-08** | Monitoreo y Telemetría 360° en tiempo real | ✅ CERRADO | Endpoint `/api/telemetria/360` con lectura de GPU, VRAM, RAM y CPU. |
| **G-09** | Blindaje criptográfico del arnés /ECC | ✅ CERRADO | Módulo `core/ecc_guard.py` con verificación SHA-256 del CEO. |
| **G-10** | Cobertura TDD automatizada | ✅ CERRADO | Suite integral de 176 pruebas automatizadas (100% verde). |

---

## 5. Matriz Dual de Hardware: Producción Workstation vs MVP Local

| Atributo de Hardware | Entorno de Desarrollo y MVP Local | Servidor Workstation de Producción |
|---|---|---|
| **GPU Primaria** | **NVIDIA GeForce GTX 1650** | **PNY NVIDIA Quadro RTX PRO 4000 24 GB** |
| **P/N Fabricante** | OEM estándar | `VCNRTXPRO4000B-PB` (PNY) |
| **Arquitectura GPU** | Turing (TU117, SM 7.5) | **NVIDIA Blackwell** (Tensor Cores 5.ª Gen, FP4/FP8) |
| **VRAM y Tipo** | 4 GB GDDR5/GDDR6 (~3.2 GB libres) | **24 GB GDDR7 con soporte ECC** |
| **Núcleos CUDA** | 896 núcleos | **8.960 núcleos CUDA®** |
| **Consumo Máximo (TDP)** | 75 W | 140 W (eficiencia energética industrial) |
| **Conectividad Video** | HDMI / DVI | 4x DisplayPort 2.1 \| NVIDIA RTX PRO SYNC |
| **CPU del Sistema** | Host x86_64 estándar | **Intel Core i9-14900** (24 núcleos / 32 hilos, hasta 5.8 GHz) |
| **Memoria RAM Sistema** | 16 – 32 GB RAM | **128 GB DDR5** (offload sin cuellos de botella) |
| **Contexto Útil (`num_ctx`)**| 2.048 – 4.096 tokens | **32.768 – 65.536 tokens** (FlashAttention-2 + KV-q8) |
| **Modelos Textuales** | `qwen2.5:3b`, `qwen2.5:1.5b` | `qwen2.5-coder:32b`, `deepseek-r1:32b`, `qwen2.5:14b` |
| **Modelos Visuales (VLM)** | `qwen2.5vl:3b` (Q4_K_M) | `qwen2.5vl:7b` / `qwen2.5vl:32b`, fallback `gemma3:4b` |
| **Throughput Estimado** | 150 – 300 docs/hora (secuencial) | **1.500 – 4.000 docs/hora** (Two-Phase Pipeline) |
