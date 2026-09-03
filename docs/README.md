# Base de Documentación del Proyecto: Plataforma IA Local

Bienvenido a la base oficial de documentación de la **Plataforma de Procesamiento y Corrección de Documentos con IA Local**.

Este sistema opera en **Windows 10 64-bit**, 100% desconectado de la nube (offline), aprovechando modelos LLM locales mediante **Ollama** (`qwen2.5:7b`, `llama3.1:8b`), **MarkItDown** y un pipeline desacoplado en **Python 3.13**.

---

## 📚 Índice de Documentación

| Documento | Descripción |
|---|---|
| [Contexto del Proyecto](contexto_proyecto.md) | Objetivos, alcance funcional, stack tecnológico, requisitos de hardware y modelos locales. |
| [Arquitectura del Núcleo de 5 Capas](arquitectura_nucleo_5_capas.md) | Módulo `core/`, endpoints `/v1` para Open WebUI, política Zero-Swap y guardrails. |
| [Planificación y Arquitectura](planificacion_y_arquitectura.md) | Diseño desacoplado, inmutabilidad, chunking semántico, prevención de mojibakes y mitigación de errores en PowerShell. |
| [Especificación TDD y Pruebas](especificacion_tdd_y_pruebas.md) | Suite de pruebas unitarias e integración (12 tests, 83% cobertura), mocks con `respx` y auditoría de fallos silenciosos. |
| [Guía Operativa y Manual de Uso](guia_operativa.md) | Comandos para Windows 10 PowerShell, flags de CLI, configuración de Ollama, ledger de auditoría y troubleshooting. |
| [Reportes de Ejecución MVP](reportes_ejecucion_mvp/README.md) | Auditorías forenses, telemetría de GPU GTX 1650, métricas de rendimiento y resultados de las corridas del MVP. |
| [Auditoría 360° y Transformaciones](auditoria_360_y_transformaciones/README.md) | Análisis multidimensional, optimizaciones de VRAM/seguridad y matriz de compatibilidad para 14 formatos. |

---

## 🛡️ Gobernanza y Mantenimiento

- **Harness `/ECC`:** El núcleo del harness Everything Claude Code es **intocable e ineditable**, actuando como árbitro metodológico estricto.
- **Control de Progreso (`ai-harness/`):** Todo el seguimiento evolutivo, checkpoints, historial de sesiones y estados de la cola de trabajo se registran formalmente en la ruta `ai-harness/progress/`.
