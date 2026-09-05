# Contexto del Proyecto: Plataforma IA Local

**Versión:** 1.0.0 (Consolidada Multiplataforma y Monorepo)  
**Entornos Operativos:** Windows 10 / 11 Pro 64-bit (PowerShell 5.1 / 7+) y GNU/Linux (Ubuntu 22.04/24.04 LTS, Debian 12, Fedora)  
**Gobernanza:** Enterprise Coding Constitution (ECC v2.0.0) con Guardia Criptográfica SHA-256

---

## 1. Visión y Propósito
El objetivo primordial del proyecto es desarrollar e implantar una **Plataforma Integral y Autónoma de Procesamiento, Corrección y Gestión de Documentos con Inteligencia Artificial 100% Local**, desacoplada de la nube y de terceros.

El sistema procesa de forma masiva y por lotes documentos locales en múltiples formatos ofimáticos y técnicos (`.pdf`, `.docx`, `.doc`, `.odt`, `.rtf`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.csv`, `.html`, `.txt`, `.md`), los normaliza a Markdown estructurado con decodificación adaptativa anti-mojibakes, aplica corrección gramatical, ortográfica y estilística con **Modelos de Lenguaje Locales (LLM vía Ollama)**, preserva elementos visuales en calidad pixel-perfect, aplica sanitización estricta **Zero-Chatter** (Pureza Documental) y permite la interacción multiusuario concurrente a través de la integración nativa de **AnythingLLM**.

---

## 2. Restricciones Críticas del Sistema

1. **Privacidad y Soberanía de Datos (100% Offline):**
   - Cero dependencias de APIs en la nube (sin OpenAI, sin Anthropic, sin servicios externos de telemetría).
   - Toda inferencia se realiza exclusivamente en el hardware local (GPU/CPU) del host mediante la API HTTP de Ollama (`http://localhost:11434`).

2. **Adaptabilidad a Hardware Restringido (Desde GTX 1650 4 GB hasta Blackwell 24 GB):**
   - **MVP Local (4 GB VRAM):** Consumo acotado a un máximo de **2.350 MB** con modelos 3B cuantizados (`qwen2.5:3b`, `qwen2.5-coder:3b`), reservando más de 850 MB libres para el sistema operativo Windows (DWM).
   - **Estaciones de Producción (24 GB VRAM):** Capacidad para albergar modelos de 14B a 32B (`qwen2.5-coder:32b`, `deepseek-r1:32b`, `qwen2.5vl:7b`) con contextos extendidos de 32K a 65K tokens, FlashAttention y KV-cache cuantizado en `q8_0`.

3. **Arquitectura Multiplataforma Simétrica (Windows 10 64-bit y Linux):**
   - Compatibilidad total nativa en Windows PowerShell (5.1 y Core 7+) mediante scripts `.ps1`.
   - Compatibilidad simétrica para entornos GNU/Linux y servidores mediante scripts Bash equivalentes (`.sh`).
   - Normalización de rutas con `pathlib.Path` para eliminar fallos por separadores (`\` vs `/`).
   - Decodificación adaptativa multicapa (UTF-8 -> CP1252 -> Latin-1) para erradicar mojibakes en consolas Windows (`CP1252`/`OEM 850`) y terminales Linux UTF-8.

4. **Chunking Semántico Jerárquico y Zero-Chatter:**
   - División segura de textos respetando párrafos (`\n\n`) y oraciones (`. `, `? `, `! `) evitando saturación del contexto (`num_ctx`).
   - Esterilización determinista de metatexto, cortesías, despedidas y bloques de razonamiento `<think>` para emitir documentos listos para publicación.

5. **Gobernanza Criptográfica Inmutable (/ECC):**
   - El arnés metodológico (`ECC/`) y el arnés operativo de producción (`ai-harness/ecc/`) están sellados y protegidos criptográficamente mediante verificación unidireccional SHA-256 reservada exclusivamente al CEO.

---

## 3. Estructura de la Solución Consolidada (Monorepo)

La plataforma organiza sus componentes funcionales de manera desacoplada:

```
Plataforma IA local/
└── AnythingLLM/
    ├── Base/                 # Plataforma central en Python (FastAPI, Pipeline, CLI, Tests)
    │   ├── core/             # Núcleo de 5 capas (conector, registro, perfiles, router, guardrails)
    │   ├── datos/            # Directorios de entrada, salida, activos y errores
    │   ├── frontend/         # Dashboard Web 360° interactivo con 5 pestañas
    │   ├── MVP/              # Documentación y configuraciones del entorno MVP (GTX 1650 4GB)
    │   ├── produccion/       # Configuraciones y scripts para estación de 24 GB VRAM
    │   ├── scripts/          # Automatizaciones duales (.ps1 y .sh)
    │   ├── tests/            # Suite de pruebas automatizadas TDD (176 tests)
    │   ├── conversor.py      # Motor de conversión multiformato a Markdown
    │   ├── corrector.py      # Motor de inferencia y chunking con Ollama
    │   ├── extractor_visual.py # Extracción y anclaje pixel-perfect de imágenes
    │   ├── mcp_server.py     # Servidor Model Context Protocol oficial
    │   ├── procesador_lote.py# Orquestador CLI de procesamiento masivo
    │   ├── reconstructor.py  # Ensamblador de documentos nativos
    │   └── servidor_api.py   # Gateway FastAPI compatible con OpenAI (/v1) y Telemetría
    ├── ECC/                  # Arnés metodológico interno ECC v2.0.0 protegido
    ├── ai-harness/           # Arnés operativo de producción con 4 workspaces AnythingLLM
    ├── docs/                 # Base de documentación técnica centralizada y actualizada
    └── [AnythingLLM Core]    # Código fuente de AnythingLLM (Docker, frontend, server, collector)
```

---

## 4. Stack Tecnológico Consolidado

| Capa / Componente | Tecnología Seleccionada | Justificación Técnica |
|---|---|---|
| **Sistemas Operativos** | Windows 10/11 Pro 64-bit / GNU/Linux | Soporte nativo para workstation de desarrollo y servidores de producción. |
| **Runtime & Gestor** | Python 3.13.14 64-bit + `uv` 0.7.8 | Resolución ultra-rápida de dependencias y aislamiento en `.venv`. |
| **Motor de Inferencia** | Ollama (`http://localhost:11434`) | Orquestador local de LLMs optimizado para CUDA en Windows y Linux. |
| **GUI & Multi-Usuario** | AnythingLLM (Docker Desktop / Desktop GUI) | Interfaz web multiusuario con aislamiento de roles, RAG y soporte MCP. |
| **Gateway & API REST** | FastAPI + Uvicorn + Server-Sent Events | Endpoints compatibles con OpenAI `/v1/chat/completions` y streaming SSE. |
| **Dashboard 360°** | HTML5 Semántico + CSS Grid/Flex + Vanilla JS | Consola visual con 5 pestañas, telemetría hardware en vivo y visor de docs. |
| **Modelos Homologados** | `qwen2.5:3b`, `qwen2.5-coder:3b`, `qwen2.5-coder:32b`, `deepseek-r1:14b/32b`, `qwen2.5vl:7b` | Máxima fidelidad sintáctica en español, código y comprensión multimodal. |
| **Conversión a Markdown** | `MarkItDown`, `odfpy`, `striprtf`, `xlrd`, `csv.Sniffer` | Ingestión universal de DOCX, ODT, RTF, CSV, XLS, PPTX, HTML, PDF, TXT y MD. |
| **Reconstrucción Nativa** | `python-docx`, `odfpy`, `striprtf`, `reportlab`, `csv.writer` | Ensamblado fiel en formatos ofimáticos nativos y PDF con estilos ejecutivos. |
| **Seguridad Criptográfica**| SHA-256 Unidireccional (`core/ecc_guard.py`) | Protección inmutable de arneses con desafío de identidad del CEO sin hardcodeo. |
| **Testing & Calidad** | `pytest`, `pytest-cov`, `respx` | Cobertura TDD exhaustiva con 176 tests automatizados (100% verde). |

---

## 5. Perfiles de Hardware y Dimensionamiento

### Perfil 1: Entorno de Desarrollo y MVP Local (NVIDIA GeForce GTX 1650 4 GB)
- **Propósito:** Desarrollo activo, suite de pruebas TDD (176 tests), validación de pipelines y piloto offline.
- **GPU:** NVIDIA GeForce GTX 1650 (Arquitectura Turing TU117, SM 7.5, 896 núcleos CUDA, 4 GB VRAM).
- **Consumo VRAM objetivo:** 2.050 – 2.400 MB (~850 MB libres para DWM y sistema operativo).
- **Modelos Homologados:** `qwen2.5:3b`, `qwen2.5-coder:3b`, `qwen2.5:1.5b` (fallback), `qwen2.5vl:3b` (visión).
- **Ventana de Contexto (`num_ctx`):** 2.048 tokens.
- **Concurrencia:** Inferencia secuencial o con 2 slots acotados (`OLLAMA_NUM_PARALLEL=2`).

### Perfil 2: Servidor Workstation de Producción (NVIDIA Blackwell 24 GB + i9-14900 + 128 GB RAM)
- **Propósito:** Procesamiento masivo concurrente, extracción visual compleja y servicio multiusuario AnythingLLM.
- **GPU:** PNY NVIDIA Quadro RTX PRO 4000 24 GB GDDR7 con ECC (Blackwell, 140W TDP, 8.960 CUDA cores).
- **CPU & RAM:** Intel Core i9-14900 (24 núcleos, 32 hilos) + 128 GB RAM DDR5.
- **Modelos Homologados:** `qwen2.5-coder:32b` (anclado caliente en VRAM), `deepseek-r1:14b/32b`, `qwen2.5vl:7b`.
- **Ventana de Contexto (`num_ctx`):** 32.768 – 65.536 tokens con FlashAttention y KV-cache `q8_0`.
- **Throughput Estimado:** 1.500 – 4.000 documentos/hora mediante Two-Phase Batching.
