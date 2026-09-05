# Auditoría Forense y Validación de Calidad de Inferencia

## 1. Alcance de la Auditoría

Este documento detalla el análisis cualitativo y forense de las salidas generadas por los modelos locales de IA (`qwen2.5:3b` y `qwen2.5-coder:3b`) durante las pruebas del MVP. Se evalúan cuatro dimensiones críticas de calidad:

1. **Corrección Ortográfica, Gramatical y de Estilo en Español.**
2. **Preservación Estructural (Encabezados H1/H2, viñetas, párrafos, tablas).**
3. **Invarianza Sintáctica de Bloques de Código y Variables Técnicas.**
4. **Ausencia de Alucinaciones, Relleno Conversacional o Pérdida de Información.**

---

## 2. Análisis Detallado por Lote de Prueba

### 2.1. Lote A: Texto Plano y Markdown General
- **Modelo:** `qwen2.5:3b` (Cuantización Q4_K_M)
- **Prompt:** `general` (desde `prompts.json`)

#### Caso 1: `comunicado_interno.txt`
| Dimensión | Entrada Original | Salida Corregida | Dictamen |
|---|---|---|---|
| **Acentuación** | `actualisada`, `autenticasion`, `segurida` | `actualizada`, `autenticación`, `seguridad` | ✅ Corregido |
| **Concordancia** | `realize`, `temporarios`, `Agradesemos` | `realice`, `temporales`, `Agradecemos` | ✅ Corregido |
| **Estructura** | Saludos y firmas corporativas | Preservación de saltos de línea y tono | ✅ Perfecto |
| **Alucinaciones** | Texto original limpio | Cero preámbulos conversacionales | ✅ Perfecto |

#### Caso 2: `informe_resumen.md`
| Fragmento Original | Fragmento Corregido | Hallazgo |
|---|---|---|
| `## Introduccion` | `## Introducción` | Tilde en título Markdown restaurada |
| `la organizacion a experimentado un cresimiento` | `la organización ha experimentado un crecimiento` | Corrección del verbo haber (`ha`) y ortografía (`crecimiento`) |
| `se an registrado inconsistensias` | `se han registrado inconsistencias` | Corrección gramatical (`han`) y ortográfica (`s/c`) |
| `- El 45% de las solicitudes fueron resueltas...` | `- El 45% de las solicitudes fueron resueltas...` | Viñeta Markdown conservada idéntica |
| `lentitut intermitente / mas de 500 mensajes simultanios` | `lentitud intermitente / más de 500 mensajes simultáneos` | Erratas tipográficas corregidas |

---

### 2.2. Lote B: Documentos Word `.docx` (Extracción y Reconstrucción)
- **Motor de Extracción:** `MarkItDown`
- **Motor de Reconstrucción:** `python-docx`
- **Modelo:** `qwen2.5:3b`

#### Caso 1: `minuta_directorio.docx`
- **Estructura Original:** Título H1 (*Minuta de Reunion de Directorio*), párrafos de asistentes, subtítulo H2 (*1. Revision Financiera Trimestral*), párrafo con erratas (*finansas*, *reducsion*), subtítulo H2 (*2. Acuerdos Principales*) y 3 viñetas con faltas de acentuación (*Aprovar*, *Autorisar*, *contratasion*).
- **Inspección de la Reconstrucción:**
  - El archivo resultante `datos/salida_mvp/minuta_directorio.docx` abre sin advertencias en Microsoft Word y LibreOffice.
  - La jerarquía de estilos (`Heading 1`, `Heading 2`, `List Bullet`) fue recreada de manera nativa mediante `_guardar_docx()`.
  - Las faltas ortográficas fueron saneadas: `Aprobar el presupuesto`, `Autorizar la contratación`, `reducción de costos`.

---

### 2.3. Lote C: Especialización Técnica y Preservación de Código
- **Modelo:** `qwen2.5-coder:3b`
- **Prompt:** `tecnico` (especializado en invariancia de código)
- **Documento:** `guia_despliegue_local.md`

Este caso constituyó la prueba más estricta de fidelidad sintáctica. A continuación se auditan los bloques técnicos línea por línea:

#### Bloque PowerShell (Original vs. Salida)
```powershell
# ORIGINAL Y SALIDA EXACTAMENTE IDÉNTICOS:
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

# Activar el entorno virtual del proyecto
.\.venv\Scripts\Activate.ps1
```
- **Dictamen:** Ningún comando ni variable fue mutado o traducido.

#### Bloque de Inferencia Python (Original vs. Salida)
```python
# ORIGINAL Y SALIDA EXACTAMENTE IDÉNTICOS:
import httpx

def consultar_modelo(prompt: str, modelo: str = "qwen2.5:3b") -> str:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": modelo,
        "prompt": prompt,
        "stream": False
    }
    with httpx.Client(timeout=60.0) as client:
        res = client.post(url, json=payload)
        res.raise_for_status()
        return res.json().get("response", "")
```
- **Dictamen:** Tipado de argumentos (`prompt: str, modelo: str = "qwen2.5:3b"`), sintaxis de diccionario y llamadas a métodos se mantuvieron 100% inalteradas.

#### Corrección del Texto Explicativo en Español
- `Descripsion General` ➔ `Descripción General`
- `poseso de configurasion` ➔ `proceso de configuración`
- `acelerasion GPU NVIDIA` ➔ `aceleración GPU NVIDIA`
- `Verificasion del Servicio` ➔ `Verificación del Servicio`
- `Versión activa` ➔ `Versión activa`

---

## 3. Matriz de Conformidad de Requisitos de Inferencia

| Criterio de Calidad | Objetivo ECC | Resultado Observado | Estado |
|---|---|---|---|
| **Cero Alucinaciones** | No agregar preámbulos ("Aquí tienes el texto...") | 0 preámbulos en todos los documentos | ✅ Cumplido |
| **Preservación Markdown** | Conservar `#`, `##`, `-`, `*`, tablas | Estructura conservada al 100% | ✅ Cumplido |
| **Invarianza de Código** | 0 cambios en bloques ```python / ```powershell | Código ejecutable idéntico | ✅ Cumplido |
| **Codificación UTF-8** | Cero mojibakes en tildes, `ñ`, `«»` | UTF-8 puro validado | ✅ Cumplido |
| **Integridad de Contenido** | No omitir párrafos ni resumir | Todo el contenido original fue preservado | ✅ Cumplido |

---

## 4. Conclusión de la Auditoría

El motor de inferencia local con `qwen2.5:3b` (para documentos generales) y `qwen2.5-coder:3b` (para documentos con código) cumple con los más altos estándares de precisión editorial y técnica. La especialización de prompts en `prompts.json` demostró guiar de forma determinista al modelo sin derivas conversacionales.
