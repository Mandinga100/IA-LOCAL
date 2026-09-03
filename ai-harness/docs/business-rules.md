# Reglas de Negocio — Asistente Integral 360

**Propósito:** Marco normativo para agentes IA y humanos sobre las reglas operativas del proyecto.

---

## 0. Reglas del Runtime Harness (Multi-Tenant)

| ID | Regla | Severidad |
|:---|:------|:----------|
| HR01 | **Cadencia obligatoria:** Toda operación crítica debe pasar por `initializeHarness()` antes de ejecutarse. | **Obligatorio** |
| HR02 | **Aislamiento por tenant:** Todo `DataRecord` debe contener `tenantId` válido. No permitir escrituras sin tenantId. | **Obligatorio** |
| HR03 | **Sin lecturas cruzadas:** Un tenant no puede leer datos de otro sin permisos explícitos. | **Obligatorio** |
| HR04 | **Separación de entornos:** `development`, `staging` y `production` deben operar con configuraciones independientes. | **Obligatorio** |
| HR05 | **La UI no decide permisos:** Los permisos se resuelven en el harness, no en componentes React. | **Obligatorio** |
| HR06 | **Auditoría obligatoria:** Toda operación de escritura/eliminación debe registrar un `AuditEvent`. | **Obligatorio** |
| HR07 | **Feature flags rigen funcionalidad:** No activar funcionalidad sin verificar su flag primero vía `guardFeatureFlag()`. | **Obligatorio** |
| HR08 | **Validación de esquema antes de persistir:** Usar `validateSchema()` con campos requeridos y permitidos. | **Obligatorio** |
| HR09 | **Sin datos sensibles en localStorage de auditoría:** Audit events pueden persistirse localmente pero sin PII. | **Obligatorio** |
| HR10 | **Contrato de datos único:** Todo registro usa `DataRecord` (`tenantId`, `environment`, `origin`, `version`, `createdAt`, `updatedAt`, `status`, `metadata`). | **Obligatorio** |

## 1. Reglas de Contenido y Landing Page

| ID | Regla | Severidad |
|:---|:------|:----------|
| LP01 | **Idioma único:** Todo el contenido debe estar en español (es-ES/es-CL). Sin contenido en otros idiomas. | **Obligatorio** |
| LP02 | **Dark mode:** El sitio solo soporta modo oscuro. No implementar toggle light/dark. | **Obligatorio** |
| LP03 | **Voz de marca:** Tono moderno, cercano, transparente. Sin promesas financieras exageradas. | **Obligatorio** |
| LP04 | **Páginas legales:** Deben existir y estar accesibles: privacidad, cookies, términos de servicio. | **Obligatorio** |

## 2. Reglas de Early Access

| ID | Regla | Severidad |
|:---|:------|:----------|
| EA01 | **Validación doble:** Zod schema en cliente y servidor para email. | **Obligatorio** |
| EA02 | **Sin backend simulado:** `subscribeToEarlyAccess` actualmente es mock. No desplegar a producción sin conectar backend real. | **Obligatorio** |
| EA03 | **Sin duplicados:** Si se implementa backend, verificar email único antes de insertar. | **Obligatorio** |

## 3. Reglas de Seguridad

| ID | Regla | Severidad |
|:---|:------|:----------|
| SE01 | **Headers en firebase.json:** Todos los security headers deben configurarse en `firebase.json` (no en `next.config.ts` por static export). | **Obligatorio** |
| SE02 | **Sin secretos hardcodeados:** Usar variables de entorno (`.env`). | **Obligatorio** |
| SE03 | **CSP obligatoria:** Content-Security-Policy debe estar activa en producción. | **Obligatorio** |
| SE04 | **Rate limiting:** El formulario de early access debe tener protección anti-spam. | **Recomendado** |

## 4. Reglas de SEO y Contenido

| ID | Regla | Severidad |
|:---|:------|:----------|
| CO01 | **Metadata única:** Cada página debe tener título y descripción propios (via `generateSEOMetadata()` o metadata export). | **Obligatorio** |
| CO02 | **Sitemap sincronizado:** Toda ruta en sitemap debe tener página real. Sin rutas huérfanas. | **Obligatorio** |
| CO03 | **FAQ estructuradas:** Incluir FAQPage schema con respuestas < 200 caracteres. | **Recomendado** |
| CO04 | **llms.txt:** Mantener actualizado en `/public/llms.txt`. | **Recomendado** |

## 5. Reglas de Código

| ID | Regla | Severidad |
|:---|:------|:----------|
| CX01 | **Build sin errores:** `npm run build` y `npm run typecheck` deben pasar antes de commits. | **Obligatorio** |
| CX02 | **Lint sin errores:** `npm run lint` sin errores (warnings permitidos). | **Obligatorio** |
| CX03 | **Sin estilos inline:** Prohibido `style="..."` en JSX. | **Obligatorio** |
| CX04 | **Server components default:** Solo usar `'use client'` cuando sea necesario. | **Obligatorio** |

## 6. Casos Prohibidos para Agentes

| ID | Acción Prohibida |
|:---|:-----------------|
| BAN01 | Hardcodear API keys o tokens en código fuente |
| BAN02 | Desplegar a producción sin validar build |
| BAN03 | Modificar `firebase.json` sin verificar security headers |
| BAN04 | Agregar páginas al sitemap sin implementarlas |
| BAN05 | Usar estilos inline en componentes |
| BAN06 | Introducir contenido en inglés |
| BAN07 | Simular backend como solución permanente a early access |
