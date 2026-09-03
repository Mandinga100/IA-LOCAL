# Protocolo de Verificación — Asistente Integral 360

> **DEPRECADO** — El contenido de este archivo es canónico en `HARNESS.md §3` (Verificación).
> Mantenido temporalmente para referencias históricas. No actualizar.

---

## 1. Niveles de Verificación

| Nivel | Cuándo se aplica | Quién valida |
|:------|:-----------------|:-------------|
| **V1 — Automático** | Documentación, contenido editorial, tareas de baja complejidad | El mismo agente ejecutor |
| **V2 — Revisión por pares** | Cambios en reglas de negocio, schemas, flujos críticos | Segundo agente o revisor humano |
| **V3 — Aprobación humana** | Security headers en firebase.json, despliegue a producción, cambios en autenticación | Supervisor humano |

## 2. Verificación de Documentación (V1)

- [ ] Enlaces relativos válidos (sin `file://`)
- [ ] Sin placeholders (`[TODO]`, lorem ipsum)
- [ ] Un solo `<h1>`, jerarquía correcta
- [ ] Tono técnico neutro
- [ ] Sin referencias a otros proyectos

## 3. Verificación de Código (V1/V2)

- [ ] `npm run build` exitoso
- [ ] `npm run typecheck` sin errores
- [ ] `npm run lint` sin errores
- [ ] Sin `style="..."` en JSX
- [ ] Sin `any` en TypeScript
- [ ] Server components default, `'use client'` justificado
- [ ] Zod validation en inputs de usuario
- [ ] Sin secretos hardcodeados

## 4. Verificación de Contenido SEO/AEO (V1)

- [ ] Answer-First en primer párrafo (< 200 caracteres)
- [ ] FAQPage schema presente (si aplica)
- [ ] Un solo `<h1>`, jerarquía correcta
- [ ] JSON-LD presente y válido
- [ ] Voz de marca consistente
- [ ] URL con trailing slash
- [ ] Ruta en sitemap con prioridad correcta
- [ ] robots.txt no bloquea crawlers en rutas públicas

## 5. Cambios Sensibles (V3 — Aprobación Humana)

| Cambio | Acción requerida |
|:-------|:-----------------|
| Modificar security headers en `firebase.json` | Propuesta escrita + aprobación |
| Despliegue a producción | Build verificado + aprobación |
| Conectar early access a backend real | Propuesta técnica + aprobación |
| Modificar variables de entorno o secretos | Propuesta escrita + aprobación |

## 6. Post-Verificación

- [ ] Actualizar `work_queue.json`
- [ ] Registrar resumen en `progress/history.md`
- [ ] Limpiar `progress/current.md`
- [ ] Mover entregables a `ai-harness/output/`
- [ ] Borradores en `progress/drafts/`
