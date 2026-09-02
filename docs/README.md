# Base de Documentación del Proyecto: Plataforma IA Local

Bienvenido a la base oficial de documentación de la **Plataforma de Procesamiento y Corrección de Documentos con IA Local**.

Este sistema opera en **Windows 10 64-bit**, 100% desconectado de la nube (offline), aprovechando modelos LLM locales mediante **Ollama** (`qwen2.5:7b`, `llama3.1:8b`), **MarkItDown** y un pipeline desacoplado en **Python 3.13**.

---

## 📚 Índice de Documentación

| Documento | Descripción |
|---|---|
| [Contexto del Proyecto](contexto_proyecto.md) | Objetivos, alcance funcional, stack tecnológico, requisitos de hardware y modelos locales. |
| [Planificación y Arquitectura](planificacion_y_arquitectura.md) | Diseño desacoplado, inmutabilidad, chunking semántico, prevención de mojibakes y mitigación de errores en PowerShell. |
| [Especificación TDD y Pruebas](especificacion_tdd_y_pruebas.md) | Suite de pruebas unitarias e integración (12 tests, 83% cobertura), mocks con `respx` y auditoría de fallos silenciosos. |
| [Guía Operativa y Manual de Uso](guia_operativa.md) | Comandos para Windows 10 PowerShell, flags de CLI, configuración de Ollama, ledger de auditoría y troubleshooting. |

---

## 🛡️ Gobernanza y Mantenimiento

- **Harness `/ECC`:** El núcleo del harness Everything Claude Code es **intocable e ineditable**, actuando como árbitro metodológico estricto.
- **Control de Progreso (`ai-harness/`):** Todo el seguimiento evolutivo, checkpoints, historial de sesiones y estados de la cola de trabajo se registran formalmente en la ruta `ai-harness/progress/`.
