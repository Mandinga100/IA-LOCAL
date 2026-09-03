# Guía de Optimización SEO, AEO y LLMO — Asistente Integral 360

## 1. SEO Tradicional

### Público Objetivo
- Personas interesadas en finanzas personales
- Usuarios buscando apps de control de gastos
- Profesionales de 25-50 años, Chile y LATAM
- Keywords: "control de gastos app", "finanzas personales inteligentes", "asistente financiero IA"

### Metadata
- **Title template:** `%s | Asistente Integral 360`
- **Descripción:** Keywords primarias en primeros 160 caracteres
- **Open Graph:** OG image 1200x630, locale es_ES
- **Twitter Cards:** summary_large_image, @asistente360

### Structured Data (JSON-LD) — Implementado
- **WebSite:** name, description, SearchAction, publisher Organization
- **Organization:** logo, contactPoint (soporte@asistente360.com), sameAs (Twitter, LinkedIn, Facebook)
- **SoftwareApplication:** FinanceApplication, free offer, aggregateRating (4.8/5)

### Faltante por Implementar
- [ ] FAQPage schema (FAQ sección en homepage)
- [ ] LocalBusiness schema (cuando tenga presencia local)
- [ ] Sitio verificado en Google Search Console (placeholders actuales)

## 2. AEO (Answer Engine Optimization)

### Directrices
- **Answer-First:** Respuesta directa en primer párrafo de cada página (< 200 caracteres)
- **FAQ Clustering:** Incluir FAQPage schema con respuestas < 200 caracteres
- **Tablas HTML semánticas:** Datos comparables en tablas HTML, no imágenes

### Checklist por Página
- [ ] ¿El primer párrafo responde la intención de búsqueda?
- [ ] ¿Hay FAQ estructuradas con schema?
- [ ] ¿Los datos comparables están en tablas HTML?

## 3. LLMO (LLM Optimization)

### Directrices
- **`data-llmo-point="truth"`:** Secciones clave (beneficios, features, pricing) marcadas para parseo de IAs
- **`llms.txt`:** Archivo en `/public/llms.txt` con índice resumido para crawlers de IA
- **Contenido semántico:** Encabezados descriptivos, párrafos informativos

### Checklist
- [ ] `public/llms.txt` existe y está actualizado
- [ ] Secciones clave tienen `data-llmo-point="truth"`
- [ ] Cada página tiene un resumen ejecutivo legible por IA
- [ ] Datos financieros precisos (sin estimaciones de IA)

## 4. Sitemap y Robots

### Sitemap
- `src/app/sitemap.ts` — generación dinámica
- Prioridades: `/` (1.0), features (0.9), páginas legales (0.3)
- **Todas las rutas deben existir** — eliminar del sitemap si no hay página

### Robots.txt
- Permitir: Googlebot, Bingbot, YandexBot (con crawl-delay: 10)
- Bloquear: AhrefsBot, MJ12bot, DotBot
- Disallow: `/_next/`, `/api/`, `/.well-known/`, `/admin/`, `/private/`
- Link: sitemap.xml
