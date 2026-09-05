# Planificación Técnica y Hoja de Ruta del MVP Local (GTX 1650)

## 1. Propósito de esta Planificación

Esta planificación redefine y adapta el proyecto para un **MVP de pruebas parciales en local** sobre el hardware real de desarrollo: **Windows 10 Pro 64-bit, AMD Ryzen 5 3600 (6C/12T), 16 GB de RAM y NVIDIA GeForce GTX 1650 con aproximadamente 4 GB de VRAM dedicada**. 

El objetivo no es alcanzar throughput masivo ni sustituir el perfil de producción, sino validar exhaustivamente la arquitectura, estabilidad, prompts, logging UTF-8, reconstrucción documental y tolerancia a fallos en un entorno restringido y 100% local.

La planificación original del proyecto estaba calibrada para GPUs de 8–12 GB VRAM como mínimo operativo (con `qwen2.5:7b` o `llama3.1:8b` y `num_ctx=4096`). Esa base se conserva intacta en `docs/` como referencia para el servidor final o estaciones más potentes, pero queda estrictamente segregada de esta carpeta `MVP/`.

---

## 2. Supuestos de Hardware y Presupuesto de Memoria

### 2.1. Perfil de Hardware Local
| Componente | Especificación Real | Implicación Operativa |
|---|---|---|
| **Sistema Operativo** | Windows 10 Pro 64-bit | PowerShell 5.1+ / Core 7+, rutas Windows con backslashes/quotes. |
| **CPU** | AMD Ryzen 5 3600 (6 núcleos / 12 hilos) | Capacidad suficiente para pre/post-procesamiento (`MarkItDown`, `python-docx`). |
| **RAM** | 16 GB DDR4 | Margen suficiente para el runtime Python y el SO. |
| **GPU** | NVIDIA GeForce GTX 1650 | Aceleración CUDA activa en Ollama. |
| **VRAM Dedicada** | **3.935 MB (~4 GB)** | **Restricción dura.** El modelo + KV Cache deben caber 100% aquí. |
| **Memoria Compartida** | 8.142 MB (WDDM 2.7) | **No utilizable para LLM.** Provoca degradación extrema de throughput (~90% de caída por bus PCIe). |
| **Entorno IA** | Ollama local en `http://localhost:11434` | Conexión HTTP vía `httpx.Client` secuencial. |

### 2.2. Presupuesto Matemático de VRAM en Windows 10
Con el monitor y el Desktop Window Manager (DWM) activos, el sistema reserva entre 400 y 700 MB de VRAM.
- **VRAM neta disponible para Ollama:** **~3.200 MB – 3.400 MB**.

| Modelo | Cuantización | Peso Disco | VRAM Modelo | KV Cache (`ctx=2048`) | VRAM Total | Margen Restante | Estado |
|---|---|---|---|---|---|---|---|
| `qwen2.5:3b` | Q4_K_M | ~1.9 GB | ~2.000 MB | ~300 MB | **~2.300 MB** | ✅ ~900 MB libres | **Principal General** |
| `qwen2.5:1.5b` | Q4_K_M | ~1.0 GB | ~1.100 MB | ~180 MB | **~1.280 MB** | ✅ ~1.900 MB libres | **Fallback General** |
| `qwen2.5-coder:3b` | Q4_K_M | ~1.9 GB | ~2.050 MB | ~300 MB | **~2.350 MB** | ✅ ~850 MB libres | **Principal Técnico** |
| `qwen2.5-coder:1.5b` | Q4_K_M | ~1.0 GB | ~1.100 MB | ~180 MB | **~1.280 MB** | ✅ ~1.900 MB libres | **Fallback Técnico** |
| `qwen2.5:7b` *(Prod)* | Q4_K_M | ~4.7 GB | ~4.900 MB | ~600 MB | **~5.500 MB** | ❌ **OOM Garantizado** | **Excluido de MVP** |

---

## 3. Objetivo y Alcance del MVP

### 3.1. Objetivo General
Demostrar que el pipeline opera de punta a punta en lotes pequeños, con preservación estructural y **tolerancia cero a fallos silenciosos**. Esto abarca:
1. Exploración con hash SHA-256 y guardia path traversal (`is_relative_to`).
2. Conversión universal a Markdown (`MarkItDown` + fallback nativo UTF-8).
3. Chunking semántico por párrafos dobles (`\n\n`).
4. Inferencia con IA local vía Ollama y prompts especializados (`prompts.json`).
5. Reconstrucción fiel en `.docx`, `.md`, `.txt` y `.html`.
6. Trazabilidad en ledger (`historial_procesados.json`) y aislamiento en `datos/errores/`.

### 3.2. Objetivos Específicos
#### Obligatorios
- Confirmar que Ollama ejecuta los modelos compactos con aceleración CUDA (`100% GPU`).
- Confirmar que el pipeline procesa documentos cortos y medianos sin bloquear el sistema operativo.
- Validar la integridad de logs UTF-8, ledger y copia a carpeta de errores.
- Validar prompts `general` y `tecnico` con los modelos de la familia `3B`.
- Confirmar el mecanismo de `modelo_fallback` instanciado en `Config`.

#### Deseables
- Comparar cualitativamente `qwen2.5:3b` frente a `qwen2.5-coder:3b` y `llama3.2:3b` en casos breves.
- Medir tiempos reales por chunk y por documento para proyectar necesidades de servidor.
- Detectar los umbrales prácticos de `num_ctx` y `chunk_chars` sobre la GTX 1650.

---

## 4. Exclusiones del MVP Local

Quedan formalmente fuera del alcance de este entorno:
- Producción final y procesamiento de lotes masivos (>50 documentos por corrida).
- Modelos 7B o superiores como baseline de trabajo diario.
- Modelos de 14B o superiores.
- Procesamiento concurrente o multihilo de documentos (concurrencia estrictamente = 1).
- Contextos extensos (4.096 a 8.192 tokens).
- Benchmarks comerciales definitivos.

---

## 5. Arquitectura Vigente y Segregación de Perfiles

La arquitectura modular se mantiene 100% idéntica entre entornos (`explorador.py`, `conversor.py`, `corrector.py`, `reconstructor.py`, `procesador_lote.py`, `config.py`, `logs.py`). Lo que varía es el **perfil de capacidad operativa**:

| Variable de Configuración | Perfil Producción (GPU 8–12 GB) | Perfil MVP Local (GTX 1650 4 GB) |
|---|---|---|
| **Modelo Principal General** | `qwen2.5:7b` o `llama3.1:8b` | `qwen2.5:3b` |
| **Modelo Fallback General** | Modelo secundario 8B | `qwen2.5:1.5b` |
| **Modelo Principal Técnico** | `qwen2.5:7b` / `qwen2.5-coder:7b` | `qwen2.5-coder:3b` |
| **Modelo Fallback Técnico** | `qwen2.5:7b` | `qwen2.5-coder:1.5b` |
| **num_ctx (Tokens)** | 4096 | **2048** (contingencia: 1024) |
| **chunk_size (Caracteres)** | 3000 – 3500 | **1500 – 2200** (default: 1800) |
| **chunk_overlap** | 200 | 150 – 200 |
| **Concurrencia Documental** | 1 (escalable) | **1 estricto** (secuencial) |
| **Carpeta Documental** | `docs/` | `MVP/` |

---

## 6. Estrategia de Perfiles de Modelos

### Perfil Principal (General)
```text
modelo: qwen2.5:3b
fallback: qwen2.5:1.5b
num_ctx: 2048
chunk_chars: 1800
concurrencia: 1
```

### Perfil Técnico / Código
```text
modelo: qwen2.5-coder:3b
fallback: qwen2.5-coder:1.5b
num_ctx: 2048
chunk_chars: 2000
concurrencia: 1
```

### Perfil de Contingencia (Memoria Crítica)
```text
modelo: qwen2.5:1.5b
num_ctx: 1024
chunk_chars: 1500
concurrencia: 1
```

---

## 7. Preparación de Datos Reales de Prueba (Estructura Local)

```text
datos/
├── entrada_mvp/
│   ├── lote_a_texto/         (3-5 archivos: .txt y .md cortos con faltas ortográficas reales)
│   ├── lote_b_ofimatica/     (2-3 archivos: .docx de 1-2 páginas con títulos H1/H2 y listas)
│   ├── lote_c_tecnico/       (1-2 archivos: .md con código python/powershell y comandos)
│   └── lote_d_control/       (1 archivo binario corrupto para validar aislamiento)
├── salida_mvp/               (Documentos corregidos generados y ledger historial_procesados.json)
└── errores_mvp/              (Archivos problemáticos aislados automáticamente)
```

---

## 8. Etapas de Implementación Operativa

### Etapa 0: Segregación Documental *(Completada)*
- **Resultado:** Coexistencia estricta de la documentación original en `docs/` y la línea de laboratorio en `MVP/`.
- **Regla:** El hardware local opera exclusivamente bajo las directivas de `MVP/`.

### Etapa 1: Baseline Operativo Local
- **Resultado:** Entorno virtual Python 3.13 con dependencias instaladas y Ollama listo.
- **Acciones:**
  1. Forzar UTF-8 en PowerShell (`[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $env:PYTHONUTF8 = "1"`).
  2. Verificar entorno `.venv` y dependencias (`uv pip install -r requirements.txt`).
  3. Descargar modelos locales:
     ```powershell
     ollama pull qwen2.5:3b
     ollama pull qwen2.5:1.5b
     ollama pull qwen2.5-coder:3b
     ollama pull qwen2.5-coder:1.5b
     ```

### Etapa 2: Smoke Test de Inferencia y Monitorización
- **Resultado:** Verificación de aceleración GPU y medición de VRAM.
- **Acciones:**
  1. Iniciar monitor en consola dedicada: `nvidia-smi -l 1`.
  2. Ejecutar inferencia mínima de prueba vía API REST local:
     ```powershell
     $body = @{ model = "qwen2.5:3b"; prompt = "Corrige la ortografía: El camion tenia una averia."; stream = $false } | ConvertTo-Json
     Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $body -ContentType "application/json"
     ```
  3. Ejecutar `ollama ps` y verificar que figure `100% GPU` con un consumo total de VRAM menor a **2.500 MB**.

### Etapa 3: Integración del Pipeline Mínimo (Lotes A y B)
- **Resultado:** Procesamiento exitoso de documentos generales sin bloquear el sistema.
- **Acciones:**
  1. Ejecutar `procesador_lote.py` sobre `datos/entrada_mvp/lote_a_texto`.
  2. Ejecutar `procesador_lote.py` sobre `datos/entrada_mvp/lote_b_ofimatica`.
  3. Verificar que los `.docx` se reconstruyen jerárquicamente y que `historial_procesados.json` almacena los hashes.

### Etapa 4: Especialización Técnica (Lote C)
- **Resultado:** Confirmar que `qwen2.5-coder:3b` respeta bloques de código y variables.
- **Acciones:**
  1. Ejecutar con `--tipo tecnico --modelo qwen2.5-coder:3b` sobre `datos/entrada_mvp/lote_c_tecnico`.
  2. Auditar que las líneas de código, comandos PowerShell y nombres de funciones no sufrieron alteraciones semánticas indebidas.

### Etapa 5: Resiliencia, Fallback y Recuperación (Lote D)
- **Resultado:** Certificar tolerancia a fallos y reanudación rápida.
- **Acciones:**
  1. Procesar archivo corrupto en `lote_d_control` y verificar su copia a `datos/errores_mvp/`.
  2. Reejecutar el lote completo y verificar la omisión instantánea por Ledger (`Omitiendo...`).

### Etapa 6: Cierre y Consolidación del MVP
- **Resultado:** Emisión del reporte de cierre de pruebas locales y certificación de parámetros estables.

---

## 9. Roadmap por Sprints Adaptado al MVP

| Sprint | Enfoque | Entregables |
|---|---|---|
| **Sprint 1** | Entorno y Baseline | `.venv`, modelos locales descargados, Ollama en ejecución, verificación CUDA con `nvidia-smi`. |
| **Sprint 2** | Pipeline Mínimo Local | Procesamiento de Lotes A y B (`qwen2.5:3b`), validación de reconstrucción Word y UTF-8. |
| **Sprint 3** | Calidad Técnica | Pruebas de Lote C con `qwen2.5-coder:3b`, evaluación cualitativa de preservación de sintaxis. |
| **Sprint 4** | Resiliencia y Fallback | Validación de aislamiento en `datos/errores_mvp/`, prueba de fallback e idempotencia con ledger. |
| **Sprint 5** | Consolidación y Métricas | Registro de tiempos por documento, consumo de VRAM y parámetros óptimos fijados para el laboratorio. |

---

## 10. KPIs Adaptados al MVP Local

| KPI | Meta de Laboratorio Local (GTX 1650) | Método de Medición | Estado |
|---|---|---|---|
| **Arranque de Ollama** | 100% reproducible | `Invoke-RestMethod /api/version` | ✅ Verificado |
| **Aceleración GPU** | `100% GPU` en `ollama ps` | `ollama ps` / `nvidia-smi` | Requerido |
| **Pico Máximo de VRAM** | < 3.200 MB (<85% de VRAM dedicada) | `nvidia-smi -l 1` | Requerido |
| **Tasa de Error** | < 10% en documentos bien formados | Auditoría de `historial_procesados.json` | Requerido |
| **OOM Recurrente** | 0 incidentes en perfil nominal | Logs del sistema | Requerido |
| **Reanudación por Ledger** | 100% de omisión de procesados | Log: `Omitiendo...` | Requerido |
| **Fidelidad UTF-8** | Cero mojibake (`ñ`, `«»`, tildes intactas) | Inspección de salidas `.docx`, `.txt`, `.md` | Requerido |

---

## 11. Matriz de Riesgos y Mitigaciones Inmediatas

| Riesgo Operativo | Severidad | Indicador / Causa | Protocolo de Mitigación Inmediata |
|---|---|---|---|
| **OOM en GPU** | Alta | VRAM > 3.900 MB, crash en Ollama | 1. Cerrar navegadores, Discord y clientes 3D.<br>2. Reiniciar Ollama (`taskkill /F /IM ollama.exe`).<br>3. Activar perfil de contingencia: `qwen2.5:1.5b` con `num_ctx: 1024`. |
| **Derrame a CPU (Offloading)** | Media/Alta | GPU al 0%, CPU al 100%, latencia > 60s/chunk | 1. Confirmar con `ollama ps` si hay capas en CPU.<br>2. Reducir `chunk_chars` a 1.500.<br>3. Migrar a modelo 1.5B. |
| **Falta de flag CLI para Fallback** | Media | CLI no expone `--fallback` | Configurar `modelo_fallback` vía instanciación directa de `Config` en script hasta implementar gap G-01. |
| **Documentos Extensos** | Media | Documento > 20 páginas satura memoria | Limitar los lotes locales a documentos de 1 a 5 páginas durante el MVP. |
| **Contaminación de Perfiles** | Alta | Usar parámetros de 7B en la GTX 1650 | Mantener segregación estricta: todo comando local debe leer exclusivamente de `MVP/`. |

---

## 12. Priorización de Gaps Técnicos (Adaptados al MVP)

| Prioridad | ID Gap | Descripción | Impacto en el MVP Local |
|---|---|---|---|
| **P1 (Alta)** | **G-01** | Soporte CLI `--fallback` en `procesador_lote.py` | Permitirá activar `qwen2.5:1.5b` sin editar código Python. |
| **P1 (Alta)** | **G-06** | Límite de tamaño máximo de archivo en `explorador.py` | Evita que un archivo accidentalmente enorme congele la GTX 1650. |
| **P2 (Media)** | **G-05** | Validación de schema para `prompts.json` | Previene que prompts incompletos degraden la respuesta del modelo compacto. |
| **P2 (Media)** | **G-04** | Heurística de detección de binarios mal nombrados | Aísla archivos binarios corruptos antes de enviarlos a inferencia. |
| **P3 (Baja)** | **G-03** | Test unitario de BOM UTF-8 | Robustez marginal en lectura de archivos heredados de Windows. |
| **P3 (Baja)** | **G-02** | Test de junctions NTFS (`mklink /J`) | Blindaje adicional en symlinks de Windows. |
| **P3 (Baja)** | **G-07** | Script automatizado de benchmark para GTX 1650 | Automatización de la toma de métricas de tokens/segundo. |

---

## 13. Decisión Operativa Final

La estrategia validada para la GTX 1650 no consiste en forzar modelos grandes ni emular un servidor empresarial, sino en **establecer un perfil de laboratorio robusto, predecible y rápido**. 

Operar con la familia **1.5B – 3B**, contexto de **2048**, chunks de **1.800 caracteres** y **un solo documento a la vez** garantiza que el 100% de la inferencia se ejecute en la VRAM de la GPU, permitiendo validar la lógica de negocio, los prompts y la arquitectura sin riesgos de colapso de memoria.
