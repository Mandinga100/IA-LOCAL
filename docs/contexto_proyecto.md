# Contexto del Proyecto: Plataforma IA Local

**Versión:** 0.3.0 (Consolidada)  
**Entorno Operativo:** Windows 10 Pro 64-bit | PowerShell 5.1 / 7+ | Python 3.13  
**Gobernanza:** Enterprise Coding Constitution (ECC v2.0.0)

---

## 1. Visión y Propósito
El objetivo primordial del proyecto es desarrollar e implantar un sistema automatizado en **Python** sobre **Windows 10 64-bit** que procese de forma masiva y por lotes documentos locales de múltiples formatos (`.pdf`, `.docx`, `.doc`, `.odt`, `.rtf`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.csv`, `.html`, `.txt`, `.md`), los convierta a Markdown estructurado con decodificación adaptativa anti-mojibakes, aplique corrección ortográfica, gramatical y de estilo mediante **Modelos de Lenguaje Locales (LLM) vía Ollama**, y preserve la integridad documental y estructural de salida.

---

## 2. Restricciones Críticas del Sistema

1. **Privacidad y Soberanía de Datos (100% Local):**
   - Cero dependencias de APIs en la nube (sin OpenAI, sin Anthropic, sin servicios de telemetría externa).
   - Toda inferencia se realiza exclusivamente en la GPU/CPU local del usuario mediante la API HTTP de Ollama (`http://localhost:11434`).

2. **Adaptabilidad a Hardware Restringido (GTX 1650 4 GB VRAM hasta 24 GB VRAM):**
   - El consumo de VRAM en entornos de 4 GB no excede los **2.350 MB** utilizando modelos 3B (`qwen2.5:3b`, `qwen2.5-coder:3b`), dejando más de 850 MB libres para el sistema operativo Windows (DWM).
   - En estaciones de trabajo con 8–16 GB VRAM opera con modelos de 7B/8B (`qwen2.5:7b`, `llama3.1:8b`).

3. **Plataforma Nativa Windows 10 64-bit:**
   - Soporte total para PowerShell nativo (5.1 y Core 7+).
   - Manipulación de rutas mediante `pathlib.Path` para evitar errores de escape con backslashes (`\`).
   - Decodificación adaptativa multicapa (UTF-8 -> CP1252 -> Latin-1) para erradicar el problema endémico de mojibakes en consolas Windows (`CP1252` / `OEM 850`).

4. **Chunking Semántico Jerárquico:**
   - División segura de textos respetando límites naturales de párrafos (`\n\n`) y subdivisión automática por oraciones cuando un párrafo individual supera `max_chars`, evitando desbordamientos de contexto (`num_ctx`).

---

## 3. Stack Tecnológico Consolidado

| Capa / Componente | Tecnología Seleccionada | Justificación Técnica |
|---|---|---|
| **Sistema Operativo** | Windows 10 Pro 64-bit | Entorno del MVP local, PowerShell nativo. |
| **Runtime & Gestor** | Python 3.13.14 64-bit + `uv` 0.7.8 | Alto rendimiento, resolución de paquetes en milisegundos y aislamiento total en `.venv`. |
| **Motor de Inferencia** | Ollama (`http://localhost:11434`) | Orquestador local de LLMs optimizado para aceleración CUDA en Windows. |
| **Modelos Homologados** | `qwen2.5:3b`, `qwen2.5-coder:3b`, `qwen2.5:7b`, `llama3.1:8b` | Alta fidelidad sintáctica en español, respeto a tablas Markdown y preservación intacta de código. |
| **Conversión a Markdown** | `MarkItDown`, `odfpy`, `striprtf`, `xlrd`, `csv.Sniffer` | Ingestión universal de DOCX, ODT, RTF, CSV, XLS, PPTX, HTML, PDF, TXT y MD. |
| **Reconstrucción** | `python-docx`, `odfpy`, `striprtf`, `csv.writer`, UTF-8 | Ensamblado fiel en formatos ofimáticos nativos. |
| **Validación y Datos** | Python `@dataclass(frozen=True)` | Inmutabilidad funcional para prevenir mutaciones colaterales. |
| **Testing & Calidad** | `pytest`, `pytest-cov`, `respx` | Cobertura TDD del 92% (61 tests), simulación de inferencia sin requerir Ollama activo en CI/CD. |

---

## 4. Perfiles de Hardware y Dimensionamiento Real

### Perfil 1: Entorno de Desarrollo y MVP Local (NVIDIA GeForce GTX 1650 4 GB)
- **Propósito:** Desarrollo activo, ejecución de la suite de pruebas TDD (100 tests), validación de pipelines y pruebas piloto offline sin saturación de recursos.
- **GPU:** NVIDIA GeForce GTX 1650 (Arquitectura Turing TU117, SM 7.5, 896 núcleos CUDA).
- **VRAM Total / Libre:** 4.096 MiB (~3.269 MiB disponibles para inferencia tras reserva del DWM de Windows).
- **Consumo VRAM objetivo:** 2.050 – 2.400 MB.
- **Modelos Textuales Homologados:** `qwen2.5:3b`, `qwen2.5-coder:3b`, `qwen2.5:1.5b` (fallback ligero).
- **Modelos Visuales (VLM):** `qwen2.5vl:3b` (cuantización Q4_K_M).
- **Ventana de Contexto (`num_ctx`):** 2.048 – 4.096 tokens.
- **Tamaño de Chunk (`chunk_size`):** 1.800 – 2.500 caracteres.
- **Estrategia de Concurrencia:** Inferencia secuencial estricta (1 documento / 1 imagen a la vez).

---

### Perfil 2: Servidor Workstation de Producción (NVIDIA Blackwell 24 GB + i9-14900 + 128 GB RAM)
- **Propósito:** Procesamiento masivo concurrente por lotes, extracción semántica visual de diagramas y tablas complejas, auditoría de razonamiento profundo y serving universal para Open WebUI.
- **GPU:** **PNY NVIDIA Quadro RTX PRO 4000 24 GB GDDR7 con ECC (VCNRTXPRO4000B-PB)**:
  - **Arquitectura:** NVIDIA Blackwell (Tensor Cores de 5.ª generación, soporte nativo FP4/FP8).
  - **VRAM:** 24 GB GDDR7 con memoria ECC (corrección de errores en inferencia crítica continua).
  - **Núcleos CUDA:** 8.960 núcleos.
  - **Consumo Energético (TDP):** 140 W (máxima eficiencia energética en rack/workstation).
  - **Conectividad:** 4x DisplayPort 2.1 | Compatible con NVIDIA RTX PRO SYNC.
  - **Ancho de Banda:** GDDR7 de ultra-alta velocidad para swaps mínimos y KV-cache masivo.
- **CPU:** **Intel Core i9-14900** (24 núcleos: 8 P-Cores + 16 E-Cores, 32 hilos, hasta 5.8 GHz, 36 MB Smart Cache).
- **Memoria RAM del Sistema:** **128 GB DDR5** (capacidad para offload en RAM sin cuello de botella y procesamiento de lotes en memoria ultra-rápido).
- **Modelos Textuales en Producción:**
  - `doc_main` / `code_ui`: `qwen2.5-coder:32b` (anclado caliente en VRAM ~19.5 GB).
  - `doc_deep`: `deepseek-r1:32b` (o 14B) con extracción de `<think>` y auditoría.
  - `doc_fast`: `qwen2.5:7b` / `qwen2.5:14b`.
- **Modelos Visuales (VLM) en Producción:** `qwen2.5vl:7b` (primario), `gemma3:12b` / `qwen2.5vl:32b`, con `gemma3:4b` como fallback.
- **Ventana de Contexto (`num_ctx`):** 32.768 – 65.536 tokens (con FlashAttention y KV-cache `q8_0`).
- **Throughput Estimado:** 1.500 – 4.000 documentos/hora con orquestación en dos fases (*Two-Phase Batching*).
