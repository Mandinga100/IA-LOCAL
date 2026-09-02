# Contexto del Proyecto: Plataforma IA Local

## 1. Visión y Propósito
El objetivo primordial del proyecto es desarrollar e implantar un sistema automatizado en **Python** sobre **Windows 10 64-bit** que procese de forma masiva y por lotes documentos locales de múltiples formatos (`.pdf`, `.docx`, `.pptx`, `.xlsx`, `.html`, `.txt`, `.md`), los convierta a Markdown estructurado, aplique corrección ortográfica, gramatical y de estilo mediante **Modelos de Lenguaje Locales (LLM) vía Ollama**, y preserve la integridad documental y estructural de salida.

---

## 2. Restricciones Críticas del Sistema

1. **Privacidad y Soberanía de Datos (100% Local):**
   - Cero dependencias de APIs en la nube (sin OpenAI, sin Anthropic, sin servicios de telemetría externa).
   - Toda inferencia se realiza exclusivamente en la GPU/CPU local del usuario mediante la API HTTP de Ollama (`http://localhost:11434`).

2. **Optimización para VRAM Limitada (8–16 GB):**
   - El consumo de VRAM de la GPU no debe exceder los 7.5 GB para modelos de 7B/8B, reservando margen libre para el sistema operativo y tareas gráficas.
   - Procesamiento estrictamente secuencial de chunks e inferencia concurrente acotada (1 ráfaga a la vez).

3. **Plataforma Nativa Windows 10 64-bit:**
   - Soporte total para PowerShell nativo (5.1 y Core 7+).
   - Manipulación de rutas mediante `pathlib.Path` para evitar errores de escape con backslashes (`\`).
   - Forzado universal de codificación `utf-8` para erradicar el problema endémico de mojibakes en consolas Windows (`CP1252` / `OEM 850`).

4. **Procesamiento de Documentos Extensos (Chunking Semántico):**
   - División segura de textos en fragmentos de 3.000 a 4.000 caracteres respetando los límites naturales de párrafos (`\n\n`) y encabezados Markdown, evitando truncar oraciones, listas o tablas.

---

## 3. Stack Tecnológico de Vanguardia

| Capa / Componente | Tecnología Seleccionada | Justificación Técnica |
|---|---|---|
| **Sistema Operativo** | Windows 10 Pro 64-bit | Entorno del MVP local, PowerShell nativo. |
| **Runtime & Gestor** | Python 3.13.14 64-bit + `uv` 0.7.8 | Alto rendimiento, resolución de paquetes en milisegundos y aislamiento total en `.venv`. |
| **Motor de Inferencia** | Ollama (`http://localhost:11434`) | Orquestador local de LLMs optimizado para aceleración CUDA en Windows. |
| **Modelos de IA** | `qwen2.5:7b-instruct`, `llama3.1:8b-instruct` | Alta fidelidad sintáctica en español, respeto a tablas Markdown y respuesta directa sin preámbulos. |
| **Conversión a Markdown** | `MarkItDown` (`markitdown[all]`) | Conversión universal de DOCX, PPTX, XLSX, HTML y PDF a Markdown limpio. |
| **Reconstrucción** | `python-docx`, I/O UTF-8 nativo | Ensamblado fiel de documentos `.docx`, `.md`, `.txt` y `.html`. |
| **Validación y Datos** | Python `@dataclass(frozen=True)` | Inmutabilidad funcional para prevenir mutaciones colaterales en lotes concurrentes. |
| **Testing & Calidad** | `pytest`, `pytest-cov`, `respx` | Cobertura TDD del 83%, simulación de inferencia sin requerir Ollama activo en CI/CD local. |

---

## 4. Requisitos de Hardware y Dimensionamiento

- **GPU con 8–12 GB VRAM:**
  - *Modelo recomendado:* `qwen2.5:7b` o `llama3.1:8b` cuantizados a 4-bit (`Q4_K_M`).
  - *Ventana de contexto (`num_ctx`):* 4.096 tokens.
  - *Tamaño de Chunk:* 3.000–3.500 caracteres.
  - *Batch size:* 1 documento a la vez.
- **GPU con 16–24 GB VRAM:**
  - *Modelo recomendado:* `qwen2.5:14b` o `gemma-2:9b`.
  - *Ventana de contexto (`num_ctx`):* 8.192 tokens.
  - *Tamaño de Chunk:* 4.000–5.000 caracteres.
  - *Batch size:* 2–3 documentos paralelos.
- **CPU y RAM del Sistema:**
  - Mínimo 16 GB de RAM física.
  - SSD NVMe recomendado para lecturas y escrituras intensivas en disco.
