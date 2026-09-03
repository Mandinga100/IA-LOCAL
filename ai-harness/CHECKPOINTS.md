# Criterios de Aceptación y Checkpoints — Asistente Integral 360

> **DEPRECADO** — Este contenido ha sido migrado a `HARNESS.md §3.5` (Checklist de Integridad del Harness), `§3.7` (Post-verificación) y `§4` (Voz de marca).
> Este archivo se mantiene temporalmente para no romper enlaces históricos. No agregar nuevos items aquí.

## 1. Estructura y Gobernanza del Harness
- [ ] ¿El harness mantiene su estructura intacta sin archivos temporales en `ai-harness/`?
- [ ] ¿`work_queue.json` refleja el estado real de cada tarea?
- [ ] ¿Se registró el resumen en `progress/history.md` y se limpió `progress/current.md`?

## 2. Documentación y Flujo de Trabajo
- [ ] Para tareas medianas/altas: ¿Existe Brief y Plan en `progress/plans/`?
- [ ] Para tareas completadas: ¿Se generó reporte en `progress/reviews/`?
- [ ] ¿Los borradores se guardaron en `progress/drafts/`?
- [ ] ¿Los entregables definitivos se depositaron en `output/`?

## 3. Voz de Marca y Reglas
- [ ] ¿El cambio respeta la voz de marca (moderna, cercana, transparente)?
- [ ] ¿Se cumple con las reglas de negocio de `business-rules.md`?
- [ ] ¿Se evitó hardcodear secretos o modificar configs críticas sin aprobación?

## 4. SEO, AEO y LLMO
- [ ] ¿El contenido tiene estructura semántica H1-H3 y metadatos optimizados?
- [ ] ¿Se incluyeron FAQs estructuradas si aplica?
- [ ] ¿Answer-First en primer párrafo (< 200 caracteres)?

## 5. Calidad de Código
- [ ] ¿`npm run build` exitoso?
- [ ] ¿`npm run typecheck` sin errores?
- [ ] ¿`npm run lint` sin errores?
- [ ] ¿El resultado es 100% accionable sin placeholders?
