# Convenciones y Estándares — Asistente Integral 360

## Archivos y Rutas
- **Nombres de archivo:** kebab-case para recursos públicos, scripts y componentes (ej: `early-access-form.tsx`).
- **Separación:** Borradores en `progress/drafts/`, entregables finales en `output/`, código productivo en `src/`.

## Estándares de Código (Next.js & TypeScript)
- **Cero estilos inline:** Prohibido `style="..."` en JSX. Usar Tailwind CSS o CSS archivos externos.
- **Tipado estricto:** Tipos/interfaces explícitas. Evitar `any`. Usar `unknown` cuando sea necesario.
- **Server/Client:** Componentes server por defecto. `'use client'` solo cuando sea necesario (estado, efectos, event handlers).
- **Manejo de errores:** Envolver llamadas asíncronas en `try/catch`.

## Documentación y Redacción
- **Enlaces relativos:** Rutas Markdown relativas dentro del repo. Prohibido `file://`.
- **Estructura semántica:** Un `<h1>` por página. Jerarquía `<h2>` → `<h3>` lógica.
- **Idioma:** Todo el contenido en español (es-CL para moneda, es-ES para metadata).

## Seguridad
- **Variables de entorno:** Nunca hardcodear APIs, tokens o credenciales. Usar `.env`.
- **Validación:** Zod schemas para todo input de usuario (cliente y servidor).
- **Headers:** Configurar en `firebase.json` (no en `next.config.ts` para static export).

## Entorno (Windows / PowerShell)
- **Rutas con espacios:** Usar comillas dobles y barras invertidas.
- **Comandos nativos:** Usar sintaxis PowerShell (ej: `Invoke-RestMethod` en vez de `curl.exe`).

## Componentes
- **Props interface:** Definir interfaz explícita para cada componente. Exportar.
- **Variantes:** Usar `class-variance-authority` (CVA) para múltiples variantes.
- **Clases condicionales:** Usar `cn()` de `@/lib/utils` (clsx + tailwind-merge).

## Convenciones Específicas del Proyecto
- **Dark mode:** Solo modo oscuro. Clase `dark` en `<html>`.
- **Fuentes:** Manrope (body) + Orbitron (headlines) vía `next/font/google`.
- **Colores:** Paleta basada en magenta primario (#E040FB) sobre fondo navy oscuro.
- **Dashboard:** Datos simulados en componentes cliente. Pendiente conexión a API real.

## Interacción y Respuestas del Agente
- **Máxima brevedad:** Respuestas ultra-cortas, sin preámbulos ni relleno (0% paja, 100% accionables para avanzar en el trabajo).
- **Gobernanza persistente:** El harness `/ECC` es intocable e inmutable; TDD obligatorio; codificación UTF-8 en Windows 10; reglas activas para cualquier modelo de IA.
