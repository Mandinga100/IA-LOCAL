# Arquitectura del Núcleo de 5 Capas y Endpoints OpenAI /v1

Este documento detalla la arquitectura desacoplada de 5 capas implementada en el módulo [`core/`](../core), así como la integración con el API Gateway [`servidor_api.py`](../servidor_api.py) y la compatibilidad universal con **Open WebUI** mediante endpoints compatibles con OpenAI (`/v1`).

---

## 🏛️ Diagrama Arquitectónico

```
                                 [ Open WebUI / Cliente OpenAI ]
                                                │
                                                ▼ (HTTP OpenAI-Compatible: /v1/chat/completions)
[ Frontend Web Local ] ────────► [ API Gateway: servidor_api.py (FastAPI) ]
                                                │
                ┌───────────────────────────────┴───────────────────────────────┐
                │              NÚCLEO ORQUESTADOR (core/)                       │
                │                                                               │
                │  [Capa 3: profiles.py] ──► Perfiles Lógicos & Contratos       │
                │  [Capa 4: router.py]   ──► Afinidad Zero-Swap & Two-Phase     │
                │  [Capa 2: registry.py] ──► Catálogo Canónico & Hash Cache     │
                │  [Capa 5: guardrails.py] ──► Extracción <think>, JSON & VLM   │
                │  [Capa 1: connector.py]──► Ollama Multimodal (FlashAttn/KV)   │
                └───────────────────────────────┬───────────────────────────────┘
                                                │ (HTTP Asíncrono / JSON)
                                        [ Ollama Local ]
                                                │
                        ┌───────────────────────┴───────────────────────┐
                        ▼                                               ▼
         [ WORKSTATION PRODUCCIÓN ]                          [ ENTORNO MVP LOCAL ]
       PNY Quadro RTX PRO 4000 24GB                     NVIDIA GeForce GTX 1650 4GB
      (NVIDIA Blackwell, GDDR7 ECC, 140W)                   (Turing SM 7.5, 896 CUDA)
      Intel Core i9-14900 | 128 GB RAM                      Contexto: 2K-4K | Q4_K_M
      Contexto: 32K-65K | FP8/KV-q8                         Modelos: 1.5B - 3B
      Modelos: 7B - 32B (Coder / VLM)
```

---

## 🧩 Descripción Detallada de las 5 Capas

### Capa 1: Conector Hardware-Aware (`core/connector.py`)
- **Responsabilidad:** Cliente asíncrono sobre `httpx.AsyncClient` optimizado para comunicarse con el daemon local de Ollama (`http://localhost:11434`), con soporte de payloads de texto y multimodales (`images: [base64_str]`).
- **Aceleración en Producción (Blackwell 24 GB GDDR7 ECC):**
  - Inyección de `flash_attn: true` en el runner llama.cpp.
  - Cuantización de KV-Cache (`kv_cache_type: q8_0`), reduciendo el consumo de VRAM en contextos masivos (32K/65K) en más de un 60% sin pérdida de precisión.
- **Modo Seguro en MVP Local (GTX 1650 4 GB):**
  - Delimitación estricta de `num_ctx: 2048/4096` y cuantización compacta para no superar el techo de 2.4 GB de VRAM útil.
- **Métodos expuestos:**
  - `generate()`: Inferencia no-streaming con soporte multimodal (`images`).
  - `chat()`: Diálogo por turnos no-streaming con mensajes estructurados.
  - `chat_stream()`: Generador asíncrono para streaming SSE chunk a chunk.
  - `list_models()`, `show_model()`, `check_health()`.

### Capa 2: Registro y Catálogo Canónico (`core/registry.py`)
- **Responsabilidad:** Mapeo de capacidades y metadatos de los modelos instalados.
- **Catálogo Canónico de Referencia:** Base de conocimiento estática sobre arquitecturas `qwen2.5-coder`, `qwen2.5`, `qwen2.5vl`, `gemma3`, `llama3.2-vision`, `deepseek-r1`, `llama3.1`, deduciendo flags de herramientas, JSON mode, visión multimodal (`supports_vision`) y ventanas nativas.
- **Caché Atómico Inmutable (`datos/registry_cache.json`):**
  - Elimina retardos de arranque (cold-start delay).
  - Lectura instantánea en memoria al iniciar la aplicación.
  - Actualización dinámica en segundo plano en el ciclo de vida `lifespan` de FastAPI.

### Capa 3: Perfiles Lógicos de Tarea (`core/profiles.py`)
- **Responsabilidad:** Desacoplar el código de nombres fijos de modelos mediante la abstracción `TaskProfile` (`@dataclass(frozen=True)`).
- **Matriz Operativa por Entorno (Producción vs MVP):**

| Perfil Lógico | Modelo Producción (Blackwell 24GB) | Modelo MVP (GTX 1650 4GB) | Contexto Prod | Contexto MVP | Rol Operativo |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **`doc_fast`** | `qwen2.5:7b` / `qwen2.5:14b` | `qwen2.5:3b` (Q4) | 32,768 | 2,048 | Ingesta masiva, OCR repair, clasificación |
| **`doc_main`** | `qwen2.5-coder:32b` | `qwen2.5:3b` | 32,768 | 2,048 | Síntesis, tablas, redacción técnica |
| **`doc_deep`** | `deepseek-r1:32b` (o 14B) | `deepseek-r1:1.5b` / `qwen:3b` | 65,536 | 2,048 | Auditoría, conciliación de fuentes, lógica |
| **`doc_vlm`** | `qwen2.5vl:7b` (fallback: `gemma3:4b`) | `qwen2.5vl:3b` (Q4) | 8,192 | 2,048 | Análisis visual de diagramas, tablas y layouts |
| **`chat_ui`** | `qwen2.5-coder:32b` | `qwen2.5:3b` | 16,384 | 2,048 | Open WebUI, diálogo técnico interactivo |
| **`code_ui`** | `qwen2.5-coder:32b` | `qwen2.5-coder:3b` | 32,768 | 2,048 | Refactorización, scripts, programación |

### Capa 4: Router de Afinidad y Concurrencia (`core/router.py`)
- **Estrategia Zero-Swap (Anti-Thrashing en Producción):** En la Quadro RTX PRO 4000 (24 GB GDDR7), alternar modelos de 32B consume 8-10 segundos por swap de 20 GB. El Router prioriza la reutilización de modelos ancla calientes en VRAM (`_current_loaded_model`) si forman parte de la cadena de fallback válida para la tarea.
- **Orquestador en Dos Fases (Two-Phase Pipeline para VLM):** Procesa primero todas las imágenes del lote manteniendo el modelo VLM caliente en VRAM y luego conmuta al modelo textual para corrección y redacción final, erradicando los swaps intercalados.
- **Control de Concurrencia:** Inferencia serializada con `asyncio.Semaphore(1)` para prevenir desbordamientos de memoria (`CUDA OOM`).
- **Ejecución en Cascada:** Reintentos automáticos y fallback transparente si el modelo primario falla por timeout o error de servidor.

### Capa 5: Guardrails, Sanitización y Auditoría (`core/guardrails.py`)
- **Aislamiento de Razonamiento (`<think>`):**
  - Detecta y separa los bloques `<think>...</think>` de DeepSeek-R1.
  - Guarda la traza en metadatos para auditoría y devuelve el texto limpio al documento final.
- **Validación y Auto-Reparación de JSON:**
  - Extrae bloques estructurados de markdown o delimitadores `{}`.
  - Heurística de reparación para JSON incompleto o truncado por límite de tokens.
- **Auditoría Estructural de Markdown:**
  - Valida ratio de longitud y balance de fences de código.

---

## 🌐 Endpoints Expuestos en `servidor_api.py`

### 1. Endpoints de Compatibilidad OpenAI (`/v1`) para Open WebUI
- **`GET /v1/models`**: Retorna los 5 perfiles lógicos como modelos virtuales junto a cualquier modelo físico en Ollama.
- **`POST /v1/chat/completions`**:
  - Acepta la especificación OpenAI (`model`, `messages`, `temperature`, `stream`).
  - Mapea el modelo al perfil correspondiente.
  - Soporta streaming Server-Sent Events (`text/event-stream`) chunk a chunk.

### 2. Endpoints de Orquestación y Perfiles
- **`GET /api/perfiles`**: Retorna la ficha técnica de los perfiles activos y sus modelos asociados.
- **`POST /api/orquestar`**: Ejecuta inferencias directas con validación estricta y entrega métricas de auditoría.
- **`POST /api/procesar`**: Endpoint principal de documentos, ahora con soporte para el parámetro opcional `perfil`, delegando en el nuevo orquestador con retrocompatibilidad 100%.
