# Base de Documentación del Proyecto: Plataforma IA Local

Bienvenido a la base oficial de documentación de la **Plataforma de Procesamiento, Corrección y Gestión de Documentos con IA Local**.

El sistema opera en arquitecturas **Windows 10 / 11 64-bit** y **GNU/Linux**, 100% desconectado de la nube (offline), aprovechando modelos LLM locales mediante **Ollama**, **AnythingLLM Multi-User en Docker**, un Gateway compatible con la API de OpenAI, un **Dashboard Web 360°** con telemetría de hardware en tiempo real y un motor de procesamiento en **Python 3.13** bajo gobernanza /ECC y verificación criptográfica SHA-256 del CEO.

---

## 📚 Índice Maestro de Documentación (Orden Estructurado)

| Orden | Documento | Ubicación | Descripción Técnica |
|:---:|---|---|---|
| **01** | **Contexto Global del Proyecto** | [contexto_proyecto.md](contexto_proyecto.md) | Alcance funcional, restricciones de hardware, stack tecnológico consolidado y monorepo. |
| **02** | **Planificación y Arquitectura Técnica** | [planificacion_y_arquitectura.md](planificacion_y_arquitectura.md) | Pipeline integral, inmutabilidad, chunking jerárquico, anti-mojibakes y matriz dual de hardware. |
| **03** | **Arquitectura del Núcleo de 5 Capas** | [arquitectura_nucleo_5_capas.md](arquitectura_nucleo_5_capas.md) | Módulo `core/`, endpoints `/v1`, afinidad Zero-Swap, two-phase batching y guardrails. |
| **04** | **Integración AnythingLLM, MCP y Pureza** | [integracion_anythingllm_mcp_y_pureza.md](integracion_anythingllm_mcp_y_pureza.md) | Protocolo Zero-Chatter, extracción visual pixel-perfect y visor web interactivo. |
| **05** | **Arquitectura Multi-Usuario Docker (10 Pax)** | [plan_anythingllm_docker_multiusers_10pax.md](plan_anythingllm_docker_multiusers_10pax.md) | Orquestación Docker, presupuesto matemático de VRAM, 4 workspaces y pruebas de concurrencia. |
| **06** | **Gobernanza /ECC y Autorización del CEO** | [gobernanza_harness_ecc_ceo.md](gobernanza_harness_ecc_ceo.md) | Política de inmutabilidad para `ECC/` y `ai-harness/ecc/` con verificación SHA-256 del CEO. |
| **07** | **Guía de Despliegue y Operación en Linux** | [despliegue_en_linux.md](despliegue_en_linux.md) | Simetría multiplataforma, scripts Bash (`.sh`), CUDA, Docker y systemd en distribuciones Linux. |
| **08** | **Dashboard Visual 360° y Telemetría** | [dashboard_frontend_360_y_telemetria.md](dashboard_frontend_360_y_telemetria.md) | Consola web con 5 pestañas, telemetría hardware GPU/RAM/CPU en vivo y visor comparativo. |
| **09** | **Guía Operativa y Manual de Uso** | [guia_operativa.md](guia_operativa.md) | Comandos Windows PowerShell nativos y Linux Bash, modos de ejecución y flags CLI. |
| **10** | **Especificación TDD y Matriz de Pruebas** | [especificacion_tdd_y_pruebas.md](especificacion_tdd_y_pruebas.md) | Matriz completa de las **176 pruebas automatizadas** (100% verde) y metodología ECC v2.0.0. |
| **11** | **Auditoría 360° y Transformaciones** | [auditoria_360_y_transformaciones/README.md](auditoria_360_y_transformaciones/README.md) | Análisis multidimensional y matriz de compatibilidad para 14 formatos ofimáticos. |
| **12** | **Reportes de Ejecución MVP** | [reportes_ejecucion_mvp/README.md](reportes_ejecucion_mvp/README.md) | Auditorías forenses y telemetría de inferencia en GPU GTX 1650. |
| **13** | **Auditoría Forense ECC y Claude** | [auditoria_forense_ecc_claude.md](auditoria_forense_ecc_claude.md) | Auditoría forense exhaustiva de compatibilidad, migración y pureza de skills. |
| **14** | **Manual de Desarrollo de Custom Skills** | [manual_desarrollo_custom_skills.md](manual_desarrollo_custom_skills.md) | Arquitectura técnica de ImportedPlugin, hot-reloading y canal requestToolApproval. |
| **15** | **Guía de Testeo Visual Multidocumento** | [guia_testeo_visual_multidocumento.md](guia_testeo_visual_multidocumento.md) | Metodología de auditoría comparativa paralela y matriz de modelos para GTX 1650. |

---

## 🗂️ Referencias de Entornos y Arneses Relacionados

- **Entorno de Producción (24 GB VRAM Workstation):** [`../Base/produccion/README.md`](../Base/produccion/README.md) — Guía de aprovisionamiento para NVIDIA RTX PRO 4000 Blackwell + i9-14900 + 128 GB RAM.
- **Entorno MVP Local (4 GB VRAM):** [`../Base/MVP/README.md`](../Base/MVP/README.md) — Calibración y optimización para NVIDIA GeForce GTX 1650 (4 GB).
- **Arnés Metodológico /ECC Protegido:** [`../ECC/README.md`](../ECC/README.md) — Marco metodológico inmutable con 8 agentes y 14 skills.
- **Arnés de Producción:** [`../ai-harness/ecc/`](../ai-harness/ecc/) — Instancia operativa con esquemas de workspaces para AnythingLLM.

---

## 🛡️ Gobernanza y Certificación de Calidad

- **Inmutabilidad y Seguridad:** Toda modificación estructural está sujeta a los contratos de la Enterprise Coding Constitution (ECC v2.0.0) y sellada criptográficamente para acceso exclusivo del CEO (`core/ecc_guard.py`).
- **Certificación TDD Automatizada:** La integridad del código y de las APIs se valida mediante **176 pruebas automatizadas** ejecutadas con `pytest`, cubriendo el 100% de los componentes críticos.
- **Backups de Estado Consolidado:** Respaldos automáticos generables mediante `scripts/generar_backup.py` tanto en Windows como en Linux.
