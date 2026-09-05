# Arquitectura Técnica — Plataforma IA Local & AnythingLLM Orchestrator

**Última actualización:** 2026-09-03  
**Versión:** 1.0.0 (Consolidación Monorepo)  
**Gobernanza:** Enterprise Coding Constitution (ECC v2.0.0)

---

## 1. Arquitectura General y Separación de Responsabilidades

El sistema opera bajo un modelo de monorepo desacoplado donde coexisten cuatro subsistemas principales:

| Subsistema | Directorio | Responsabilidad |
|:---|:---|:---|
| **Núcleo de Ejecución** | `Base/` | Servidor FastAPI, pipeline de procesamiento en 5 capas, interfaz web 360° y suite de tests. |
| **Gobernanza ECC** | `ECC/` | Marco rector inmutable de Everything Claude Code (agentes, habilidades, reglas de codificación). |
| **Harness de Producción** | `ai-harness/` | Gestión operativa de tareas (`work_queue.json`), control de progreso (`current.md`, `history.md`) y auditorías. |
| **Documentación Oficial** | `docs/` | 12 manuales maestros canónicos que rigen la operación, arquitectura y mantenimiento. |

---

## 2. El Pipeline en 5 Capas del Núcleo (`Base/core/`)

```
[Documento Fuente: DOCX / PDF / TXT]
                    │
                    ▼
┌────────────────────────────────────────┐
│ Capa 1: Ingesta, Detección y Hash      │  ──▶ `explorador.py` / `config.py`
│ - Cálculo de Hash SHA-256 fuente       │
│ - Validación de formato y permisos     │
└──────────────────┬─────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ Capa 2: Extracción y Conversión        │  ──▶ `conversor.py`
│ - MarkItDown / python-docx             │
│ - Conversión a Markdown estructurado   │
└──────────────────┬─────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ Capa 3: Chunking Semántico             │  ──▶ `chunker.py`
│ - Partición por párrafos/secciones     │
│ - Preservación de tablas y encabezados │
└──────────────────┬─────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ Capa 4: Inferencia IA & Corrección     │  ──▶ `corrector.py` / `servicios_ia.py`
│ - Cliente Ollama con retry exponencial │
│ - Pureza Zero-Chatter (sin preámbulos) │
│ - Fallback de modelos y control VRAM   │
└──────────────────┬─────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ Capa 5: Reconstrucción & Validación    │  ──▶ `reconstructor.py` / `validador.py`
│ - Reensamblado inmutable en `output/`  │
│ - Verificación de estructura y hashes  │
└────────────────────────────────────────┘
```

---

## 3. Servidor FastAPI y Capa de Integración (`Base/server/`)

1. **Adaptador OpenAI `/v1`:**
   - Endpoint: `POST /v1/chat/completions` y `GET /v1/models`.
   - Permite que AnythingLLM (Desktop o Docker) consuma directamente el pipeline y los modelos gestionados por el núcleo como si fuera un proveedor compatible con la API de OpenAI.

2. **Telemetría 360° en Tiempo Real:**
   - Endpoint: `GET /api/telemetria/360`.
   - Entrega métricas en vivo de CPU, RAM del sistema, VRAM y temperatura de GPU (NVIDIA vía `nvidia-smi` o WMI/fallback), estado del daemon Ollama y rendimiento del pipeline.

3. **Endpoints de Ingesta y Procesamiento:**
   - `POST /api/procesar`: Ingesta individual o por lotes con streaming SSE de progreso.
   - `GET /api/archivos`: Exploración de documentos en carpetas de entrada y salida.

---

## 4. Frontend Visual Dashboard 360° (`Base/web/`)

La interfaz del Dashboard 360° es una Single Page Application (SPA) ultra-ligera construida en HTML5 semántico, Vanilla CSS (diseño oscuro premium corporativo con tokens CSS) y Vanilla JavaScript modular:

- **Pestaña 1 (Telemetría 360°):** Tacómetros y barras de estado en tiempo real (CPU, RAM, VRAM, GPU Temp, Ollama Status).
- **Pestaña 2 (Procesamiento de Documentos):** Zona drag & drop, selección de modelo, selector de tono y visualizador split (Markdown vs. Corregido).
- **Pestaña 3 (AnythingLLM & Espacios):** Monitor de workspaces, estado del bridge RAG y configuración de prompts.
- **Pestaña 4 (Gobernanza & Auditoría):** Visor del estado de la Enterprise Coding Constitution y logs de auditoría.
- **Pestaña 5 (Terminal de Control):** Consola para disparar tareas operativas y scripts del sistema.

---

## 5. Simetría Operativa Multiplataforma

Toda operación del sistema cuenta con implementación idéntica y testeada en ambos sistemas operativos:

| Operación | Windows PowerShell (`Base/scripts/`) | Linux Bash (`Base/scripts/`) |
|:---|:---|:---|
| Iniciar Servidor Base | `iniciar_servidor.ps1` | `iniciar_servidor.sh` |
| Ejecutar Pruebas TDD | `ejecutar_pruebas.ps1` | `ejecutar_pruebas.sh` |
| Instalar Dependencias | `instalar_dependencias.ps1` | `instalar_dependencias.sh` |
| Despliegue Docker 10 Pax | `desplegar_docker.ps1` | `desplegar_docker.sh` |
| Verificación Hardware | `verificar_hardware.ps1` | `verificar_hardware.sh` |

---

## 6. Blindaje Criptográfico de Gobernanza (`core/ecc_guard.py`)

Cualquier intento de modificación o escritura en los directorios protegidos `/ECC` y `ai-harness/ecc/` es interceptado por la guardia criptográfica:
- Requiere autenticación del CEO mediante cálculo SHA-256 de token de autorización.
- Los tokens nunca se almacenan en texto plano en el repositorio.
- Previene regresiones accidentales provocadas por agentes autónomos de IA.
