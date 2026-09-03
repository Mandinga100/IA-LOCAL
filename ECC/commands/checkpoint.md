---
description: Alias command — redirects to /save-session for richer, cross-session state capture.
---

# Checkpoint Command

> `/checkpoint` ha sido reemplazado por `/save-session`.

El sistema de sesiones (`save-session`/`resume-session`) ofrece una solución más completa:

| Capacidad | `/checkpoint` (anterior) | `/save-session` |
|---|---|---|
| Almacenamiento | Git SHA en `.claude/checkpoints.log` | Estado completo: tareas, blockers, decisiones, test status |
| Cross-session | No | Sí — con auto-resume |
| Automatización | Manual | Hooks `session-start.js` / `session-end.js` |
| Handler | Markdown instructivo (sin ejecutable) | 14 scripts JS con 2000+ líneas de código |
| Persistencia | Frágil (echo >> .log) | Archivos estructurados en `~/.claude/session-data/` |
| Rollback | Parcial (git stash) | Estado completo + contexto |

## Uso

```bash
/save-session          # Guarda estado actual
/resume-session        # Restaura sesión anterior
/sessions              # Lista, busca, administra sesiones
```

## Migración desde `/checkpoint`

Si usabas `/checkpoint create "nombre"`, ahora usa:

```bash
/save-session
```

Al retomar, `/resume-session` cargará automáticamente el último estado guardado, incluyendo cambios pendientes, blockers y contexto completo.

---

El comando `checkpoint` se mantiene en el catálogo Premium por compatibilidad, pero su funcionalidad está consolidada en el sistema de sesiones.
