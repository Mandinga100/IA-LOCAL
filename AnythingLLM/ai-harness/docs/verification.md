# Protocolo de Verificación y Control de Calidad — Plataforma IA Local & AnythingLLM

**Última actualización:** 2026-09-03  
**Versión:** 1.0.0 (Consolidación Monorepo)  
**Gobernanza:** Enterprise Coding Constitution (ECC v2.0.0)

---

## 1. Niveles de Verificación del Sistema

| Nivel | Ámbito de Aplicación | Mecanismo de Validación | Responsable |
|:------|:---------------------|:------------------------|:------------|
| **V1 — Verificación Automatizada** | Código fuente, refactorizaciones, endpoints FastAPI, pipeline de documentos. | Suite completa de 176 tests con pytest (`pytest tests/ -v`). Verificación de tipos y linting. | Agente IA ejecutor / CI |
| **V2 — Verificación de Integración & Paridad** | Scripts `.ps1` y `.sh`, configuración de AnythingLLM, Dashboard 360°, Docker. | Validación cruzada en entornos Windows 10 y Linux. Prueba de carga y simetría de scripts. | Lead Architect / Senior Developer |
| **V3 — Autorización Criptográfica CEO** | Modificaciones al marco rector `ECC/` o `ai-harness/ecc/`. | Validación de hash SHA-256 mediante `core/ecc_guard.py` con token secreto de autorización. | CEO / Autoridad de Gobernanza |

---

## 2. Checklist de Verificación de Código (Nivel V1)

- [ ] **Tests Automatizados:** Ejecución de `pytest tests/` con 100% de tests activos en verde (Línea base: 175 pasados, 1 skipped).
- [ ] **Cobertura TDD:** Cobertura de código superior al 80% medida con `pytest --cov=core --cov=server`.
- [ ] **Manejo de Errores:** Cero `except: pass` o bloques `try/except` que silencien excepciones sin loguear.
- [ ] **Inmutabilidad:** Verificación de que los documentos fuente nunca son sobrescritos.
- [ ] **Tipado Estricto:** Código Python con anotaciones de tipo válidas y sin advertencias críticas.
- [ ] **Codificación:** Archivos guardados en UTF-8 sin BOM (prevención de mojibakes).

---

## 3. Checklist de Verificación de Infraestructura y Scripts (Nivel V2)

- [ ] **Simetría Multiplataforma:** Todo script nuevo en `Base/scripts/*.ps1` cuenta con su correspondiente `Base/scripts/*.sh`.
- [ ] **Sintaxis PowerShell:** Comandos nativos utilizados (`Invoke-RestMethod`), rutas entre comillas dobles, variables de entorno correctamente leídas.
- [ ] **Sintaxis Bash:** Shebang `#!/usr/bin/env bash`, modo `set -euo pipefail`, compatibilidad probada con Ubuntu 22.04 / 24.04.
- [ ] **Dashboard 360°:** Endpoint `/api/telemetria/360` responde HTTP 200 con payload JSON válido de CPU, RAM, VRAM y estado de Ollama.
- [ ] **Zero-Chatter AnythingLLM:** Endpoints compatibles con OpenAI `/v1/chat/completions` devuelven respuestas limpias y estructuradas sin texto conversacional no solicitado.

---

## 4. Protocolo de Modificación de Gobernanza (Nivel V3)

Toda modificación a las carpetas `/ECC` o `ai-harness/ecc/` requiere seguir el protocolo:
1. Generación de solicitud formal detallando motivo y archivos a alterar.
2. Generación del token de autorización único.
3. Validación criptográfica mediante `python -m core.ecc_guard --token <TOKEN> --verify`.
4. Solo si el hash SHA-256 coincide con el secreto autorizado por el CEO se desbloquea la escritura.
5. Registro de la modificación en `ai-harness/progress/history.md`.

---

## 5. Protocolo de Cierre de Tareas (Post-Verificación)

Al completar cualquier tarea o hito:
1. Actualizar el estado de la tarea en `ai-harness/work_queue.json` a `"status": "done"`.
2. Registrar los resultados detallados y métricas en `ai-harness/progress/history.md`.
3. Actualizar `ai-harness/progress/current.md` con el estado activo.
4. Generar el reporte de revisión correspondiente en `ai-harness/progress/reviews/` si se trata de un hito mayor.
