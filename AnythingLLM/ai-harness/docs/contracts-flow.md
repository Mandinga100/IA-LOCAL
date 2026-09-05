# Flujo de Contenido y Publicación — Asistente Integral 360

**Nota:** Este proyecto no tiene contratos ni flujo financiero. Este documento describe el workflow de contenido editorial.

---

## 1. Flujo de Creación de Contenido

```
Brief → Draft en progress/drafts/ → Revisión V1
  → Aprobación → Página en src/app/
  → SEO check → Build → Publicación
```

## 2. Tipos de Páginas

| Tipo | Ruta | Editor |
|:-----|:-----|:-------|
| Landing (home) | `/` | Código |
| Feature detail | `/features/[slug]/` | Código |
| Legal | `/(legal)/` | Código |
| Blog | `/blog/[slug]/` | Contenido (futuro) |

## 3. Checklist de Publicación

- [ ] Metadata completa (title, description, OG, Twitter)
- [ ] Structured data JSON-LD presente
- [ ] Ruta agregada al sitemap
- [ ] Build exitoso (`npm run build`)
- [ ] Sin 404s en rutas relacionadas
- [ ] Voz de marca consistente
- [ ] URLs con trailing slash

## 4. Control de Versiones

- Rama `main` — producción
- Rama `develop` — staging/pruebas
- Features en ramas separadas con merge a develop
- Commits descriptivos siguiendo conventional commits
