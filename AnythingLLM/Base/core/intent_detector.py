"""
core/intent_detector.py - Detección inteligente de intenciones documentales y exportación.
Permite a AnythingLLM y clientes OpenAI solicitar reconstrucción física y descarga de archivos.
"""

import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from logs import logger
from reconstructor import exportar_documento_formato


@dataclass(frozen=True)
class ExportIntent:
    """Información extraída de la intención de exportación del usuario."""
    es_exportacion: bool
    formato: str  # .pdf, .docx, .odt, .rtf, .html, .csv, .md, .txt
    nombre_base: str
    ruta_fuente: Optional[Path] = None
    texto_fuente_contexto: Optional[str] = None


FORMATOS_MAP = {
    "pdf": ".pdf",
    "docx": ".docx",
    "word": ".docx",
    "doc": ".docx",
    "odt": ".odt",
    "rtf": ".rtf",
    "csv": ".csv",
    "excel": ".csv",
    "html": ".html",
    "txt": ".txt",
    "texto": ".txt",
    "md": ".md",
    "markdown": ".md"
}

KEYWORDS_ACCION = [
    "devuelv", "descarg", "export", "gener", "guard", "pasam", "crea", "entreg", "dámel", "damel"
]


def detectar_intencion_exportacion(messages: List[Dict[str, str]]) -> Optional[ExportIntent]:
    """
    Inspecciona la lista de mensajes en busca de peticiones de descarga o exportación
    física de documentos estructurados.
    """
    if not messages:
        return None

    # El último mensaje del usuario suele tener la orden específica
    ultimo_mensaje_user = ""
    todo_el_historial = ""

    for m in messages:
        contenido = m.get("content", "")
        todo_el_historial += f"\n{contenido}"
        if m.get("role") == "user":
            ultimo_mensaje_user = contenido

    texto_analisis = f"{ultimo_mensaje_user}\n{todo_el_historial}".lower()

    # 1. Comprobar si hay intención de acción
    tiene_accion = any(kw in ultimo_mensaje_user.lower() for kw in KEYWORDS_ACCION)
    
    # 2. Detectar formato solicitado
    formato_detectado = None
    for token, ext in FORMATOS_MAP.items():
        patron = rf"\b{token}\b|\.{token}\b"
        if re.search(patron, ultimo_mensaje_user.lower()):
            formato_detectado = ext
            break

    if not formato_detectado and not tiene_accion:
        return None

    # Si se pide descargar explícitamente pero no se indica formato, buscar en el historial o asumir .pdf
    if tiene_accion and not formato_detectado:
        for token, ext in FORMATOS_MAP.items():
            if re.search(rf"\b{token}\b|\.{token}\b", texto_analisis):
                formato_detectado = ext
                break
        if not formato_detectado:
            formato_detectado = ".pdf"

    # 3. Buscar rutas de archivos locales en el prompt o contexto de AnythingLLM
    # AnythingLLM suele incluir `chunkSource: localfile://C:\...` o `title: "archivo.ext"`
    ruta_encontrada: Optional[Path] = None
    nombre_base = "documento_corregido"

    match_localfile = re.search(r"localfile://([^\s\"'\n]+)", todo_el_historial)
    if match_localfile:
        ruta_candidata = Path(match_localfile.group(1))
        ruta_encontrada = ruta_candidata
        nombre_base = ruta_candidata.stem
    else:
        match_winpath = re.search(r"([a-zA-Z]:\\[^\s\"'\n<>]+\.[a-zA-Z0-9]+)", todo_el_historial)
        if match_winpath:
            ruta_candidata = Path(match_winpath.group(1))
            ruta_encontrada = ruta_candidata
            nombre_base = ruta_candidata.stem
        else:
            match_title = re.search(r'["\']title["\']\s*:\s*["\']([^"\'\n]+)["\']', todo_el_historial)
            if match_title:
                nombre_base = Path(match_title.group(1)).stem

    # Limpiar caracteres ilegales del nombre base
    nombre_base_limpio = re.sub(r'[\\/*?:"<>|]', "", nombre_base).strip() or "documento_corregido"
    formato_final: str = formato_detectado if formato_detectado is not None else ".pdf"

    logger.info(
        f"Intención de exportación detectada: formato={formato_final}, "
        f"nombre_base={nombre_base_limpio}, ruta_fuente={ruta_encontrada}"
    )

    return ExportIntent(
        es_exportacion=True,
        formato=formato_final,
        nombre_base=nombre_base_limpio,
        ruta_fuente=ruta_encontrada
    )


def generar_bloque_descarga_markdown(
    archivo_nombre: str,
    ruta_absoluta: Optional[Path] = None,
    formato: str = ".pdf",
    base_url: str = "http://127.0.0.1:8000",
    ruta_copia_escritorio: Optional[Path] = None,
    texto_previsualizacion: Optional[str] = None
) -> str:
    """Construye un bloque formal y seguro en Markdown con enlaces limpios de descarga y visor."""
    nombre_url = urllib.parse.quote(archivo_nombre)
    url_descarga = f"{base_url}/api/descargar/{nombre_url}"
    url_visor = f"{base_url}/api/ver/{nombre_url}"
    formato_fmt = formato.upper().lstrip(".")

    bloque = [
        "\n\n---",
        "### 📥 Opciones de Descarga",
        f"- **Documento:** `{archivo_nombre}` ({formato_fmt})",
        f"- 📥 **Descarga Directa:** [Descargar {archivo_nombre}]({url_descarga})",
        f"- 🌐 **Visor en Navegador:** [Abrir Documento en Navegador]({url_visor})",
        "---\n"
    ]
    return "\n".join(bloque)


def ejecutar_exportacion_automatica(
    intent: ExportIntent,
    texto_markdown: str,
    salida_dir: Path,
    base_url: str = "http://127.0.0.1:8000"
) -> Dict[str, Any]:
    """
    Ejecuta la exportación material del documento en disco y genera los enlaces formales
    de descarga y visualización, sin copiar al Escritorio ni exponer rutas locales sensibles.
    """
    from core.pureza_documental import sanitizar_texto_documental, es_respuesta_de_rechazo

    # Aplicar Protocolo Zero-Chatter de Pureza Documental
    texto_limpio = sanitizar_texto_documental(texto_markdown)
    if not texto_limpio:
        texto_limpio = texto_markdown.strip()

    # Guardarraíl de Rechazo: Evitar exportar mensajes de incapacidad o disculpas del LLM
    if es_respuesta_de_rechazo(texto_limpio):
        logger.warning(
            f"Exportación cancelada para '{intent.nombre_base}': "
            f"El contenido fue identificado como rechazo/incapacidad del modelo."
        )
        return {
            "exito": False,
            "motivo": "rechazo_modelo",
            "bloque_markdown": "",
            "nombre_archivo": "",
            "ruta_absoluta": "",
            "url_descarga": "",
            "url_visor": "",
            "ruta_desktop": None
        }

    salida_dir.mkdir(parents=True, exist_ok=True)
    nombre_final = f"{intent.nombre_base}{intent.formato}"
    ruta_destino = salida_dir / nombre_final

    ruta_generada = exportar_documento_formato(
        texto_markdown=texto_limpio,
        ruta_destino=ruta_destino,
        formato=intent.formato
    )

    bloque_markdown = generar_bloque_descarga_markdown(
        archivo_nombre=ruta_generada.name,
        ruta_absoluta=ruta_generada.resolve(),
        formato=intent.formato,
        base_url=base_url,
        ruta_copia_escritorio=None,
        texto_previsualizacion=texto_limpio
    )

    return {
        "exito": True,
        "nombre_archivo": ruta_generada.name,
        "ruta_absoluta": str(ruta_generada.resolve()),
        "url_descarga": f"{base_url}/api/descargar/{urllib.parse.quote(ruta_generada.name)}",
        "url_visor": f"{base_url}/api/ver/{urllib.parse.quote(ruta_generada.name)}",
        "ruta_desktop": None,
        "bloque_markdown": bloque_markdown
    }
