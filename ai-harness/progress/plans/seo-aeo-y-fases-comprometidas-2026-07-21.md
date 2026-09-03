# Plan de ejecución — SEO/AEO alto impacto, fases comprometidas y arquitectura

> **Origen:** Auditoría de próximos pasos del roadmap, sesión 2026-07-21 (verificada contra `src/` real, no solo contra documentación).
> **Alcance:** Todo lo posterior a los dos bloques ya resueltos aparte — EmailJS (pausado por decisión del cliente) y GA4/analytics (crítico, tratado como tarea independiente previa). Este plan cubre desde "Alto impacto SEO/AEO" hasta las oportunidades de arquitectura.
> **Para quién:** Handoff al harness (`opencode`) para ejecución vía agentes `tech-architect` / `content` / `design` / `qa` según corresponda. Cada bloque es una unidad ejecutable de forma independiente — no hay que hacerlas en una sola sesión.
> **Convención de referencia:** `ai-harness/docs/conventions.md` está desactualizado (habla de Next.js/Tailwind/paleta magenta de un proyecto anterior — ver hallazgo de deuda documental en `docs/governance/AUDIT_BACKLOG_2026-07-20.md#11`). Las convenciones reales de este proyecto son: React 19 + TS + Vite, CSS Modules (no Tailwind), paleta negro/dorado. Este plan sigue el código real, no `conventions.md`.

---

## Orden de ejecución recomendado

1. [SEO-1] Alt text de Galería — más rápido, cero dependencias externas
2. [SEO-2] Alt text de Hero — decisión de trade-off, sin dependencias externas
3. [ARQ-1] Auditoría sitemap/robots — rápido, sin dependencias
4. [FASE-7] Flip de cards de Servicios — ya comprometido con cliente, datos listos
5. [ARQ-2] Code-splitting de rutas — hacerlo *antes* de sumar `/cotizador`, no después
6. [FASE-8] Página `/cotizador` — ya comprometido con cliente
7. [SEO-3] AggregateRating en schema.org — bloqueado por datos reales del cliente
8. [SEO-4] Testimonios con comuna/fecha/servicio — bloqueado por datos reales del cliente
9. [ARQ-3] Suite de tests Vitest — transversal, ejecutar en paralelo o al cierre de cada bloque anterior

Los ítems 7 y 8 quedan al final no por baja prioridad sino porque **dependen de que el cliente entregue datos que no se pueden inventar** (comuna/fecha de testimonios, conteo real de reseñas). No bloquean el resto del plan — se puede avanzar en paralelo pidiéndolos.

---

## [SEO-1] Alt text de Galería — de caption a oración descriptiva

**Estado actual:** `src/components/Gallery/index.tsx:19` usa `alt={caption}`. Los captions en `src/data/content.ts` son de 2-3 palabras ("Velatorio íntimo"), pensados para mostrarse como leyenda visual, no como alt text.

**Por qué importa:** Google Images y los motores de respuesta con IA (AEO) indexan por `alt`, no por el caption visual. Un alt de 2-3 palabras es prácticamente inútil para SEO de imágenes.

**Enfoque técnico:** Separar el campo visual del campo semántico. Añadir un campo `altText` (oración completa, 8-15 palabras, describe la escena + contexto de marca) al tipo de dato de galería, sin tocar el `caption` que ya funciona visualmente.

**Tareas:**
1. Extender el tipo `GalleryImage` (o equivalente) en `src/types/index.ts` con `altText: string`.
2. En `src/data/content.ts`, agregar `altText` a cada entrada de galería (probablemente 9-10 imágenes). Redactar cada uno como oración completa: qué se ve + servicio + tono ceremonial. Ejemplo: `"Velatorio íntimo para mascotas con sala privada, flores y ambiente sereno — Funeraria Brunetti"`.
3. En `src/components/Gallery/index.tsx:19`, cambiar `alt={caption}` por `alt={altText}`.
4. Verificar visualmente que el caption (texto que ve el usuario) no cambia — solo el atributo HTML `alt`.

**Criterios de aceptación:**
- [ ] Las 9-10 imágenes de galería tienen `altText` distinto de `caption`, con oración completa
- [ ] El caption visible en el overlay de hover no cambió
- [ ] `npm run build` y `npm run lint` en verde

**Esfuerzo:** 1-2 horas (copywriting + cambio de tipo). **Dependencias:** ninguna — se puede redactar sin esperar al cliente, aunque idealmente se valida el copy contra `docs/BRAND_IDENTITY_360.md` antes de mergear.

**Archivos:** `src/types/index.ts`, `src/data/content.ts`, `src/components/Gallery/index.tsx`.

---

## [SEO-2] Alt text indexable en Hero (decisión de trade-off)

**Estado actual:** `src/components/HeroCarousel/styles.module.css` implementa las 7 slides como `background-image` en CSS (`background-size: cover`, `background-position: center`). Cero elementos `<img>` en el DOM → cero alt text indexable para Google Images/IA visual.

**Por qué no es un fix trivial:** El carrusel actual depende de `background-image` para lograr el efecto de crossfade suave entre slides (probablemente vía opacidad de capas superpuestas). Migrar a `<img>` real puede introducir problemas de layout/timing en la animación si no se hace con cuidado.

**Dos opciones — decidir antes de implementar:**

| Opción | Cómo | Pro | Contra |
|---|---|---|---|
| **A. Migrar a `<img>` real** | Cada slide pasa a ser un `<img>` posicionado `absolute` con `object-fit: cover`, la transición de opacidad se aplica al `<img>` en vez de al `background-image` del div | Alt text real, mejor para accesibilidad y `loading="lazy"`/`fetchpriority` nativos | Requiere retocar el CSS de crossfade y probar que la animación Ken Burns/transición siga igual de fluida |
| **B. Mantener `background-image` + accesibilidad ARIA** | Agregar `role="img"` y `aria-label` descriptivo a cada slide `<div>` | Cero riesgo de romper la animación actual | No indexa en Google Images (Google no lee `aria-label` como alt de imagen para Images/AEO, solo para lectores de pantalla) |

**Recomendación:** Opción A. El valor SEO/AEO de que Google indexe las imágenes del hero (la sección más vista del sitio) supera el riesgo de retocar el CSS, siempre que se pruebe bien la animación después. La opción B resuelve accesibilidad pero no el problema SEO que originó el hallazgo.

**Tareas (asumiendo opción A):**
1. Revisar `src/components/HeroCarousel/index.tsx` y `styles.module.css` para entender el mecanismo de crossfade actual (probablemente clases `.active`/`.prev` con `opacity` + `transition`).
2. Reemplazar cada slide-`div` con `background-image` por un `<img src=... alt=... />` dentro del mismo contenedor, con `position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;`.
3. Migrar la transición de opacidad/Ken Burns del `background-image` al `<img>` (mismas clases, mismo timing).
4. Redactar `alt` por slide en `src/data/carousel.ts` — oración descriptiva por imagen (mismo criterio que SEO-1).
5. Probar en navegador: crossfade sigue fluido, sin parpadeos ni salto de layout (CLS).
6. Verificar `loading="eager"` + `fetchpriority="high"` solo en la primera slide (LCP), el resto `loading="lazy"`.

**Criterios de aceptación:**
- [ ] 7 slides con `<img>` real y `alt` descriptivo único
- [ ] Animación de crossfade visualmente idéntica a la actual (verificar en navegador, no solo en código)
- [ ] Sin regresión de CLS/LCP (verificar con Lighthouse — coordinar con ARQ-1 si aún no hay baseline)
- [ ] `npm run build`, `npm run lint`, `tsc --noEmit` en verde

**Esfuerzo:** 3-4 horas (incluye pruebas visuales de la animación). **Dependencias:** ninguna técnica; sí requiere aprobación de que el trade-off (opción A vs B) es el correcto antes de tocar el CSS del hero, que es visualmente sensible.

**Archivos:** `src/components/HeroCarousel/index.tsx`, `src/components/HeroCarousel/styles.module.css`, `src/data/carousel.ts`.

---

## [ARQ-1] Auditoría y refuerzo de sitemap.xml / robots.txt

**Estado actual:** `public/sitemap.xml` solo tiene 2 URLs (`/` y `/precios`) con `<lastmod>` hardcodeado a mano. `robots.txt` y `site.webmanifest` existen pero no fueron auditados en detalle.

**Por qué importa ahora:** Es barato hoy (2 rutas) y se vuelve más trabajoso después de sumar `/cotizador` (FASE-8) o un blog (Fase 2 del roadmap). Mejor resolver el patrón ahora que agregar URLs a mano cada vez.

**Tareas:**
1. Revisar `public/robots.txt` — confirmar que apunta al sitemap correcto y no bloquea rutas que deberían indexarse.
2. Decidir: ¿el `sitemap.xml` se sigue manteniendo a mano (aceptable con 2-4 rutas) o se automatiza su generación en el build (`vite-plugin-sitemap` o script propio en `scripts/`)? Recomendado: automatizar ahora que se sabe que vienen más rutas (`/cotizador`, posible blog), para no repetir este hallazgo cada vez que se agregue una página.
3. Si se automatiza: generar `<lastmod>` desde la fecha de build o desde `git log` del archivo de cada página, no hardcodeado.
4. Revisar `site.webmanifest` — íconos, colores de tema (`theme_color`) coherentes con la paleta negro/dorado.

**Criterios de aceptación:**
- [ ] `robots.txt` verificado sin bloqueos incorrectos
- [ ] Sitemap con estrategia clara (manual documentado en `docs/conventions.md` propio del proyecto, o automatizado)
- [ ] `site.webmanifest` con íconos y colores correctos

**Esfuerzo:** 1-2 horas. **Dependencias:** ninguna.

**Archivos:** `public/robots.txt`, `public/sitemap.xml`, `public/site.webmanifest`, posible nuevo `scripts/generate-sitemap.mjs`.

---

## [FASE-7] Flip en cards de Servicios (home) — comprometido con cliente

**Estado actual:** Verificado que `slugify` y `Service.priceFrom` ya existen en el modelo de datos (`src/data/content.ts` / `src/types/index.ts`) desde la Fase 1 de `/precios`. No requiere tocar el modelo de datos.

**Objetivo:** Cada card de servicio en Home voltea (flip 3D o crossfade, a definir con `design`) para mostrar un resumen breve de precio (o "Cotización personalizada" si no aplica precio fijo) + CTA que lleva a `/precios#[servicio-slug]`.

**Tareas:**
1. Confirmar con `design` el mecanismo visual del flip (CSS `transform: rotateY` con `perspective`, o crossfade más simple — evaluar performance en mobile).
2. Extender el componente de card de Servicios (`src/components/Services/`) con estado de hover/click que dispara el flip.
3. Cara trasera de la card: precio desde (`priceFrom`) o badge "Cotización personalizada", + botón CTA con `href="/precios#${slugify(service.title)}"`.
4. Verificar que los anchors (`id` en cada bloque de `/precios`) coinciden exactamente con el slug generado — ya deberían estar listos desde la Fase 1 de `/precios`, pero confirmar antes de dar por cerrado.
5. Accesibilidad: el flip no debe depender solo de `:hover` (mobile no tiene hover) — usar click/tap con `aria-expanded` o similar.

**Criterios de aceptación:**
- [ ] Las 9 cards de servicio voltean mostrando precio/CTA
- [ ] Funciona en mobile (tap, no solo hover)
- [ ] Los links de CTA aterrizan exactamente en el bloque correspondiente de `/precios`
- [ ] Sin regresión de performance perceptible (animación fluida en dispositivos de gama media)

**Esfuerzo:** 2-3 días (incluye diseño + implementación + pruebas cross-device). **Dependencias:** ninguna técnica — el modelo de datos ya está listo.

**Archivos:** `src/components/Services/*`, posible nuevo CSS de flip, `src/pages/Precios/index.tsx` (solo para confirmar anchors).

---

## [ARQ-2] Code-splitting de rutas — antes de sumar `/cotizador`

**Estado actual:** `src/App.tsx` importa `Home` y `Precios` de forma estática — ambas rutas viven en el mismo bundle JS pese a usar `react-router-dom`.

**Por qué ahora y no después:** Con 2 rutas el impacto es bajo, pero al sumar `/cotizador` (FASE-8) el bundle crece de nuevo. Es más barato meter `React.lazy` ahora, con 2 rutas simples de probar, que retrofitearlo después con 3 rutas y más superficie de regresión.

**Tareas:**
1. En `src/App.tsx`, reemplazar los imports estáticos de `Home` y `Precios` por `React.lazy(() => import('./pages/Home'))` / `React.lazy(() => import('./pages/Precios'))`.
2. Envolver `<Routes>` en `<Suspense fallback={...}>` con un fallback simple (spinner o skeleton coherente con la paleta negro/dorado, no un `"Cargando..."` genérico).
3. Verificar en build (`npm run build`) que se generan chunks separados por ruta (revisar output de Vite).
4. Probar navegación entre `/` y `/precios` en el navegador — sin parpadeos ni FOUC perceptible.

**Criterios de aceptación:**
- [ ] Bundle de `/precios` no se descarga al visitar `/`
- [ ] Fallback de `Suspense` visualmente coherente con la marca (no un loader genérico blanco)
- [ ] `npm run build` muestra chunks separados
- [ ] Navegación fluida entre rutas, sin regresión visible

**Esfuerzo:** 2-3 horas. **Dependencias:** ninguna — hacerlo antes de FASE-8 para que `/cotizador` nazca ya con lazy-loading.

**Archivos:** `src/App.tsx`.

---

## [FASE-8] Página `/cotizador` — comprometido con cliente

**Estado actual:** `priceAddons` y `cremationBasePrices` ya están modelados en `src/data/content.ts` para alimentar esta página sin cambios de modelo de datos (según hallazgo de auditoría 2026-07-20).

**Objetivo:** Ruta nueva (`/cotizador`) con selector interactivo: servicio + peso de la mascota + extras (domicilio/Parque de Asís, presencial, sacerdotal) → total calculado en vivo.

**Tareas:**
1. Confirmar con el código real (`src/data/content.ts`) la forma exacta de `priceAddons`/`cremationBasePrices` antes de diseñar el componente — no asumir la estructura sin releer el archivo actualizado, puede haber cambiado desde el hallazgo original.
2. Diseñar el flujo del selector: paso 1 (servicio) → paso 2 (peso, si aplica a cremación) → paso 3 (extras) → resultado.
3. Crear `src/pages/Cotizador/` siguiendo la misma estructura que `src/pages/Precios/` (CSS Modules, mismo patrón de layout).
4. Registrar la ruta en `src/App.tsx` (ya con `React.lazy`, ver ARQ-2).
5. Lógica de cálculo: función pura testeable (candidato ideal para el primer test de Vitest, ver ARQ-3) que reciba servicio+peso+extras y devuelva el total.
6. CTA final del cotizador: enviar el resultado como contexto precargado al formulario de contacto (`OrderModal`/`QuoteModal` ya soportan `preselectedService` — confirmar si soportan también extras/peso o si hay que extenderlos).
7. Agregar `/cotizador` a `public/sitemap.xml` (coordinürregir con ARQ-1 si ya se automatizó).

**Criterios de aceptación:**
- [ ] Selector completo funciona para las 6 combinaciones de precio de cremación + extras
- [ ] Total se recalcula en vivo sin errores de redondeo
- [ ] CTA final lleva el contexto (servicio elegido) al formulario de contacto
- [ ] Ruta en sitemap y con SEO propio (`SEOHead` con title/description específicos)
- [ ] Al menos 1 test unitario de la función de cálculo de precio (ver ARQ-3)

**Esfuerzo:** 4-6 días (incluye UI del selector, lógica de cálculo, integración con modales existentes, SEO de la página). **Dependencias:** ARQ-2 idealmente resuelto antes (para que la ruta nazca con lazy-loading); ninguna dependencia de datos externos del cliente.

**Archivos:** nuevo `src/pages/Cotizador/`, `src/App.tsx`, `public/sitemap.xml`, posible extensión de `OrderModal`/`QuoteModal`.

---

## [SEO-3] `AggregateRating` en schema.org — bloqueado por datos reales

**Estado actual:** `src/components/SEOHead/schema.ts` (55 líneas) hoy solo declara `LocalBusiness` + `makesOffer` (9 servicios). **No existe ningún `Review` ni `AggregateRating`** — es un hallazgo más severo de lo que decía la auditoría anterior, que asumía que había al menos un `Review` aislado.

**Por qué está bloqueado:** El sitio comunica "+500 familias acompañadas" en el copy, pero publicar un `ratingValue`/`reviewCount` sin respaldo real es manipulación de reseñas — exactamente lo que penaliza Google. Se necesita:
- Conteo real de reseñas (Google Business Profile, Meta, o donde el cliente las tenga)
- Promedio real de calificación

**Tareas (cuando el cliente entregue los datos):**
1. Pedir al cliente: link a Google Business Profile (o exportación) con conteo y promedio real de reseñas.
2. Extender `src/components/SEOHead/schema.ts` con bloque `AggregateRating` dentro del `LocalBusiness`:
   ```ts
   aggregateRating: {
     '@type': 'AggregateRating',
     ratingValue: <promedio real>,
     reviewCount: <conteo real>,
   }
   ```
3. Si el cliente puede compartir 3-5 reseñas textuales reales con nombre/fecha, agregar también `review: [...]` como array de `Review` individuales (no solo el agregado).
4. Validar el JSON-LD resultante con el [Rich Results Test de Google](https://search.google.com/test/rich-results) antes de mergear.

**Criterios de aceptación:**
- [ ] `ratingValue`/`reviewCount` respaldados por una fuente real citable (no inventados)
- [ ] JSON-LD válido en Rich Results Test
- [ ] Si se agregan `Review` individuales, cada uno con `author` y fecha reales

**Esfuerzo:** 1-2 horas de implementación una vez hay datos. **Dependencias:** 🔴 bloqueado por el cliente — no iniciar sin los datos reales.

**Archivos:** `src/components/SEOHead/schema.ts`.

---

## [SEO-4] Testimonios con comuna/fecha/servicio — bloqueado por datos reales

**Estado actual:** Confirmado en `src/data/content.ts:220-239` — 5 testimonios, cada uno solo con `quote` + `author` genérico (ej. `"— José T."`, `"— Familia Muñoz"`). Sin comuna, fecha ni tipo de servicio.

**Por qué importa:** Un testimonio con `"— Carolina M., Ñuñoa · Cremación individual, mayo 2026"` aporta mucho más E-E-A-T (Experience, Expertise, Authoritativeness, Trust) que un nombre suelto — tanto para SEO como para la confianza real del visitante.

**Tareas (cuando el cliente confirme los datos):**
1. Pedir al cliente, por cada uno de los 5 testimonios existentes: comuna de la familia, fecha aproximada del servicio, tipo de servicio contratado.
2. Extender el tipo de testimonio en `src/types/index.ts` con `comuna?: string`, `service?: string`, `date?: string`.
3. Actualizar `src/data/content.ts:220-239` con los datos reales.
4. Actualizar el componente que renderiza testimonios (`Trust` o donde vivan) para mostrar el formato ampliado: `"— {author}, {comuna} · {service}, {date}"`.
5. Si además se resuelve SEO-3 con `Review` individuales, reutilizar estos mismos datos ampliados en el schema.

**Criterios de aceptación:**
- [ ] Los 5 testimonios muestran comuna + servicio + fecha reales (no inventados)
- [ ] Si algún dato no se puede confirmar para un testimonio puntual, se omite ese campo en vez de inventarlo (no forzar consistencia falsa)

**Esfuerzo:** 1 hora de implementación una vez hay datos. **Dependencias:** 🔴 bloqueado por el cliente.

**Archivos:** `src/types/index.ts`, `src/data/content.ts`, componente `Trust` (o el que renderice testimonios).

---

## [ARQ-3] Suite de tests Vitest — transversal

**Estado actual:** Cero archivos `.test.*`/`.spec.*` en `src/`. Vitest no está instalado en `package.json`. Los tres documentos de roadmap (`ROADMAP_3FASES.md`, `PLANIFICACION_FASES.md`, `ai-harness/work_queue.json`) declaran "test-driven, 80%+ cobertura" como principio de ejecución, pero nunca se implementó.

**Enfoque recomendado:** No intentar 80% de cobertura de entrada — es un objetivo aspiracional que no se sostiene con cero tests hoy. Empezar por lo que tiene mayor retorno:
1. Setup de Vitest + React Testing Library (config base, sin tests todavía).
2. Primer test real: la función de cálculo de precio de FASE-8 (`/cotizador`) — es lógica pura, fácil de testear, y es exactamente donde un bug de cálculo le costaría dinero/confianza al cliente.
3. Segundo test: `formService.ts` — verificar que el honeypot filtra correctamente y que `templateParams` arma bien el payload (mockeando `emailjs.send`).
4. Tercer test: algún componente crítico de conversión (ej. `OrderModal` — que el submit dispare `submitForm` con los datos correctos).

**Tareas:**
1. `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom`
2. Config `vitest.config.ts` (o extender `vite.config.ts`) con entorno `jsdom`.
3. Script `"test": "vitest run"` en `package.json`.
4. Implementar los 3 tests descritos arriba (priorizar el de cálculo de precio si FASE-8 ya está en marcha).

**Criterios de aceptación:**
- [ ] `npm run test` corre y pasa en verde
- [ ] Al menos 3 tests: cálculo de precio, `formService`, un componente de conversión
- [ ] Config documentada (no hace falta 80% de cobertura para cerrar este ítem — eso es una meta continua, no un entregable único)

**Esfuerzo:** 1 día para el setup + 3 tests iniciales. **Dependencias:** el test de cálculo de precio depende de que FASE-8 exista; los otros dos no dependen de nada.

**Archivos:** `package.json`, nuevo `vitest.config.ts`, nuevos `*.test.ts(x)` junto a los archivos que testean.

---

## Resumen para el harness

| ID | Bloque | Prioridad | Esfuerzo | Bloqueado por cliente |
|---|---|---|---|---|
| SEO-1 | Alt text Galería | Alto | 1-2h | No |
| SEO-2 | Alt text Hero (migrar a `<img>`) | Alto | 3-4h | No |
| ARQ-1 | Sitemap/robots | Medio | 1-2h | No |
| FASE-7 | Flip cards Servicios | Comprometido | 2-3 días | No |
| ARQ-2 | Code-splitting rutas | Medio | 2-3h | No |
| FASE-8 | Página `/cotizador` | Comprometido | 4-6 días | No |
| SEO-3 | AggregateRating schema | Alto | 1-2h* | **Sí** |
| SEO-4 | Testimonios con metadata | Alto | 1h* | **Sí** |
| ARQ-3 | Suite Vitest | Medio | 1 día | No (parcial, ver nota) |

\* Esfuerzo de implementación una vez llegan los datos — no incluye el tiempo de espera al cliente.

**Acción inmediata sugerida:** pedirle al cliente en paralelo, sin bloquear el resto del plan, los datos de SEO-3 y SEO-4 (link a Google Business Profile + comuna/fecha/servicio de los 5 testimonios existentes), mientras el harness avanza con SEO-1 → SEO-2 → ARQ-1 → FASE-7 → ARQ-2 → FASE-8.

---

> **Alineado con:** `docs/governance/AUDIT_BACKLOG_2026-07-20.md`, `docs/ROADMAP_3FASES.md`, `docs/PLANIFICACION_FASES.md`, `ai-harness/work_queue.json`, estado real de `src/` verificado 2026-07-21.
