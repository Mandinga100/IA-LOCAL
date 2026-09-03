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
    ruta_absoluta: Path,
    formato: str,
    base_url: str = "http://127.0.0.1:8000",
    ruta_copia_escritorio: Optional[Path] = None,
    texto_previsualizacion: Optional[str] = None
) -> str:
    """Construye el bloque formateado en Markdown con opciones de previsualización y descargas múltiples."""
    nombre_url = urllib.parse.quote(archivo_nombre)
    url_descarga = f"{base_url}/api/descargar/{nombre_url}"
    url_visor = f"{base_url}/api/ver/{nombre_url}"
    url_abrir = f"{base_url}/api/abrir/{nombre_url}"
    formato_fmt = formato.upper().lstrip(".")

    bloque = [
        "\n\n---",
        "### 👁️ Previsualización y Métodos de Descarga",
        f"- **Archivo Reconstruido:** `{archivo_nombre}` ({formato_fmt})",
        f"- ⚡ **Apertura Instantánea en Windows:** [Abrir Archivo en tu Equipo]({url_abrir}) *(1 clic para abrir en Word/Acrobat)*",
        f"- 🌐 **Previsualización Interactiva:** [Abrir Visor Web en Navegador]({url_visor})",
        f"- 📥 **Descarga Directa:** [Descargar {archivo_nombre}]({url_descarga})",
        f"- 📁 **Ruta Local en Servidor:** `{ruta_absoluta}`"
    ]

    if ruta_copia_escritorio and ruta_copia_escritorio.exists():
        bloque.append(f"- 🖥️ **Copia en Escritorio:** Disponible en `{ruta_copia_escritorio}`")

    bloque.append(f"- ⚡ **Comando Rápido PowerShell:** `Start-Process \"{ruta_absoluta}\"`")

    if texto_previsualizacion:
        preview_limpia = texto_previsualizacion.strip()
        bloque.append("\n<details open>")
        bloque.append("<summary><b>📖 Previsualización del Contenido Corregido (Clic para colapsar/expandir)</b></summary>\n")
        bloque.append(preview_limpia)
        bloque.append("\n</details>")

    bloque.append("---\n")
    return "\n".join(bloque)


def ejecutar_exportacion_automatica(
    intent: ExportIntent,
    texto_markdown: str,
    salida_dir: Path,
    base_url: str = "http://127.0.0.1:8000"
) -> Dict[str, Any]:
    """
    Ejecuta la exportación material del documento en disco, crea una copia en el Escritorio
    si está disponible, y genera los metadatos de descarga y previsualización.
    """
    import shutil
    from core.pureza_documental import sanitizar_texto_documental

    salida_dir.mkdir(parents=True, exist_ok=True)
    nombre_final = f"{intent.nombre_base}{intent.formato}"
    ruta_destino = salida_dir / nombre_final

    # Aplicar Protocolo Zero-Chatter de Pureza Documental
    texto_limpio = sanitizar_texto_documental(texto_markdown)
    if not texto_limpio:
        texto_limpio = texto_markdown.strip()

    ruta_generada = exportar_documento_formato(
        texto_markdown=texto_limpio,
        ruta_destino=ruta_destino,
        formato=intent.formato
    )

    # Copia automática en el Escritorio de Windows para acceso manual instantáneo
    ruta_desktop_copia: Optional[Path] = None
    try:
        desktop_dir = Path.home() / "Desktop"
        if desktop_dir.exists() and desktop_dir.is_dir():
            ruta_desktop_copia = desktop_dir / ruta_generada.name
            shutil.copy2(ruta_generada, ruta_desktop_copia)
            logger.info(f"Copia automática en Escritorio creada exitosamente: {ruta_desktop_copia}")
    except Exception as e_copy:
        logger.debug(f"No se pudo copiar automáticamente al Escritorio: {e_copy}")

    bloque_markdown = generar_bloque_descarga_markdown(
        archivo_nombre=ruta_generada.name,
        ruta_absoluta=ruta_generada.resolve(),
        formato=intent.formato,
        base_url=base_url,
        ruta_copia_escritorio=ruta_desktop_copia,
        texto_previsualizacion=texto_limpio
    )

    return {
        "exito": True,
        "nombre_archivo": ruta_generada.name,
        "ruta_absoluta": str(ruta_generada.resolve()),
        "url_descarga": f"{base_url}/api/descargar/{urllib.parse.quote(ruta_generada.name)}",
        "url_visor": f"{base_url}/api/ver/{urllib.parse.quote(ruta_generada.name)}",
        "ruta_desktop": str(ruta_desktop_copia) if ruta_desktop_copia else None,
        "bloque_markdown": bloque_markdown
    }
