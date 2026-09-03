# Base de Documentación del Proyecto: Plataforma IA Local

Bienvenido a la base oficial de documentación de la **Plataforma de Procesamiento y Corrección de Documentos con IA Local**.

Este sistema opera en **Windows 10 / 11 64-bit**, 100% desconectado de la nube (offline), aprovechando modelos LLM locales mediante **Ollama**, **AnythingLLM Multi-User en Docker**, un Gateway compatible con la API de OpenAI y un pipeline desacoplado en **Python 3.13** bajo gobernanza /ECC.

---

## 📚 Índice Maestro de Documentación

| Documento | Ubicación | Descripción |
|---|---|---|
| **Arquitectura Multi-Usuario Docker (10 Usuarios)** | [plan_anythingllm_docker_multiusers_10pax.md](plan_anythingllm_docker_multiusers_10pax.md) | Orquestación Docker, cálculo de VRAM en concurrencia y matriz de roles. |
| **Integración AnythingLLM, MCP y Pureza** | [integracion_anythingllm_mcp_y_pureza.md](integracion_anythingllm_mcp_y_pureza.md) | Protocolo Zero-Chatter, extracción visual pixel-perfect y visor web interactivo. |
| **Entorno de Producción (24 GB VRAM Workstation)** | [../produccion/README.md](../produccion/README.md) | Guía, modelos 14B/32B, docker-compose y scripts para RTX PRO 4000 Blackwell + i9-14900. |
| **Entorno MVP Local (4 GB VRAM)** | [../MVP/README.md](../MVP/README.md) | Guía, modelos compactos 3B y validación en NVIDIA GeForce GTX 1650. |
| **Arnés /ECC Curado (3.5 MB)** | [../ECC/README.md](../ECC/README.md) | Catálogo de los 8 agentes y 14 skills seleccionados para ofimática, presentaciones y código. |
| **Contexto del Proyecto** | [contexto_proyecto.md](contexto_proyecto.md) | Alcance funcional, stack tecnológico, requisitos de hardware y modelos locales. |
| **Arquitectura del Núcleo de 5 Capas** | [arquitectura_nucleo_5_capas.md](arquitectura_nucleo_5_capas.md) | Módulo `core/`, endpoints `/v1`, afinidad Zero-Swap y guardrails. |
| **Planificación y Arquitectura** | [planificacion_y_arquitectura.md](planificacion_y_arquitectura.md) | Diseño desacoplado, inmutabilidad, chunking semántico y prevención de mojibakes. |
| **Especificación TDD y Pruebas** | [especificacion_tdd_y_pruebas.md](especificacion_tdd_y_pruebas.md) | Suite de 154 pruebas unitarias (100% verde) y prueba de estrés de 10 usuarios concurrentes. |
| **Guía Operativa y Manual de Uso** | [guia_operativa.md](guia_operativa.md) | Comandos para Windows 10 PowerShell, flags de CLI y troubleshooting. |
| **Reportes de Ejecución MVP** | [reportes_ejecucion_mvp/README.md](reportes_ejecucion_mvp/README.md) | Auditorías forenses y telemetría de GPU GTX 1650. |
| **Auditoría 360° y Transformaciones** | [auditoria_360_y_transformaciones/README.md](auditoria_360_y_transformaciones/README.md) | Análisis multidimensional y matriz de compatibilidad para 14 formatos. |

---

## 🛡️ Gobernanza y Mantenimiento

- **Arnés `/ECC` Curado:** El arnés ha sido optimizado y saneado quirúrgicamente para eliminar dependencias innecesarias, preservando solo las herramientas requeridas por los usuarios.
- **Control de Versiones y Backup:** Todo cambio arquitectónico se valida mediante la suite automatizada de 154 pruebas (`pytest`) y se respalda con `scripts/generar_backup.py`.
