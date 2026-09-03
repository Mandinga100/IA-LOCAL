"""
core/pureza_documental.py - Sanitizador y Guardarraíl Determinista de Pureza Documental.
Elimina completamente cualquier residuo conversacional, notas explicativas de la IA,
disculpas, preámbulos y epílogos coloquiales para garantizar que los documentos
compilados contengan 100% contenido legítimo y 0% charla ("Zero-Chatter Protocol").
Bajo gobernanza /ECC y estándares de ciberseguridad por diseño.
"""

import re
from typing import List, Tuple
from logs import logger


# Patrones regex de apertura conversacional que deben ser eliminados de raíz
PATRONES_PREAMBULO: List[re.Pattern] = [
    re.compile(r"^[\s\S]*?(?=(?:^#{1,3}\s+[^\n]+))", re.MULTILINE),  # Texto previo al primer encabezado Markdown
]

PATRONES_FRASES_CHATTER_INICIO: List[re.Pattern] = [
    re.compile(r"^(?:¡?Hola!?|Saludos|Estimad[oa]|Buenos días|Buenas tardes)[^\n]*\n*", re.IGNORECASE),
    re.compile(r"^(?:Voy a corregir|A continuación|Aquí (?:tienes|está|presento)|Te presento|He corregido|Procedo a)[^\n]*\n*", re.IGNORECASE),
    re.compile(r"^(?:Detalles técnicos del procesamiento|Resumen de cambios|Nota del asistente|Notas de corrección)[^\n]*\n*", re.IGNORECASE),
    re.compile(r"^(?:A continuación se muestra|Versión corregida|Documento corregido)[^\n]*:\s*\n*", re.IGNORECASE),
]

PATRONES_FRASES_CHATTER_FINAL: List[re.Pattern] = [
    re.compile(r"\n*(?:Si necesitas|Espero que|No dudes en|Quedo a tu disposición|Cualquier duda|¿Hay algo más|Si tienes alguna)[^\n]*$", re.IGNORECASE),
    re.compile(r"\n*(?:El documento ha sido convertido|Si requieres cambios adicionales|Saludos cordiales|Atentamente)[^\n]*$", re.IGNORECASE),
    re.compile(r"\n*---+\s*\n*(?:Detalles técnicos|Documento reconstruido|El documento ha sido)[^\n]*$", re.IGNORECASE),
]


def eliminar_etiquetas_razonamiento(texto: str) -> str:
    """Elimina etiquetas de razonamiento como <think>...</think> o [THINK]...[/THINK]."""
    texto_sin_think = re.sub(r"<think>[\s\S]*?</think>", "", texto, flags=re.DOTALL)
    texto_sin_think = re.sub(r"\[THINK\][\s\S]*?\[/THINK\]", "", texto_sin_think, flags=re.DOTALL)
    return texto_sin_think.strip()


def limpiar_preambulos_conversacionales(texto: str) -> str:
    """
    Elimina preámbulos tipo 'Voy a corregir el documento', 'Aquí tienes...',
    o metatextos técnicos generados por el LLM antes de comenzar el documento.
    """
    lineas = texto.splitlines()
    if not lineas:
        return ""

    # Si el texto contiene encabezados Markdown (# Título), buscar el primer encabezado legítimo
    primer_header_idx = -1
    for idx, linea in enumerate(lineas):
        linea_str = linea.strip()
        # Ignorar si es un encabezado falso de chatter tipo "### Detalles Técnicos del Procesamiento" o "### Documento Reconstruido"
        if re.match(r"^#{1,3}\s+(?:Detalles Técnicos|Documento Reconstruido|Notas de Corrección|Resumen de Cambios)", linea_str, re.IGNORECASE):
            continue
        if re.match(r"^#{1,3}\s+", linea_str):
            primer_header_idx = idx
            break

    if primer_header_idx > 0:
        # Verificar si las líneas previas eran chatter conversacional
        lineas_previas = "\n".join(lineas[:primer_header_idx])
        es_chatter_previo = any(
            p.search(lineas_previas) for p in PATRONES_FRASES_CHATTER_INICIO
        ) or "detalles técnicos" in lineas_previas.lower() or "procesamiento" in lineas_previas.lower()

        if es_chatter_previo:
            logger.info(f"Zero-Chatter: Se recortaron {primer_header_idx} líneas de preámbulo conversacional.")
            lineas = lineas[primer_header_idx:]

    texto_reducido = "\n".join(lineas).strip()

    # Limpiar líneas iniciales individuales de saludo/intención
    cambio = True
    while cambio and texto_reducido:
        cambio = False
        for patron in PATRONES_FRASES_CHATTER_INICIO:
            match = patron.match(texto_reducido)
            if match:
                texto_reducido = texto_reducido[match.end():].lstrip()
                cambio = True
                break

    return texto_reducido.strip()


def limpiar_epilogos_conversacionales(texto: str) -> str:
    """
    Elimina despedidas o notas al pie añadidas por el LLM
    como 'Si necesitas más detalles...', 'Espero que te sirva', etc.
    """
    lineas = texto.splitlines()
    if not lineas:
        return ""

    # Revisar desde el final hacia arriba líneas de chatter
    while lineas:
        ultima_linea = lineas[-1].strip()
        if not ultima_linea:
            lineas.pop()
            continue

        es_chatter = any(p.search(ultima_linea) for p in PATRONES_FRASES_CHATTER_FINAL)
        # Bloques de separador con notas de cierre
        if ultima_linea in ("---", "***") and len(lineas) > 1 and any(p.search(lineas[-2]) for p in PATRONES_FRASES_CHATTER_FINAL):
            es_chatter = True

        if es_chatter:
            logger.info(f"Zero-Chatter: Se recortó línea de epílogo conversacional: '{ultima_linea}'")
            lineas.pop()
        else:
            break

    return "\n".join(lineas).strip()


def sanitizar_texto_documental(texto_crudo: str) -> str:
    """
    Función principal del Protocolo de Pureza Documental (Zero-Chatter).
    Toma la salida textual de una inferencia o documento y asegura que esté 100% limpia
    de chatter, razonamiento interno o añadidos artificiales antes de ser reconstruida.
    """
    if not texto_crudo or not texto_crudo.strip():
        return ""

    # 1. Eliminar etiquetas <think>
    texto_sin_pensamiento = eliminar_etiquetas_razonamiento(texto_crudo)

    # 2. Eliminar preámbulos conversacionales
    texto_sin_preambulo = limpiar_preambulos_conversacionales(texto_sin_pensamiento)

    # 3. Eliminar epílogos conversacionales
    texto_sanitizado = limpiar_epilogos_conversacionales(texto_sin_preambulo)

    return texto_sanitizado.strip()


def calcular_indice_pureza(texto_original: str, texto_sanitizado: str) -> float:
    """
    Calcula un score de 0.0 a 100.0% indicando el ratio de pureza y retención.
    """
    len_orig = len(texto_original.strip())
    len_san = len(texto_sanitizado.strip())
    if len_orig == 0:
        return 100.0
    return round((len_san / len_orig) * 100.0, 2)
