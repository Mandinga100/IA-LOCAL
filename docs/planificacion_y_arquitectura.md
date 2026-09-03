# Planificación y Arquitectura Técnica del Sistema

**Versión:** 0.3.0 (Consolidada con Formatos Extendidos y Auditoría Forense)  
**Entorno Operativo:** Windows 10 Pro 64-bit | PowerShell 5.1 / 7+ | Python 3.13  
**Estándar de Gobernanza:** Enterprise Coding Constitution (ECC v2.0.0)

---

## 1. Principios de Arquitectura bajo Gobernanza ECC

La arquitectura del sistema responde a los principios clave del harness **Everything Claude Code (ECC v2.0.0)**:
- **Agent-First:** Especialización funcional en agentes de diseño, seguridad, rendimiento y calidad.
- **Inmutabilidad de Datos:** Uso sistemático de `@dataclass(frozen=True)` para todas las estructuras compartidas (`DocumentoTarea`, `ChunkTexto`, `Config`).
- **Tolerancia Cero a Fallos Silenciosos (`silent-failure-hunter`):** Prohibición terminante de bloques `except: pass` o retornos de texto vacío sin registrar excepción ni aislar el documento problemático.
- **Seguridad y Validación en Fronteras (`security-reviewer`):** Blindaje contra *Path Traversal* mediante `Path.resolve().is_relative_to()`, Sniffer de firmas ejecutables (`MZ`, `ELF`) y límite preventivo de tamaño por documento.
- **Resiliencia Lingüística:** Decodificación adaptativa en cascada UTF-8 -> CP1252 -> Latin-1 para aniquilar cualquier posibilidad de mojibakes.

---

## 2. Diagrama de Flujo del Pipeline de Procesamiento

```
                 [Directorio de Entrada]
                            │
                            ▼
             ┌─────────────────────────────┐
             │       explorador.py         │ ◄── Omitir temporales Office (~$*)
             │  (Hash SHA-256 + Tarea)     │ ◄── Guardia Path Traversal (is_relative_to)
             │                             │ ◄── Sniffer Magic Bytes (MZ / ELF)
             │                             │ ◄── Guardia de tamaño máximo (50 MB)
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
                            ▼
             ┌─────────────────────────────┐
             │        corrector.py         │ ◄── Chunking semántico jerárquico (\n\n / . )
             │   (Inferencia Ollama HTTP)  │ ◄── Prompts especializados (prompts.json)
             │                             │ ◄── Reintentos exponenciales + Fallback
             └──────────────┬──────────────┘
                            │
                            ▼
             ┌─────────────────────────────┐
             │       reconstructor.py      │ ──► Generación de .docx, .odt, .rtf, .csv,
             │                             │     .md, .txt, .html y exportación .pdf
             └──────────────┬──────────────┘
                            │
                            ▼
             ┌─────────────────────────────┐
             │      procesador_lote.py     │ ──► [Directorio de Salida] (Ledger JSON)
             │                             │ ──► [Directorio de Errores] (shutil.copy2)
             └─────────────────────────────┘
```

---

## 3. Desglose Modular de Scripts

### 3.1. `config.py` (Configuración Inmutable)
- **Función:** Define la clase `Config` con decorador `frozen=True`. Centraliza rutas relativas/absolutas, credenciales locales, URL de Ollama, modelo activo, hiperparámetros (`temperature=0.2`, `top_p=0.9`, `num_ctx=4096`), tamaño de chunk, extensiones soportadas y `modelo_fallback`.
- **Extensiones Formalizadas:** `.pdf`, `.docx`, `.doc`, `.odt`, `.rtf`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.csv`, `.html`, `.txt`, `.md`.

### 3.2. `explorador.py` (Escaneo Seguro y Sniffer)
- **Seguridad en Fronteras:**
  - Filtrado de temporales Office (`~$*`) y archivos ocultos (`.*`).
  - Guardia contra Path Traversal con `Path.resolve().is_relative_to()`.
  - Sniffer de Magic Bytes: descarta binarios ejecutables Windows (`MZ` / `PE`) y Linux (`\x7FELF`).
  - Límite máximo de tamaño por documento (50 MB por defecto).

### 3.3. `conversor.py` (Ingestión Multiformato y Anti-Mojibake)
- **Decodificación Adaptativa:** Implementa `_leer_texto_auto_encoding` que intenta UTF-8 estricto -> CP1252 -> Latin-1 -> UTF-8 replace.
- **Motores Especializados:**
  - `MarkItDown`: `.docx`, `.pptx`, `.xlsx`, `.pdf`, `.html`.
  - `odfpy`: `.odt` (extracción de títulos, párrafos y listas viñeteadas).
  - `striprtf`: `.rtf` (decodificación directa sin pérdida).
  - `csv.Sniffer`: `.csv` (conversión automática a tablas Markdown `| Col1 | Col2 |`).
  - `xlrd`: `.xls` (volcado de celdas a Markdown tabular).

### 3.4. `corrector.py` (Chunking Jerárquico e Inferencia)
- **Chunking Jerárquico:** Divide por párrafos dobles `\n\n`. Si un párrafo individual supera `max_chars`, se subdivide automáticamente por oraciones (`. `, `? `, `! `) o saltos simples (`\n`).
- **Resiliencia:** Reintentos exponenciales (2s, 4s, 8s) con timeout de 120s y fallback automático a modelo alternativo (`modelo_fallback`).
- **Gestión de Recursos:** Soporte nativo para context manager `with CorrectorOllama() as corrector:` y método `close()` para liberar sockets HTTP.
- **Sanitización LLM:** Desempaqueta wrappers Markdown redundantes (`_limpiar_respuesta_llm`).

### 3.5. `reconstructor.py` (Reconstrucción Universal Fiel)
- **`.docx`:** Maquetación con títulos `H1`, `H2`, `H3`, párrafos y viñetas mediante `python-docx`.
- **`.odt`:** Reconstrucción nativa OpenDocumentText con jerarquía de encabezados y listas.
- **`.rtf`:** Formateo RTF con escapes Unicode (`\uN?`).
- **`.csv`:** Reconstrucción de tablas Markdown a valores separados por comas estándar RFC 4180.
- **`.html`:** Renderizado HTML5 con codificación UTF-8 estricta y estilos limpios.
- **Binarios Complejos (`.pdf`, `.xlsx`, etc.):** Exportación auditable con sufijo `.corregido.md`.

### 3.6. `procesador_lote.py` (Orquestador y Ledger)
- **Ledger de Idempotencia:** `historial_procesados.json` con hash SHA-256 de cada archivo. Re-ejecución instantánea.
- **Aislamiento Seguro:** Cuarentena automática con `shutil.copy2` en `datos/errores/` ante cualquier anomalía sin abortar el lote.
- **Interfaz CLI:** Argumentos `--origen`, `--destino`, `--tipo`, `--modelo`, `--fallback`, `--chunk-size`, `--url`.

---

## 4. Matriz de Estado y Cierre de Gaps

| ID | Requerimiento / Gap | Estado | Solución Implementada |
|---|---|---|---|
| **G-01** | Soporte CLI para `modelo_fallback` | ✅ CERRADO | Añadido flag `--fallback` en `procesador_lote.py`. |
| **G-02** | Detección de binarios ejecutables camuflados | ✅ CERRADO | Sniffer de Magic Bytes `MZ` y `ELF` en `explorador.py`. |
| **G-03** | Límite preventivo de tamaño por documento | ✅ CERRADO | Guardia `max_tamano_bytes` (50 MB) en `explorador.py`. |
| **G-04** | Prevención de mojibakes en archivos ANSI/CP1252 | ✅ CERRADO | Decodificación en cascada UTF-8 -> CP1252 -> Latin-1 en `conversor.py`. |
| **G-05** | Chunking de párrafos gigantes continuos | ✅ CERRADO | Subdivisión jerárquica por oraciones en `corrector.py`. |
| **G-06** | Soporte de formatos extendidos (.odt, .rtf, .csv) | ✅ CERRADO | Integración completa en `conversor.py` y `reconstructor.py`. |
| **G-07** | Política de backup único consolidado | ✅ CERRADO | Script `generar_backup.py` mantiene 1 solo backup optimizado. |
| **G-08** | Cobertura TDD certificada | ✅ CERRADO | 100 tests (99 passed, 1 skipped), cobertura integral del pipeline. |

---

## 5. Matriz Dual de Hardware: Producción Workstation vs MVP Local

El sistema desacopla la arquitectura entre el entorno de desarrollo/pruebas locales y la estación de trabajo dedicada a producción continua:

| Atributo de Hardware | Entorno de Desarrollo y MVP Local | Servidor Workstation de Producción |
|---|---|---|
| **GPU Primaria** | **NVIDIA GeForce GTX 1650** | **PNY NVIDIA Quadro RTX PRO 4000 24 GB** |
| **P/N Fabricante** | OEM estándar | `VCNRTXPRO4000B-PB` (PNY) |
| **Arquitectura GPU** | Turing (TU117, SM 7.5) | **NVIDIA Blackwell** (Tensor Cores 5.ª Gen, FP4/FP8) |
| **VRAM y Tipo** | 4 GB GDDR5/GDDR6 (~3.2 GB libres) | **24 GB GDDR7 con soporte ECC** |
| **Núcleos CUDA** | 896 núcleos | **8.960 núcleos CUDA®** |
| **Consumo Máximo (TDP)** | 75 W | 140 W (eficiencia energética excepcional) |
| **Sincronización / Video** | HDMI / DVI | 4x DisplayPort 2.1 \| NVIDIA RTX PRO SYNC |
| **CPU del Sistema** | Host local estándar (x86_64) | **Intel Core i9-14900** (24 núcleos / 32 hilos, hasta 5.8 GHz) |
| **Memoria RAM Sistema** | 16 – 32 GB RAM | **128 GB DDR5** (offload masivo sin cuello de botella) |
| **Contexto Útil (`num_ctx`)**| 2.048 – 4.096 tokens | **32.768 – 65.536 tokens** (FlashAttention-2 + KV-q8) |
| **Modelos Textuales** | `qwen2.5:3b`, `qwen2.5:1.5b` | `qwen2.5-coder:32b`, `deepseek-r1:32b`, `qwen2.5:14b` |
| **Modelos Visuales (VLM)** | `qwen2.5vl:3b` (Q4_K_M) | `qwen2.5vl:7b` / `qwen2.5vl:32b`, fallback `gemma3:4b` |
| **Throughput Estimado** | 150 – 300 docs/hora (secuencial) | **1.500 – 4.000 docs/hora** (Two-Phase Pipeline) |

---

## 6. Matriz de Gaps de Extensión Visual y Multimodal (VLM)

| ID | Brecha / Gap | Estado | Solución Técnica Implementada |
|---|---|---|---|
| **V-01** | Extractor seguro de imágenes embebidas en DOCX | ✅ CERRADO | Módulo `extractor_visual.py` con extracción binaria directa. |
| **V-02** | Hash SHA-256 independiente por imagen | ✅ CERRADO | Hashing SHA-256 por asset en `extractor_visual.py`. |
| **V-03** | Contrato Pydantic formal para metadatos visuales | ✅ CERRADO | Modelos `MetadatosVisuales`, `ElementoVisual`, `RelacionVisual`. |
| **V-04** | Mitigación de alucinaciones en diagramas | ✅ CERRADO | Prompt VLM negativo estricto y campo `requires_human_review`. |
| **V-05** | Métrica de confianza y umbral de revisión | ✅ CERRADO | Scoring `overall_confidence` con flag para revisión si es < 0.6. |
| **V-06** | Prevención de duplicados visuales por hash | ✅ CERRADO | Normalización y huella binaria persistida. |
| **V-07** | Protección contra Visual Prompt Injection | ✅ CERRADO | Aislamiento del texto de la imagen como datos no confiables. |
| **V-08** | Cadena de fallback multimodal | ✅ CERRADO | Perfil `doc_vlm` con fallback `qwen2.5vl:7b` -> `gemma3:4b` -> `3b`. |
| **V-09** | Fixtures de prueba con imágenes en español | ✅ CERRADO | Tests unitarios sintéticos en `test_extractor_visual.py`. |
| **V-10** | Reconstrucción visual en Markdown estructurado | ✅ CERRADO | Inyección de bloques `> [IMAGEN: ...]` semánticos legibles. |
| **V-11** | Gestión de ciclo de vida de assets | ✅ CERRADO | Organización jerárquica `assets/{hash_doc[:8]}/`. |
| **V-12** | Flujo de advertencias y revisión humana | ✅ CERRADO | Captura de `warnings` del modelo visual en el contrato. |
| **V-13** | **Blindaje Decompression Bomb (Pixel Flood DoS)** | ✅ CERRADO | Límite estricto `PIL.Image.MAX_IMAGE_PIXELS = 50_000_000`. |
| **V-14** | **Downscaling adaptativo para protección VRAM** | ✅ CERRADO | Reducción a max 1280px en el lado mayor antes de inferencia. |
| **V-15** | **Path Traversal en directorio assets** | ✅ CERRADO | Validación de contención con `is_relative_to()`. |
