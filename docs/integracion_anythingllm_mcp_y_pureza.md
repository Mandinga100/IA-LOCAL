# Integración AnythingLLM Desktop, Protocolo Zero-Chatter y Preservación Visual Pixel-Perfect

**Documento:** `docs/integracion_anythingllm_mcp_y_pureza.md`  
**Estado:** PRODUCCIÓN / OPERATIVO  
**Gobernanza:** SDP-U / Arquitectura /ECC  
**Entorno Operativo:** Windows 10 Pro 64-bit, Ollama Local (Qwen 2.5 3B), AnythingLLM Desktop, Python 3.13.14  

---

## 1. Resumen Ejecutivo

La **Plataforma IA Local** ha completado su transición arquitectónica hacia un modelo headless donde **AnythingLLM Desktop** asume el rol de interfaz gráfica de usuario principal. 

A través de un **Action-Aware Gateway** compatible con la API de OpenAI (`/v1/chat/completions`), un **Servidor MCP Oficial** potenciado por el arnés `/ecc` y motores deterministas de **Pureza Documental (Zero-Chatter)** y **Preservación Visual Pixel-Perfect**, el sistema permite la corrección, reestructuración y conversión física de documentos (`.pdf`, `.docx`, `.odt`, `.rtf`, `.html`, `.md`, `.txt`) sin fugas conversacionales ni degradación visual.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             ANYTHINGLLM DESKTOP (GUI)                            │
│  - Workspace: Mi espacio de trabajo                                              │
│  - Proveedor LLM: OpenAI Compatible (http://127.0.0.1:8000/v1)                   │
│  - MCP Client: plataforma_ia_local (mcp_server.py stdio)                         │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ HTTP /v1/chat/completions (SSE Stream / Batch)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   ACTION-AWARE GATEWAY (servidor_api.py)                         │
│  - Intercepta intenciones de exportación ("devuelve en .pdf", "convertir a docx")│
│  - Extrae referencias de documentos fuente (localfile:// o rutas de Windows)     │
│  - Inyecta el Protocolo Zero-Chatter de Pureza Documental                        │
└──────────────┬─────────────────────────┬─────────────────────────┬───────────────┘
               │                         │                         │
               ▼                         ▼                         ▼
┌───────────────────────────┐ ┌───────────────────────────┐ ┌──────────────────────┐
│  PUREZA DOCUMENTAL        │ │  PRESERVACIÓN VISUAL      │ │ SERVIDOR MCP /ECC    │
│  (core/pureza_documental) │ │  (extractor_visual.py)    │ │ (mcp_server.py)      │
│  - Zero-Chatter           │ │  - pypdfium2 / pdfplumber │ │ - ecc_auditoria_pureza
│  - Remoción de preámbulos │ │  - Hash SHA-256 por asset │ │ - ecc_inspeccion_pixel
│  - Remoción de epílogos   │ │  - Anclaje posicional     │ │ - ecc_verification   │
│  - Retención 100% pura    │ │  - Flowables ReportLab    │ │ - ecc_telemetry      │
└──────────────┬────────────┘ └─────────────┬─────────────┘ └──────────────────────┘
               │                            │
               └──────────────┬─────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│               RECONSTRUCTOR Y CANALES DE DISTRIBUCIÓN FÍSICA                     │
│  1. Compilación a Disco: datos/salida_web/<documento>.[pdf|docx|odt|rtf|html]    │
│  2. Copia Inmediata en Escritorio: C:\Users\mandi\Desktop\<documento>.[pdf|docx] │
│  3. Visor Web Interactivo: http://127.0.0.1:8000/api/ver/<documento>             │
│  4. Descarga Directa HTTP: http://127.0.0.1:8000/api/descargar/<documento>       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Protocolo de Pureza Documental Estricta (Zero-Chatter)

### Diagnóstico Forense
Cuando un usuario solicita corregir o exportar un documento, los modelos LLM tienden de forma predeterminada a anteponer preámbulos de cortesía (*"Voy a corregir el documento...", "A continuación presento la versión corregida..."*, o notas alucinadas de versiones) y a cerrar con despedidas (*"Espero que te sea útil, no dudes en consultar"*). Si la salida de la IA se compila directamente, el documento final queda contaminado con dicho metatexto.

### Solución Implementada (`core/pureza_documental.py`)
Se diseñó un filtro determinista que aplica tres niveles de sanitización en el Gateway antes de entregar texto al reconstructor físico:

1. **Eliminación de Razonamiento:** Suprime cualquier bloque `<think>...</think>` proveniente de modelos de razonamiento (como DeepSeek-R1 o Qwen-QwQ).
2. **Corte Quirúrgico de Preámbulo:** Localiza el primer encabezado legítimo de Markdown (`# Título`) y poda todo el texto conversacional previo. Descarta encabezados falsos generados por el LLM tales como `### Detalles Técnicos del Procesamiento` o `### Documento Reconstruido`.
3. **Poda de Epílogo:** Analiza el texto desde la última línea hacia arriba para remover expresiones de despedida, firmas o disculpas.
4. **Cálculo de Índice de Pureza:** Emite una métrica porcentual de retención (`calcular_indice_pureza`) asegurando que el contenido sea 100% legítimo.

---

## 3. Preservación Visual Quirúrgica Pixel-Perfect de Imágenes

Para garantizar que diagramas, logotipos y firmas de documentos no se pierdan al reconstruir o cambiar formatos:

### Extracción (`extractor_visual.py`)
- **PDFs:** Se implementó `extraer_imagenes_pdf()` utilizando `pypdfium2` y `pdfplumber`. Cada imagen incrustada se extrae directamente en su resolución bitmap nativa sin recompresión ni alteración cromática.
- **DOCX:** Se extraen las imágenes empaquetadas en la estructura OpenXML mediante `extraer_imagenes_docx()`.
- **Huella SHA-256:** Cada asset recibe un identificador determinista único basado en su hash criptográfico SHA-256 (`asset_<sha256[:12]>.png`).
- **Prevención DoS:** Se aplican límites estrictos contra ataques de descompresión (Pixel Flood) limitando la descompresión a un máximo seguro de 50.000.000 píxeles.
- **Inyección de Anclas:** El módulo `inyectar_anclas_imagenes_en_markdown()` ubica las etiquetas `![asset_id](ruta_disco)` en el documento para mantener la correlación de lectura.

### Renderizado Físico (`reconstructor.py`)
- **En PDF (ReportLab):** Se detectan las etiquetas Markdown y se generan flowables `reportlab.platypus.Image` escalados proporcionalmente respetando la caja tipográfica y márgenes de la página (ancho máximo 480 pt), incorporando epígrafes tipográficos (`DocCaption`).
- **En Word (DOCX):** Se integró inserción nativa con `python-docx` (`doc.add_picture()`) con ancho calibrado en 5.5 pulgadas y párrafo de pie de foto centrado.
- **En HTML:** Se generan etiquetas semánticas `<figure><img ...><figcaption>...</figcaption></figure>`.

---

## 4. Servidor MCP Oficial con Arnés /ECC (`mcp_server.py`)

El servidor MCP (Model Context Protocol) se ejecuta bajo transporte estándar `stdio` y está registrado en la configuración de AnythingLLM Desktop (`%APPDATA%\anythingllm-desktop\storage\plugins\anythingllm_mcp_servers.json`).

### Herramientas Disponibles

| Herramienta | Origen / Dominio | Descripción Operativa |
|---|---|---|
| `corregir_y_exportar_documento` | Núcleo Plataforma | Extrae, corrige con Ollama y genera el archivo físico compilado con link de descarga. |
| `exportar_texto_a_documento` | Núcleo Plataforma | Convierte texto Markdown a `.pdf`, `.docx`, `.odt`, `.rtf`, `.html`, `.csv`, `.md`. |
| `telemetria_hardware_local` | Núcleo Plataforma | Reporta VRAM en uso/libre, temperatura y porcentaje de carga de la GPU NVIDIA GTX 1650. |
| `ecc_auditoria_pureza` | `/ecc` Safety Guard | Evalúa el texto contra el protocolo Zero-Chatter y devuelve el documento 100% esterilizado. |
| `ecc_inspeccion_visual_pixel` | `/ecc` Nutrient Docs | Reporta dimensiones (px), formato, peso (KB) y SHA-256 de todas las imágenes de un PDF/DOCX. |
| `ecc_verification_loop` | `/ecc` Verification Loop | Ejecuta validación en 4 fases (Build, Visual, Zero-Chatter y Compilación física). |
| `ecc_token_telemetry` | `/ecc` Cost-Aware | Telemetría de contexto y hardware para evitar desbordamientos de memoria en la GTX 1650. |

---

## 5. Visor Web Interactivo y Multicanal de Descarga

Al procesar cualquier solicitud de exportación desde AnythingLLM, el usuario recibe 4 vías simultáneas de acceso:

1. **Visor Web Interactivo (`GET /api/ver/{nombre_archivo}`):**  
   Interfaz moderna con tema oscuro, tipografía Inter/Outfit, visor PDF nativo embebido (`<iframe>`), metadatos del archivo y botón de descarga.
2. **Descarga Directa HTTP (`GET /api/descargar/{nombre_archivo}`):**  
   Emite el binario con cabecera `Content-Disposition: attachment` para descarga inmediata en el navegador.
3. **Copia Automática en Escritorio (`C:\Users\mandi\Desktop\`):**  
   El servidor copia automáticamente el archivo generado al Escritorio de Windows del usuario para apertura instantánea sin depender del explorador web.
4. **Comando Rápido PowerShell:**  
   Proporciona el comando `Start-Process "ruta_absoluta"` ejecutable en consola.

---

## 6. Configuración de AnythingLLM Desktop

### Registro de Servidor MCP (`anythingllm_mcp_servers.json`)
Ubicación: `C:\Users\mandi\AppData\Roaming\anythingllm-desktop\storage\plugins\anythingllm_mcp_servers.json`
```json
{
  "mcpServers": {
    "plataforma_ia_local": {
      "command": "C:\\Users\\mandi\\Documents\\Proyectos\\Plataforma IA local\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\mandi\\Documents\\Proyectos\\Plataforma IA local\\mcp_server.py"
      ]
    }
  }
}
```

### System Prompt del Workspace en SQLite (`anythingllm.db`)
El campo `openAiPrompt` de la tabla `workspaces` (ID 1) fue actualizado con las directivas de pureza documental y gobernanza /ECC para impedir que el LLM emita saludos o introducciones conversacionales.

---

## 7. Verificación y Cobertura de Pruebas

Toda la implementación cuenta con cobertura unitaria automatizada ejecutada con `pytest`:
- **Total de pruebas:** **122 pruebas pasadas, 1 saltada (100% VERDE)**.
- Módulos probados:
  - `tests/unit/test_pureza_documental.py`: 6 tests (Zero-Chatter, preámbulos, epílogos, pensares).
  - `tests/unit/test_extractor_visual.py`: 7 tests (DOCX, PDF pypdfium2, anclas Markdown, hashes).
  - `tests/unit/test_reconstructor.py`: 15 tests (DOCX, PDF ReportLab con imágenes, HTML, ODT, RTF).
  - `tests/unit/test_mcp_server.py`: 8 tests (Herramientas nativas y herramientas /ECC).
  - `tests/unit/test_servidor_api.py`: 8 tests (Salud, visor web HTML, descargas seguras).
  - `tests/unit/test_intent_detector.py`: 4 tests (Detección de formato, rutas locales, exportación).
  - `tests/unit/test_v1_endpoints.py`: 5 tests (Compatibilidad OpenAI, orquestación).
