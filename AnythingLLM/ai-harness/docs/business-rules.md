# Reglas de Negocio y Normas Operativas — Plataforma IA Local & AnythingLLM

**Última actualización:** 2026-09-03  
**Versión:** 1.0.0 (Consolidación Monorepo)  
**Marco Rector:** Enterprise Coding Constitution (ECC v2.0.0)

---

## 1. Reglas Fundamentales del Núcleo y Pipeline

| ID | Regla | Severidad | Descripción |
|:---|:------|:----------|:------------|
| **BR01** | **Inmutabilidad del Documento Fuente** | **Crítica** | Los archivos originales en carpetas de entrada nunca se sobrescriben ni modifican. Toda salida procesada se escribe exclusivamente en `output/` con cálculo de hash SHA-256 para trazabilidad. |
| **BR02** | **Cobertura de Pruebas TDD >= 80%** | **Crítica** | Ningún código nuevo o refactorización puede incorporarse a `main` si la cobertura de pruebas cae por debajo del 80% o si algún test falla. (Línea base actual: 176 tests). |
| **BR03** | **Cero Secretos en Código** | **Crítica** | Prohibido hardcodear API keys, contraseñas o tokens en el código fuente. Toda configuración sensible se gestiona vía variables de entorno (`.env`) validadas al inicio. |
| **BR04** | **Blindaje Criptográfico SHA-256** | **Crítica** | Las carpetas `/ECC` y `ai-harness/ecc/` son inmutables para agentes IA estándar. Solo se permiten modificaciones autenticadas criptográficamente vía `core/ecc_guard.py` mediante token SHA-256 validado del CEO. |
| **BR05** | **Tolerancia Cero a Fallos Silenciosos** | **Crítica** | Prohibido el uso de `except: pass` o bloques `try/except` que capturen excepciones genéricas sin log estructurado o propagación adecuada mediante excepciones de dominio. |
| **BR06** | **Pureza Zero-Chatter** | **Alta** | Los prompts y la lógica de inferencia deben garantizar que el LLM devuelva única y exclusivamente el contenido corregido o estructurado, sin saludos, preámbulos ("Aquí tienes el texto..."), ni explicaciones conversacionales no solicitadas. |
| **BR07** | **Simetría Multiplataforma Paritaria** | **Alta** | Todo script operativo desarrollado en PowerShell (`.ps1`) para Windows 10/11 debe poseer su contraparte idéntica en Bash (`.sh`) para entornos Linux / Docker, con los mismos parámetros y comportamiento. |
| **BR08** | **Codificación UTF-8 Estricta** | **Alta** | Todo flujo de lectura y escritura de archivos, logs y comunicaciones por consola debe especificar explícitamente `encoding="utf-8"` para evitar mojibakes en entornos Windows. |
| **BR09** | **Gestión Preventiva de Memoria VRAM** | **Alta** | En perfiles de hardware limitados (GTX 1650 4GB), el sistema debe asegurar la descarga de modelos previos (`keep_alive=0`) antes de invocar tareas pesadas para prevenir errores OOM (Out Of Memory). |
| **BR10** | **Preservación Estructural de Documentos** | **Media** | El conversor y reconstructor deben mantener intactos los títulos, listas, tablas y bloques de código originales durante el ciclo completo de procesamiento. |

---

## 2. Reglas Específicas de Interfaz y UI/UX (Dashboard 360°)

| ID | Regla | Severidad | Descripción |
|:---|:------|:----------|:------------|
| **UI01** | **Cero Estilos Inline** | **Obligatorio** | Prohibido el uso de `style="..."` en los archivos HTML/JS. Todos los estilos deben residir en hojas CSS estructuradas con variables de tema. |
| **UI02** | **Tema Oscuro Corporativo** | **Obligatorio** | La interfaz utiliza una paleta oscura moderna (dark slate / zinc / neon accents) de alto contraste y legibilidad óptima para entornos operativos prolongados. |
| **UI03** | **Actualización Asíncrona sin Bloqueo** | **Obligatorio** | La telemetría en tiempo real (`/api/telemetria/360`) debe consumirse mediante fetch periódico o SSE sin congelar el hilo principal de la UI. |

---

## 3. Acciones Terminantemente Prohibidas para Agentes IA (BAN)

| Código | Acción Prohibida | Razón Técnica / Impacto |
|:---|:---|:---|
| **BAN-01** | Modificar archivos dentro de `ECC/` o `ai-harness/ecc/` sin autorización criptográfica. | Violación de la Enterprise Coding Constitution y corrupción de la gobernanza base. |
| **BAN-02** | Modificar directamente el archivo de entrada del usuario en el pipeline. | Riesgo de pérdida irreparable de documentos originales. |
| **BAN-03** | Silenciar excepciones con bloques vacíos (`pass`). | Imposibilita el diagnóstico forense de errores en producción. |
| **BAN-04** | Utilizar `curl.exe` o comandos CMD dentro de scripts o instrucciones para PowerShell. | Causa fallos de parsing de parámetros y comillas en Windows 10/11. Usar `Invoke-RestMethod`. |
| **BAN-05** | Introducir respuestas con "chatter" o texto conversacional en las respuestas para AnythingLLM. | Rompe el formateo de documentos y la pureza de la ingesta RAG. |
| **BAN-06** | Modificar scripts de Windows (`.ps1`) sin replicar exactamente la lógica en Linux (`.sh`). | Destruye la simetría multiplataforma del proyecto. |
| **BAN-07** | Escribir código sin pruebas automatizadas asociadas en `tests/`. | Degrada la cobertura TDD y viola el estándar de certificación continua. |
