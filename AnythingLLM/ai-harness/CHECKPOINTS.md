# Criterios de Aceptación y Checkpoints — Plataforma IA Local & AnythingLLM Orchestrator

**Versión:** 1.0.0 (Consolidación Monorepo)  
**Gobernanza:** Enterprise Coding Constitution (ECC v2.0.0)

---

## 1. Integridad y Gobernanza del Harness
- [ ] ¿El harness mantiene su estructura intacta sin archivos residuales o temporales en `ai-harness/`?
- [ ] ¿`work_queue.json` refleja con exactitud el estado actual (`done`, `in-progress`, `pending`) de todas las tareas?
- [ ] ¿Se registró el resumen en `progress/history.md` y se actualizó `progress/current.md`?
- [ ] ¿Se preservaron inmutables las carpetas `/ECC` y `ai-harness/ecc/` bajo el guardia criptográfico SHA-256 (`core/ecc_guard.py`)?

## 2. Calidad de Código y TDD (Línea Base: 176 Tests)
- [ ] ¿Se ejecutó la suite completa de tests automatizados (`pytest tests/ -v`)?
- [ ] ¿100% de los tests activos están en verde (175 pasados, 1 skipped)?
- [ ] ¿La cobertura de código se mantiene >= 80%?
- [ ] ¿Se evitó terminantemente cualquier excepción silenciosa (`except: pass`)?
- [ ] ¿El código cuenta con tipado estricto mediante type hints y modelos inmutables?

## 3. Simetría Multiplataforma (Windows & Linux)
- [ ] ¿Todo nuevo script de automatización cuenta con su versión Windows (`.ps1`) y Linux (`.sh`)?
- [ ] ¿Los scripts de PowerShell utilizan sintaxis nativa (`Invoke-RestMethod`) y comillas para rutas con espacios?
- [ ] ¿Los scripts de Bash incluyen `#!/usr/bin/env bash` y `set -euo pipefail`?
- [ ] ¿Se garantiza la codificación UTF-8 sin BOM en todos los flujos de lectura/escritura?

## 4. Arquitectura del Pipeline e Integración
- [ ] ¿Los documentos fuente originales se mantienen estrictamente inmutables?
- [ ] ¿Las salidas procesadas se depositan únicamente en `output/` con hash SHA-256 asociado?
- [ ] ¿Las respuestas hacia AnythingLLM cumplen con la pureza Zero-Chatter (cero preámbulos conversacionales)?
- [ ] ¿El endpoint de telemetría `/api/telemetria/360` responde en tiempo real con datos verídicos de CPU/RAM/VRAM?

## 5. UI/UX Dashboard 360°
- [ ] ¿El Dashboard Visual 360° (`Base/web/`) mantiene cero estilos inline (`style="..."`)?
- [ ] ¿Las 5 pestañas modulares (Telemetría, Documentos, AnythingLLM, Gobernanza, Consola) son plenamente navegables?
- [ ] ¿El diseño visual sigue una estética oscura corporativa de alto impacto visual sin marcas de terceros no deseadas?
