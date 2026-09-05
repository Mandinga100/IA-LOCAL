# Convenciones y Estándares de Ingeniería — Plataforma IA Local & AnythingLLM

**Última actualización:** 2026-09-03  
**Versión:** 1.0.0 (Consolidación Monorepo)  
**Gobernanza:** Enterprise Coding Constitution (ECC v2.0.0)

---

## 1. Estándares de Código Python (`Base/`)

- **Versión de Python:** Compatible con Python >= 3.10 y optimizado para 3.13.
- **Tipado Estricto:** Uso obligatorio de `type hints` en todas las funciones y métodos públicos.
- **Inmutabilidad:** Las estructuras de datos de transferencia interna deben usar `@dataclass(frozen=True)` o modelos de `Pydantic v2` inmutables.
- **Manejo de Excepciones:** Definir excepciones de dominio específicas heredando de una base común (`PlataformaIAError`). Prohibido `except Exception: pass`.
- **Estructura de Imports:**
  1. Librerías estándar de Python (`os`, `sys`, `pathlib`, `typing`, `json`, `hashlib`).
  2. Dependencias de terceros (`fastapi`, `pydantic`, `httpx`, `markitdown`, `docx`).
  3. Módulos internos del proyecto (`from core... import ...`).
- **Codificación:** Todo archivo debe ser UTF-8 sin BOM.

---

## 2. Convenciones de Scripts y Automatización (`Base/scripts/`)

- **Doble Implementación Obligatoria:** Todo script debe existir en versión Windows PowerShell (`.ps1`) y versión Linux Bash (`.sh`).
- **PowerShell (Windows 10/11):**
  - Uso de comandos nativos de PowerShell: `Invoke-RestMethod` en lugar de `curl.exe`, `Test-Path`, `Get-Content`, `Set-Item`.
  - Rutas con espacios siempre entre comillas dobles: `"$PSScriptRoot\..\config"`.
  - Manejo de codificación de salida forzado: `$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8`.
- **Bash (Linux Ubuntu / Debian):**
  - Shebang estándar: `#!/usr/bin/env bash`.
  - Modo estricto obligatorio al inicio: `set -euo pipefail`.
  - Detección de ruta base: `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`.

---

## 3. Estándares del Frontend Dashboard 360° (`Base/web/`)

- **Tecnología:** Vanilla HTML5 semántico, Vanilla CSS3 y JavaScript moderno ES6+.
- **Sin Build Overhead:** No requiere Webpack, Vite ni compiladores en runtime para el dashboard del backend. Debe servirse de forma directa y eficiente por FastAPI.
- **Estilos:**
  - Cero estilos inline (`style="..."`).
  - Todas las variables de color, tipografía y espaciado centralizadas en `:root` dentro de `css/styles.css`.
  - Diseño responsive mediante Flexbox y CSS Grid.
  - Micro-interacciones sutiles en hover y transiciones suaves (`cubic-bezier(0.4, 0, 0.2, 1)`).
- **Consumo de APIs:** Uso de `fetch()` asíncrono con manejo de errores visual en pantalla (badges de estado y alertas).

---

## 4. Estándares de Documentación y Enlaces

- **Formato de Enlaces:** Enlaces tipo GitHub markdown con esquema `file:///` y barras inclinadas (`/`) hacia adelante para interoperabilidad Windows/Linux.
- **Jerarquía Semántica:** Un único `<h1>` por documento, seguido de una progresión coherente `<h2>` -> `<h3>`.
- **Trazabilidad:** Cada documento debe indicar su fecha de actualización, versión y estado.
- **Cero Placeholders:** Prohibido dejar textos de relleno, comentarios `[TODO]` sin planificar o mocks ficticios en producción.

---

## 5. Directiva de Comportamiento del Super Agente IA

- **Memoria de Plataforma:** Invariablemente confirmar al inicio de cada interacción: `✅ Windows 10 64-bit memoria activa.`
- **Máxima Brevedad y Concisión:** Respuestas directas, 0% relleno, 100% accionables, enfocadas en la ejecución del trabajo.
- **Pipeline de Procesamiento:** Seguir la estructura metodológica:
  `[MEMORIA]`, `[ROLES]`, `[ETAPA X]`, `[VERIFICACIÓN]`, `[SOLUCIÓN FINAL]`.
- **Blindaje ECC:** Reconocimiento de la autoridad inmutable de `ECC/` y `ai-harness/ecc/`, requiriendo autorización criptográfica SHA-256 para cualquier modificación en esos directorios.
