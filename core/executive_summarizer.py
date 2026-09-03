"""
core/executive_summarizer.py - Generador de Resúmenes Ejecutivos Profesionales 360° (C-Level).
Transforma cualquier documento técnico, informe o propuesta en un resumen directivo de alto impacto,
con estructura rigurosa, métricas clave, matriz de riesgos y plan de acción priorizado.
Bajo gobernanza /ECC.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import httpx
from logs import logger
from conversor import convertir_a_markdown
from reconstructor import exportar_documento_formato


PROMPT_SISTEMA_EJECUTIVO = """Eres un consultor de estrategia empresarial y analista ejecutivo C-Level (CEO/CTO).
Tu misión es generar un RESUMEN EJECUTIVO DE ALTO IMPACTO a partir de la información provista.

DEBES ESTRUCTURAR TU RESPUESTA OBLIGATORIAMENTE EN ESTAS 5 SECCIONES MARKDOWN:

# 📊 RESUMEN EJECUTIVO DIRECTIVO: [TÍTULO DEL DOCUMENTO]

## 1. 🎯 Tesis Central y Propósito
(Párrafo conciso y contundente explicando el objetivo estratégico, problema que resuelve y valor principal).

## 2. 🔍 Hallazgos Clave y Puntos Críticos
- **Hallazgo 1:** Descripción de alto impacto.
- **Hallazgo 2:** Descripción de alto impacto.
- **Hallazgo 3:** Descripción de alto impacto.

## 3. 📈 Matriz Cuantitativa e Indicadores de Rendimiento
| Indicador / Métrica | Estado Actual | Impacto / Proyección |
|---|---|---|
| [Métrica o Componente] | [Dato cuantificado] | [Impacto directo] |
| [Métrica o Componente] | [Dato cuantificado] | [Impacto directo] |

## 4. ⚠️ Matriz de Riesgos y Mitigación
- **Riesgo:** [Identificación del riesgo crítico].
  - *Mitigación:* [Acción correctiva propuesta].

## 5. 🚀 Plan de Acción y Recomendaciones Priorizadas
1. **Acción Inmediata (Corto Plazo):** [Acción concreta y medible].
2. **Acción Estratégica (Mediano Plazo):** [Consolidación operativa].
3. **Visión de Escala (Largo Plazo):** [Crecimiento sostenido].

REGLA DE PUREZA DIRECTIVA: No agregues saludos, introducciones ni despedidas de asistente. Empieza directamente en el encabezado principal (#).
"""


class ExecutiveSummaryError(Exception):
    """Excepción de dominio para fallos en generación de resumen ejecutivo."""
    pass


def generar_resumen_ejecutivo(
    texto_o_ruta: str | Path,
    modelo: str = "qwen2.5:3b",
    endpoint_ollama: str = "http://127.0.0.1:11434/api/generate",
    timeout_segundos: float = 90.0
) -> Dict[str, Any]:
    """
    Genera un resumen ejecutivo profesional con análisis cualitativo y cuantitativo.
    Acepta tanto una ruta a un archivo (PDF, DOCX, etc.) como una cadena de texto directo.
    """
    # 1. Obtener texto fuente
    if isinstance(texto_o_ruta, Path) or (isinstance(texto_o_ruta, str) and Path(texto_o_ruta).exists() and not "\n" in texto_o_ruta):
        path_doc = Path(texto_o_ruta)
        texto_fuente = convertir_a_markdown(path_doc)
        titulo_doc = path_doc.stem.replace("_", " ").title()
    else:
        texto_fuente = str(texto_o_ruta)
        titulo_doc = "Documento Analizado"

    if not texto_fuente.strip():
        raise ExecutiveSummaryError("El contenido del documento está vacío para generar el resumen ejecutivo.")

    # Acotar longitud si excede la ventana de contexto
    max_chars = 12000
    texto_procesar = texto_fuente[:max_chars] if len(texto_fuente) > max_chars else texto_fuente

    prompt_usuario = f"Genera el Resumen Ejecutivo Directivo para el siguiente contenido:\n\n---\n{texto_procesar}\n---"

    payload = {
        "model": modelo,
        "prompt": prompt_usuario,
        "system": PROMPT_SISTEMA_EJECUTIVO,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 2048
        }
    }

    try:
        with httpx.Client(timeout=timeout_segundos) as client:
            resp = client.post(endpoint_ollama, json=payload)
            if resp.status_code != 200:
                raise ExecutiveSummaryError(f"Ollama respondió con error {resp.status_code}: {resp.text}")
            datos = resp.json()
            resumen_md = datos.get("response", "").strip()

            from core.pureza_documental import sanitizar_texto_documental
            resumen_limpio = sanitizar_texto_documental(resumen_md)

            logger.info(f"Resumen ejecutivo generado exitosamente ({len(resumen_limpio.split())} palabras).")
            return {
                "titulo": titulo_doc,
                "modelo": modelo,
                "contenido_markdown": resumen_limpio,
                "palabras_originales": len(texto_fuente.split()),
                "palabras_resumen": len(resumen_limpio.split())
            }

    except Exception as e:
        logger.error(f"Error generando resumen ejecutivo: {e}", exc_info=True)
        raise ExecutiveSummaryError(f"Fallo al invocar IA para resumen ejecutivo: {e}") from e


def exportar_resumen_ejecutivo(
    resumen_data: Dict[str, Any],
    ruta_salida: Path,
    formato: str = ".pdf"
) -> Path:
    """
    Exporta el resumen ejecutivo al formato físico deseado (.pdf, .docx, .html, .md).
    """
    contenido_md = resumen_data.get("contenido_markdown", "")
    if not contenido_md:
        raise ExecutiveSummaryError("No hay contenido de resumen para exportar.")

    return exportar_documento_formato(
        texto_markdown=contenido_md,
        ruta_destino=ruta_salida,
        formato=formato
    )
