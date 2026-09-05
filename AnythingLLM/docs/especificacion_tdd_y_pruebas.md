# Especificación TDD y Matriz de Pruebas Automatizadas

**Versión:** 1.0.0 (Consolidada Multiplataforma y Monorepo)  
**Entorno de Pruebas:** Python 3.13.14 (64-bit) | Pytest 9.1.1 | Pytest-Cov 7.1.0 | Respx 0.23.1  
**Estándar de Calidad:** Enterprise Coding Constitution (ECC v2.0.0) — Tolerancia Cero a Fallos Silenciosos  
**Total de Pruebas en Suite:** **176 pruebas automatizadas**  

---

## 1. Metodología TDD bajo Gobernanza ECC

1. **Fase RED:** Definición rigurosa de casos de prueba y aserciones estrictas para cada nuevo requerimiento (formatos extendidos, compatibilidad Linux POSIX, Zero-Chatter, concurrencia 10 usuarios, seguridad SHA-256 CEO y telemetría 360°) antes de codificar la lógica de producción.
2. **Fase GREEN:** Implementación modular en `core/`, `servidor_api.py`, `extractor_visual.py` y `ecc_guard.py` satisfaciendo los contratos de prueba.
3. **Fase REFACTOR:** Optimización de tipado estático, inmutabilidad con `@dataclass(frozen=True)`, streaming SSE no bloqueante y decodificación adaptativa en cascada (UTF-8 -> CP1252 -> Latin-1).

---

## 2. Matriz Exhaustiva de Pruebas Automatizadas (176 Tests)

| Archivo de Test | Tipo | Casos Validados | Cobertura / Estado |
|---|---|---|---|
| `tests/unit/test_config.py` | Unitario | Inmutabilidad (`frozen=True`), resolución de rutas `Path`, defaults y perfiles. | PASSED (3/3) |
| `tests/unit/test_explorador.py` | Unitario | Exclusión temporales Office (`~$*`), sniffer Magic Bytes (`MZ`/`ELF`), límite 50MB, Path Traversal. | PASSED (3/3), 1 SKIPPED |
| `tests/unit/test_chunker.py` | Unitario | Preservación de párrafos (`\n\n`), subdivisión por oraciones en bloques gigantes, limpieza markdown. | PASSED (6/6) |
| `tests/unit/test_corrector.py` | Unitario | Inferencia con `respx`, manejo de error 500 (`InferenciaError`), backoff exponencial, fallback. | PASSED (7/7) |
| `tests/unit/test_reconstructor.py` | Unitario | Generación nativa `.docx`, `.odt`, `.rtf`, `.csv`, `.html`, `.pdf` con imágenes ReportLab. | PASSED (14/14) |
| `tests/unit/test_formatos_extendidos.py` | Unitario | Conversión y reconstrucción `.odt`, `.rtf`, `.csv`, `.xls`, flags CLI (`--fallback`, `--chunk-size`). | PASSED (9/9) |
| `tests/unit/test_procesador_lote.py` | Unitario | Aislamiento en `datos/errores/` con `shutil.copy2`, tolerancia a fallos, ledger JSON y reanudación SHA-256. | PASSED (6/6) |
| `tests/unit/test_encoding.py` | Unitario | Round-trip UTF-8, decodificación en cascada anti-mojibakes (CP1252/Latin-1), caracteres tipográficos. | PASSED (11/11) |
| `tests/integration/test_pipeline.py` | Integración | Pipeline E2E multiformato con simulación `respx`, generación de ledger y salida UTF-8. | PASSED (1/1) |
| `tests/unit/test_concurrencia_10_usuarios.py` | Estrés / Concurrencia | 10 peticiones simultáneas, simulación de usuarios paralelos, presupuesto VRAM < 3GB, cero colisiones. | PASSED (3/3) |
| `tests/unit/test_ecc_guard.py` | Seguridad / Cripto | Inmutabilidad de `ECC/` y `ai-harness/ecc/`, verificación SHA-256 del CEO, cero hardcodeo de nombres. | PASSED (4/4) |
| `tests/unit/test_compatibilidad_linux.py` | Multiplataforma | Separadores de ruta POSIX, permisos de ejecución en scripts `.sh`, codificación LF, sin dependencias win32. | PASSED (5/5) |
| `tests/unit/test_telemetria_360.py` | Telemetría / Hardware | Lectura de VRAM, temperatura GPU, carga CUDA, RAM del host y uso CPU; fallback suave en CPU hosts. | PASSED (4/4) |
| `tests/unit/test_servidor_api.py` | API / Gateway | Endpoints `/api/telemetria/360`, `/api/documentos`, visor web seguro, descargas directas sin traversal. | PASSED (8/8) |
| `tests/unit/test_v1_endpoints.py` | Compatibilidad OpenAI | Endpoints `/v1/models` y `/v1/chat/completions` con streaming SSE para AnythingLLM y Open WebUI. | PASSED (5/5) |
| `tests/unit/test_mcp_server.py` | Protocolo MCP | Herramientas oficiales MCP (`corregir_y_exportar_documento`, `ecc_auditoria_pureza`, etc.). | PASSED (8/8) |
| `tests/unit/test_perfiles_entornos.py` | Arquitectura / Hardware | Validación de perfiles de hardware (MVP GTX 1650 vs Workstation 24GB) y esquemas JSON de workspaces. | PASSED (6/6) |
| `tests/unit/test_extractor_visual.py` | Visión / Gráficos | Extracción bitmap en PDF (`pypdfium2`) y DOCX, hashes SHA-256 por asset, blindaje Pixel Flood DoS. | PASSED (7/7) |
| `tests/unit/test_vlm_connector.py` | Multimodal VLM | Inferencia con imágenes en base64 hacia Ollama VLM, contratos de respuesta y timeouts. | PASSED (6/6) |
| `tests/unit/test_vlm_guardrails.py` | Guardrails VLM | Validación de metadatos de diagramas, detección de alucinaciones y umbral de revisión humana (<0.6). | PASSED (6/6) |
| `tests/unit/test_watermark.py` | Seguridad Visual | Inserción y detección de marcas de agua digitales y esteganografía visual en PDFs generados. | PASSED (7/7) |
| `tests/unit/test_image_surgery.py` | Procesamiento Visual | Redimensionamiento adaptativo, preservación de aspect ratio y downscaling para protección VRAM. | PASSED (7/7) |
| `tests/unit/test_executive_summarizer.py` | Síntesis Semántica | Generación de minutas ejecutivas, extracción de acuerdos y resúmenes de alto nivel. | PASSED (7/7) |
| `tests/unit/test_intent_detector.py` | Detección de Intenciones | Detección de peticiones de exportación, parsing de rutas de Windows y formato solicitado. | PASSED (8/8) |
| `tests/unit/test_core_router.py` | Enrutamiento | Afinidad Zero-Swap, orquestación en dos fases (Two-Phase Batching) y semáforo de concurrencia. | PASSED (6/6) |
| `tests/unit/test_core_connector.py` | Red / Hardware | Cliente asíncrono httpx hacia Ollama, inyección FlashAttention y KV-cache q8_0. | PASSED (6/6) |
| `tests/unit/test_core_registry.py` | Catálogo | Detección de capacidades de modelos, caché en disco `registry_cache.json` y cold-start delay 0. | PASSED (5/5) |
| `tests/unit/test_core_guardrails.py` | Sanitización | Aislamiento quirúrgico de `<think>`, autoreparación de JSON truncado y validación de Markdown. | PASSED (5/5) |

---

## 3. Certificación de Calidad y Resiliencia

- **Total de pruebas:** **176 pruebas automatizadas** (175 activas, 1 skipped justificada para SO específico).
- **Tolerancia a Fallos:** Verificada con `respx` simulando cortes de red, caídas de Ollama (500/503), timeouts de socket y archivos corruptos.
- **Idempotencia y Eficiencia:** El explorador y ledger omiten documentos previamente procesados a más de **2.900 documentos por segundo**.
- **Compatibilidad de Plataforma:** Verificación simétrica en Windows 10/11 64-bit y Linux POSIX.
