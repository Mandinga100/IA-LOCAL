# Arquitectura del Proyecto — Asistente Integral 360

**Última actualización:** 2026-07-01

---

## 1. Arquitectura General

El proyecto opera con dos capas de harness que NO se duplican sino que se complementan:

| Capa | Ubicación | Propósito |
|:-----|:----------|:----------|
| **Governance Harness** | `ai-harness/` | Documentación, reglas de negocio, work queue, checkpoints, sesiones — gobierna a los agentes IA |
| **Runtime Harness** | `src/harness/` | Código TypeScript ejecutable — resuelve tenant, entorno, permisos, flags, auditoría en runtime |

El Governance Harness es la **especificación**; el Runtime Harness es la **implementación**.

### Orden de Ejecución del Runtime Harness

```
1. resolveEnvironment()    → development | staging | production
2. resolveTenant()         → carga configuración del tenant
3. validateIdentity()      → autenticación (si aplica)
4. resolvePermissions()    → permisos según rol
5. resolveFlags()          → feature flags por tenant/entorno
6. validateSchema()        → contrato de datos
7. guard*()                → bloquea operaciones inseguras
8. registerAuditEvent()    → registra todo evento crítico
9. initializeHarness()     → entry point unificado
```

## 2. Stack Tecnológico

| Capa | Tecnología | Versión | Uso |
|:-----|:-----------|:--------|:----|
| Frontend | Next.js App Router | 15.3.3 | Static export, rutas públicas |
| Lenguaje | TypeScript | 5 | Tipado estricto |
| Estilos | Tailwind CSS | 3.4.1 | Utility-first, dark mode |
| UI Base | shadcn/ui + Radix | — | 35 componentes accesibles |
| Gráficos | Recharts | 2.15.1 | Dashboard interactivo |
| Formularios | React Hook Form + Zod | 7.x / 3.x | Validación cliente/servidor |
| IA | Google Genkit | 1.14.1 | Gemini 2.0 Flash (pending) |
| Hosting | Firebase Hosting | — | CDN, estático |
| BD | Firebase Data Connect | — | PostgreSQL (pendiente) |

## 2. Mapa de Rutas

| Ruta | Archivo | Propósito |
|:-----|:--------|:----------|
| `/` | `src/app/page.tsx` | Home: Hero, Features, Early Access, Security, Footer |
| `/features/gestion-de-gastos/` | `src/app/features/gestion-de-gastos/page.tsx` | Feature detail |
| `/features/pagos-recurrentes/` | `src/app/features/pagos-recurrentes/page.tsx` | Feature detail (con SEO metadata) |
| `/features/gastos-comunes/` | `src/app/features/gastos-comunes/page.tsx` | Feature detail |
| `/features/asistente-personal/` | `src/app/features/asistente-personal/page.tsx` | Feature detail |
| `/features/monitor-de-precios/` | `src/app/features/monitor-de-precios/page.tsx` | Feature detail |
| `/features/listas-de-compras-inteligentes/` | `src/app/features/listas-de-compras-inteligentes/page.tsx` | Feature detail |
| `/privacy-policy/` | `src/app/privacy-policy/page.tsx` | Aviso de privacidad |
| `/cookie-policy/` | `src/app/cookie-policy/page.tsx` | Política de cookies |
| `/terms-of-service/` | `src/app/terms-of-service/page.tsx` | Términos de servicio |
| `/sitemap.xml` | `src/app/sitemap.ts` | Sitemap dinámico |

### Rutas en sitemap SIN implementar (generan 404)
`/features/alertas-inteligentes`, `/features/reportes-avanzados`, `/features/asistente-ia`, `/features/seguridad-avanzada`, `/security`

## 3. Componentes

### Landing (13)
`header`, `hero-section`, `features-section`, `feature-card`, `security-section`, `early-access-section`, `early-access-form`, `footer`, `fade-in`, `cookie-banner`, `interactive-dashboard`, `neuronal-background`, `social-share`

### SEO (3)
`structured-data` (JSON-LD: WebSite, Organization, SoftwareApplication, Article), `seo-head` (metadata helper), `breadcrumbs`

### UI (35)
shadcn/ui: accordion, alert-dialog, button, card, carousel, chart, dialog, dropdown-menu, form, sheet, sidebar, tabs, toast, etc.

## 4. Server Action (único endpoint)

**`subscribeToEarlyAccess(prevState, formData)`** en `src/app/actions.ts`
- Validación Zod (email)
- Simula envío con `setTimeout` + `console.warn`
- **Sin backend real** — pendiente conectar a Firebase/email service

## 5. IA / Genkit

| Archivo | Propósito | Estado |
|:--------|:----------|:-------|
| `src/ai/genkit.ts` | Instancia de Genkit con plugin Google AI | Configurado |
| `src/ai/dev.ts` | Placeholder para flujos | Sin implementar |

## 6. Firebase

| Servicio | Estado |
|:---------|:-------|
| Hosting | Configurado — static export a `out/` |
| Data Connect | Schema/Query/Mutation todo comentado |
| Auth | No implementado |
| Firestore Rules | No definidas |

## 7. Flujo de Datos: Early Access

```
Usuario → Hero/Footer → EarlyAccessSection
  → EarlyAccessForm (cliente: validación Zod)
  → subscribeToEarlyAccess (server action: validación Zod)
  → console.warn + setTimeout (SIMULACIÓN)
  → Mensaje de éxito/error al usuario
```

## 8. Runtime Harness (`src/harness/`)

### Módulos

| Archivo | Responsabilidad |
|:--------|:----------------|
| `types.ts` | Tipos compartidos: Environment, Tenant, User, Role, Permission, DataRecord, AuditEvent, HarnessContext |
| `env.ts` | Resuelve entorno por hostname (development/staging/production) |
| `tenant.ts` | Resuelve tenant por ID; registro de nuevos tenants |
| `config.ts` | Carga config pública/privada del tenant; runtime config para UI |
| `auth.ts` | Valida identidad de usuario (id, email, tenantId, role) |
| `permissions.ts` | Resuelve permisos según rol; jerarquía owner→admin→member→viewer |
| `flags.ts` | Feature flags por tenant y entorno con override support |
| `validate.ts` | Validación de esquemas, construcción de DataRecord, aislamiento tenant |
| `audit.ts` | Registro de eventos críticos con persistencia local |
| `guards.ts` | Guards compuestos: permiso + feature flag + aislamiento tenant + entorno |
| `index.ts` | `initializeHarness()` — entry point que ejecuta la cadena completa |

### Contrato de Datos

Todo registro persistido debe implementar `DataRecord`:
- `tenantId`, `environment`, `origin`, `version`, `createdAt`, `updatedAt`, `status`, `metadata`

### Principio de Diseño

- La UI nunca decide permisos ni persistencia.
- Toda operación crítica pasa por `initializeHarness()` + guards.
- La landing se ve simple por fuera, pero opera como plataforma modular y segura por dentro.

## 9. Seguridad

- Security headers en `next.config.ts`: **COMENTADOS** (no aplican en static export)
- `firebase.json`: Sin headers configurados
- Suite automation: GitHub Action diario + script local `security-check.js`
- Validación Zod en formularios
- Sin autenticación, sin rate limiting, sin CSP activa
