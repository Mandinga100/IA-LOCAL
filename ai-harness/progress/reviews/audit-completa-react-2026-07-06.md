# Auditoría Completa — Proyecto React + TypeScript + Vite

**Fecha:** 2026-07-06
**Agente:** tech-architect
**Contexto:** Post-migración de HTML vanilla a React, corrección de mojibake (14 archivos)

---

## 1. Build & TypeScript

| Item | Estado | Detalle |
|------|--------|---------|
| `tsc --noEmit` | ✅ 0 errores | strict: true, skipLibCheck: true |
| `vite build` | ✅ Build exitoso | CSS 22.67 kB (gzip 4.48), JS 234.38 kB (gzip 73.59) |
| Dependencias instaladas | ✅ | React 19, react-helmet-async, Vite 8, TypeScript 6 |

## 2. Calidad de Código

| Item | Estado | Detalle |
|------|--------|---------|
| ESLint | ❌ No configurado | No existe `.eslintrc*` ni `eslint.config.*` |
| Prettier | ❌ No configurado | No existe `.prettierrc*` |
| Tests | ❌ No implementados | Sin Vitest, sin RTL |
| CSS Modules | ✅ | Todos los componentes usan CSS Modules scoped |
| Inline styles | ✅ 0 | Sin estilos en línea |
| `dangerouslySetInnerHTML` | ✅ 0 | Sin uso |
| Secrets hardcodeados | ✅ 0 | Solo placeholders ficticios |

## 3. Contenido (Mojibake)

| Item | Estado | Detalle |
|------|--------|---------|
| Caracteres mojibake (`Ã¡ Ã© Ã±` etc.) | ✅ 0 | En .tsx, .ts, .html |
| HTML entities (`&oacute;` etc.) | ✅ 0 | En .tsx, .ts |
| Unicode escapes para texto español | ✅ 0 | `\u00XX` eliminados |
| Unicode escapes para iconos | ⚠️ 16 | Legítimos (♡ ✨ ☰ etc.) |
| **Archivo corregido** | `SEOHead/index.tsx` | Mojibake en líneas 9, 44, 56, 66, 67 |

## 4. SEO & AEO

| Item | Estado | Detalle |
|------|--------|---------|
| `<h1>` único | ✅ | Hero/index.tsx:12 |
| Jerarquía h1→h2→h3 | ✅ | Correcta |
| Meta title + description | ✅ | SEOHead/index.tsx |
| Open Graph tags | ✅ | og:title, og:description, og:image, og:locale |
| Twitter cards | ✅ | summary_large_image |
| JSON-LD Schema | ✅ | LocalBusiness + FuneralHome |
| FAQPage Schema | ❌ Ausente | FAQ es accordion HTML pero sin structured data JSON-LD |
| Canonical URL | ✅ | `https://funerariabrunetti.cl` |
| robots.txt | ✅ | `/public/robots.txt` |
| Sitemap.xml | ❌ No generado | Sin sitemap |
| Answer-First content | ✅ | Hero subtitle < 200 caracteres |
| Google Fonts | ✅ | Playfair Display, Inter, Cormorant |

## 5. Identidad de Marca (AP-001)

| Item | Estado | Detalle |
|------|--------|---------|
| Estética negro/dorado | ✅ | variables.css: #000000, #C9A84C, #D4AF37 |
| Tono profesional/humano | ✅ | Sin infantilización, sin "pet shop" |
| Filtro "¿funeraria humana seria?" | ✅ | Pasa el filtro |

## 6. Funcionalidad

| Item | Estado | Detalle |
|------|--------|---------|
| WhatsApp link | ⚠️ Placeholder | `56999999999` (ficticio, user-requested) |
| Formulario Formspree | ⚠️ Placeholder | `yourFormID` (ficticio, user-requested) |
| Chatbox | ✅ | Derivación a WhatsApp por tipo |
| FAQ Accordion | ✅ | Estados open/close |
| Modal | ✅ | useModal hook |
| Cookie Notice | ✅ | useCookieConsent hook |
| Navegación mobile | ✅ | Hamburguer menu + Header |
| WhatsApp Float | ✅ | Botón flotante |

## 7. Imágenes y Assets

| Item | Estado | Detalle |
|------|--------|---------|
| Hero background | ❌ Ausente | Sin imagen en `/public/` |
| Gallery imágenes | ❌ Ausentes | Gallery usa solo iconos Unicode |
| Favicon | ✅ | `public/favicon.svg` — "B" dorado |
| site.webmanifest | ✅ | PWA básico |
| Alt text en imágenes | ⚠️ N/A | Sin imágenes todavía |

## 8. Rendimiento (estimado)

| Item | Estado | Detalle |
|------|--------|---------|
| Lighthouse real | ⏳ No ejecutado | Requiere dev server o deploy |
| Imágenes optimizadas | ❌ | Sin imágenes cargadas |
| Lazy loading | ❌ No configurado | Sin lazy en componentes |
| Core Web Vitals | ⏳ Sin medir | Pendiente |

## 9. Documentación y Gobernanza

| Item | Estado | Detalle |
|------|--------|---------|
| `opencode.json` | ❌ No existe | CANONICAL.md lo referencia pero no está |
| `.opencode/LOGS.md` | ❌ No existe | Debería estar en `.opencode/` |
| PATTERNS.md | ❌ Desactualizado | Referencia patrones vanilla JS (BEM, data-animate, Intersection Observer) |
| DECISIONS.md | ❌ Desactualizado | Dice "HTML+CSS+Vanilla JS (fase 1-2)" — ya se migró a React |
| work_queue.json | ⚠️ Parcialmente obsoleto | Tareas refieren a `brunetti-funeraria.html` (HTML legacy) |
| ERRORS.md | ✅ Existe | Vacío (no se registró error de mojibake) |
| progress/current.md | ✅ | Actualizado |
| progress/history.md | ✅ | Historial completo |

## 10. Checklist §3.2 HARNESS.md (V1 Documentación)

- [x] Enlaces relativos válidos (sin `file://`)
- [x] Sin placeholders (ficticios deliberados por instrucción)
- [x] Un solo `<h1>`, jerarquía correcta
- [x] Tono de marca consistente
- [x] Sin referencias a otros proyectos
- [ ] Sin duplicación documental — PATTERNS.md duplica patrones obsoletos

## 11. Checklist §3.3 HARNESS.md (V1/V2 Código)

- [x] Build exitoso
- [x] Typecheck sin errores
- [ ] Lint sin errores — ESLint no configurado
- [x] Sin secretos hardcodeados
- [x] Sin placeholders en producción (ficticios por solicitud)

## 12. Checklist §3.5 HARNESS.md (Integridad del Harness)

- [ ] work_queue.json desactualizado — referencias a brunetti-funeraria.html deben migrarse a src/ React
- [ ] No existe LOGS.md
- [x] progress/current.md refleja estado real
- [ ] PATTERNS.md no actualizado a React

---

## Score Global: 68/100

| Categoría | Peso | Puntos | Justificación |
|-----------|------|--------|---------------|
| Build/TypeCheck | 15 | 15 | Perfecto |
| Calidad de código | 15 | 7 | Sin ESLint, Prettier, tests |
| Contenido (mojibake) | 15 | 15 | Perfecto |
| SEO/AEO | 15 | 11 | Falta FAQPage schema, sitemap |
| Identidad de marca | 10 | 10 | Perfecto |
| Funcionalidad | 10 | 8 | Placeholders WhatsApp/Formspree |
| Imágenes | 5 | 1 | Sin imágenes reales |
| Rendimiento | 5 | 1 | Sin medición, sin lazy loading |
| Doc/Gobernanza | 10 | 5 | PATTERNS/DECISIONS desactualizados, falta opencode.json/LOGS.md |

## Hallazgos Prioritarios

### Críticos
1. **PATTERNS.md y DECISIONS.md desactualizados** — Contradicen la arquitectura React actual
2. **Falta opencode.json y LOGS.md** — El harness los requiere como canónicos

### Altos
3. **Sin FAQPage JSON-LD schema** — Google no indexa las FAQ como rich snippets
4. **Sin sitemap.xml** — Google no descubre todas las URLs
5. **Sin imágenes reales** — Hero y Gallery vacíos
6. **Sin ESLint/Prettier** — Riesgo de inconsistencia de código

### Medios
7. **work_queue.json desactualizado** — Tareas apuntan a HTML legacy
8. **Sin lazy loading** — Impacta rendimiento con imágenes futuras
9. **No registrar error mojibake en ERRORS.md** — Se perdió trazabilidad

### Bajos
10. **Sin tests** — Sin suite configurada en React
11. **Sin medición Lighthouse** — Sin baseline de rendimiento
