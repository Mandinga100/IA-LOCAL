# Planificación y Arquitectura Técnica del Sistema

## 1. Principios de Arquitectura bajo Gobernanza ECC

La arquitectura del sistema responde a los principios clave del harness **Everything Claude Code (ECC v2.0.0)**:
- **Agent-First:** Especialización funcional en agentes de diseño, seguridad, rendimiento y calidad.
- **Inmutabilidad de Datos:** Uso sistemático de `@dataclass(frozen=True)` para todas las estructuras compartidas (`DocumentoTarea`, `ChunkTexto`, `Config`).
- **Tolerancia Cero a Fallos Silenciosos (`silent-failure-hunter`):** Prohibición terminante de bloques `except: pass` o retornos de texto vacío sin registrar excepción ni aislar el documento problemático.
- **Seguridad y Validación en Fronteras (`security-reviewer`):** Blindaje contra *Path Traversal* mediante `Path.resolve().is_relative_to()` y encapsulamiento en delimitadores seguros para neutralizar *Prompt Injection* indirecto.

---

## 2. Diagrama de Flujo del Pipeline de Procesamiento

```
                 [Directorio de Entrada]
                            │
                            ▼
             ┌─────────────────────────────┐
             │       explorador.py         │ ◄── Omitir temporales (~$*)
             │  (Hash SHA-256 + Tarea)     │
             └──────────────┬──────────────┘
                            │
                            ▼
             ┌─────────────────────────────┐
             │   ¿Hash ya en Ledger?       │ ──► [Omitir: ya procesado]
             └──────────────┬──────────────┘
                            │ NO
                            ▼
             ┌─────────────────────────────┐
             │        conversor.py         │ ◄── MarkItDown (DOCX/PDF/PPTX/XLSX/HTML)
             │   (Markdown UTF-8 limpio)   │     Fallback nativo UTF-8 (TXT/MD)
             └──────────────┬──────────────┘
                            │
                            ▼
             ┌─────────────────────────────┐
             │        corrector.py         │ ◄── Chunking semántico (\n\n)
             │   (Inferencia Ollama HTTP)  │ ◄── Prompts especializados (prompts.json)
             └──────────────┬──────────────┘
                            │
                            ▼
             ┌─────────────────────────────┐
             │       reconstructor.py      │ ──► Generación de .docx, .md, .txt, .html
             └──────────────┬──────────────┘
                            │
                            ▼
             ┌─────────────────────────────┐
             │      procesador_lote.py     │ ──► [Directorio de Salida]
             │ (Actualizar historial.json) │ ──► [Directorio de Errores] (en caso de fallo)
             └─────────────────────────────┘
```

---

## 3. Desglose Modular de Scripts

### 3.1. `config.py` (Configuración Inmutable)
- **Función:** Define la clase `Config` con decorador `frozen=True`. Centraliza rutas relativas/absolutas, credenciales locales, URL de Ollama, modelo activo, hiperparámetros (`temperature=0.2`, `top_p=0.9`, `num_ctx=4096`), tamaño de chunk (3.500 caracteres) y extensiones soportadas.
- **Ventaja:** Evita que hilos o procesos paralelos muten accidentalmente la configuración durante un lote masivo.

### 3.2. `logs.py` (Logging Estructurado y Auditoría)
- **Función:** Implementa rotación de logs mediante `RotatingFileHandler` con un límite de 10 MB y 5 copias de respaldo.
- **Blindaje Windows 10:** Forzado explícito de `encoding="utf-8"` en `RotatingFileHandler` (línea 44 de `logs.py`) y en `StreamHandler(sys.stdout)`. El handler opera de forma **síncrona estándar**, compatible con el pipeline secuencial (un documento a la vez). No se requiere I/O asíncrono dado que no existe concurrencia real en el sistema.

### 3.3. `explorador.py` (Escaneo Recursivo y Detección de Archivos)
- **Función:** Recorre recursivamente árboles de carpetas con `Path.rglob("*")`.
- **Filtros de Seguridad:**
  - Ocurrencia de archivos de bloqueo de Microsoft Office que inician con `~$`.
  - Archivos ocultos de sistema que inician con `.`.
  - Cálculo atómico de hash SHA-256 en bloques de 64 KB para identificar unívocamente el contenido.
  - ⚠️ **[Sprint 2-A — Pendiente]:** Validación de *Path Traversal* con `Path.resolve().is_relative_to(ruta_base)` para bloquear symlinks que apunten fuera del directorio raíz. Actualmente `resolve()` se llama pero la verificación `is_relative_to()` no está implementada.

### 3.4. `conversor.py` (Conversor Universal a Markdown)
- **Función:** Transforma documentos binarios y complejos en Markdown plano legible.
- **Motores:**
  - `MarkItDown` con todas las dependencias (`markitdown[all]`) para `.docx`, `.pptx`, `.xlsx`, `.pdf` y `.html`.
  - Lector nativo con `errors="replace"` y `utf-8` forzado para `.txt` y `.md`.
- **Manejo de Errores:** Lanza `ConversionError` ante corrupciones de archivo o dependencias ausentes, impidiendo que el pipeline continúe con un string vacío.

### 3.5. `corrector.py` (Inferencia Semántica e IA Local)
- **Función:** Divide el documento en objetos inmutables `ChunkTexto` respetando los párrafos dobles `\n\n` (sin cortar palabras a la mitad).
- **Comunicación HTTP:** Utiliza `httpx.Client` apuntando a `/api/generate` de Ollama con `stream=False`.
- **Resiliencia:** Algoritmo de reintentos exponenciales (2s, 4s, 8s) con timeout de 120 segundos. Lanza `InferenciaError` ante caídas no recuperables.

### 3.6. `reconstructor.py` (Reconstrucción de Formatos)
- **Función:** Toma el Markdown corregido y lo guarda en el formato de salida respectivo:
  - Documentos Word `.docx`: Reconstrucción jerárquica con `python-docx` interpretando títulos (`#`, `##`, `###`), viñetas y párrafos normales.
  - Documentos de texto `.txt` y `.md`: Escritura directa con codificación UTF-8 pura.
  - Documentos `.html`: Maquetación completa con `<!DOCTYPE html>`, meta `charset="utf-8"` y estilos CSS limpios.
  - Formatos complejos binarios (`.pdf`, `.xlsx`): Exportación con sufijo `.corregido.md` para revisión humana antes de sobreescritura.

### 3.7. `procesador_lote.py` (Orquestador y Ledger de Auditoría)
- **Función:** Coordina el flujo global. Incluye interfaz de línea de comandos (CLI) con `argparse` y barra de progreso en tiempo real con `tqdm`.
- **Tolerancia a Fallos y Reanudación:** Mantiene el archivo `historial_procesados.json`. Si un lote se interrumpe, al relanzarse se omiten instantáneamente los documentos cuyo hash ya haya sido procesado exitosamente. Los documentos con fallo se copian a `datos/errores/` para su aislamiento.

---

## 4. Estrategia de Prompts por Especialidad (`prompts.json`)

Se crearon 5 plantillas optimizadas para no alucinar y devolver únicamente el texto corregido:
1. **General:** Corrección ortográfica y gramatical neutra conservando tono coloquial o formal.
2. **Legal:** Preservación absoluta de términos jurídicos, numeración de cláusulas y citas legales.
3. **Técnico:** Respeto íntegro a bloques de código, comandos, nombres de variables y términos en inglés.
4. **Académico:** Elevación del estilo formal y coherencia sintáctica sin tocar citas bibliográficas.
5. **Comercial:** Fluidez, claridad ejecutiva y tono persuasivo sin alterar datos comerciales.
