# Contexto del Proyecto — Plataforma de Procesamiento y Corrección de Documentos con IA Local & AnythingLLM Orchestrator

**Última actualización:** 2026-09-03  
**Versión del Sistema:** 1.0.0 (Consolidación Monorepo)  
**Gobernanza:** Enterprise Coding Constitution (ECC v2.0.0)

---

## 1. Visión General y Propósito
El proyecto consiste en una plataforma integral y soberana de extracción, procesamiento, chunking semántico y corrección gramatical/estilística de documentos corporativos en formatos DOCX, PDF, Markdown y texto plano.

Opera de forma estrictamente local y privada (air-gapped / offline first), combinando la potencia de modelos de lenguaje open-source (Llama 3, Mistral, DeepSeek) ejecutados mediante Ollama, la integración sinérgica con AnythingLLM como orquestador empresarial RAG/Multi-agente, y un Dashboard Visual 360° en tiempo real con monitoreo de hardware.

---

## 2. Estructura del Monorepo
El repositorio se encuentra unificado bajo la raíz `AnythingLLM/`:

```
AnythingLLM/
├── Base/                  # Núcleo de backend en Python (FastAPI, procesamiento de documentos, Ollama)
│   ├── core/              # Motor del pipeline (conversor, corrector, chunker, reconstructor, ecc_guard)
│   ├── server/            # Servidor FastAPI, endpoints REST, telemetría y adaptador OpenAI /v1
│   ├── web/               # Frontend estático del Dashboard Visual 360° (HTML, CSS, JS)
│   ├── tests/             # Suite de 176 tests automatizados con pytest y pytest-cov
│   ├── scripts/           # Scripts operativos simétricos para Windows (.ps1) y Linux (.sh)
│   ├── output/            # Directorio de entrega inmutable de documentos procesados
│   └── prompts.json       # Prompts especializados para el pipeline de corrección
├── ECC/                   # Enterprise Coding Constitution (Harness de desarrollo y agentes)
├── ai-harness/            # Harness operativo en producción, work_queue, progress, y gobernanza
└── docs/                  # Documentación técnica y operativa oficial (12 manuales maestros)
```

---

## 3. Stack Tecnológico y Dependencias

| Componente | Tecnología | Versión / Detalle | Función |
|:---|:---|:---|:---|
| **Lenguaje Backend** | Python | >= 3.10 / 3.13 | Lógica central del pipeline y servidor |
| **Framework Web** | FastAPI + Uvicorn | 0.115+ / 0.34+ | API REST asíncrona, SSE y adaptador OpenAI |
| **Extracción Documentos** | MarkItDown + python-docx | 0.0.1a4+ / 1.1+ | Conversión de DOCX/PDF/TXT a Markdown estructurado |
| **Validación de Datos** | Pydantic v2 + Dataclasses | 2.10+ | Validación de esquemas y tipos inmutables |
| **Motor de Inferencia** | Ollama | v0.5+ | Servidor de modelos LLM locales |
| **Orquestación RAG** | AnythingLLM | Desktop / Docker | Gestión de espacios de trabajo, agentes y RAG |
| **Dashboard Frontend** | Vanilla HTML5 / CSS3 / JS | Estándar W3C | Dashboard 360° sin dependencias pesadas de build |
| **Framework de Tests** | pytest + pytest-asyncio + respx | 8.3+ | 176 tests unitarios y de integración |
| **Seguridad de Gobernanza** | SHA-256 Cryptographic Guard | `core/ecc_guard.py` | Protección inmutable de carpetas `/ECC` |

---

## 4. Perfiles de Hardware Objetivo

1. **Perfil Económico / Ultrabook (GTX 1650 4GB VRAM):**
   - Modelos: `llama3.2:1b`, `qwen2.5:1.5b`, `llama3.2:3b` (Q4_K_M).
   - Modo de operación: Carga secuencial con descarga forzada preventiva (`keep_alive=0`) para evitar Out-Of-Memory (OOM).

2. **Perfil Servidor / Estación de Trabajo (RTX 3060 12GB VRAM):**
   - Modelos: `llama3:8b`, `mistral:7b`, `deepseek-r1:8b`, embeddings `nomic-embed-text`.
   - Modo de operación: Residencia permanente en VRAM para baja latencia en AnythingLLM y pipeline de documentos.

---

## 5. Modos de Operación Soportados
- **Modo 1: Offline Puro:** 100% desconectado, inferencia local con Ollama en Windows/Linux.
- **Modo 2: Asistido Local (Desktop AnythingLLM):** Inferencia compartida con la UI desktop de AnythingLLM.
- **Modo 3: Híbrido (Local + Cloud API):** Enrutamiento inteligente según confidencialidad de datos.
- **Modo 4: Full Cloud:** Para entornos sin GPU local utilizando APIs de Anthropic/OpenAI/Gemini.
- **Modo 5: Docker Multiuser (10 Pax):** Despliegue contenerizado corporativo para 10 usuarios concurrentes con AnythingLLM multi-tenant.

---

## 6. Estado y Certificación
- **Tests Automatizados:** 176 tests ejecutados (175 passed, 1 skipped) con pytest.
- **Simetría de Scripts:** 100% de paridad funcional entre scripts Windows PowerShell (`.ps1`) y Linux Bash (`.sh`).
- **Integridad de Datos:** Zero-Chatter garantizado en respuestas LLM hacia AnythingLLM; preservación de formato Markdown y tablas; validación SHA-256 en salida.
