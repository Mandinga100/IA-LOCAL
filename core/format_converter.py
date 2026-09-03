"""
core/format_converter.py - Transformador Universal 360° de Formatos y Extensiones Documentales.
Convierte de manera legítima, bidireccional y sin pérdida estructural entre:
PDF, DOCX, ODT, RTF, HTML, CSV, MD y TXT, preservando activos visuales e imágenes.
Bajo gobernanza /ECC.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
from logs import logger
from conversor import convertir_a_markdown, ConversionError
from reconstructor import exportar_documento_formato, ReconstruccionError
from extractor_visual import extraer_imagenes_documento, inyectar_anclas_imagenes_en_markdown


class FormatConverterError(Exception):
    """Excepción de dominio para fallos en la transformación de formatos."""
    pass


FORMATOS_VALIDOS = {".pdf", ".docx", ".odt", ".rtf", ".html", ".csv", ".md", ".txt"}


def transformar_formato_documento(
    ruta_origen: Path,
    formato_destino: str,
    ruta_salida: Optional[Path] = None,
    preservar_imagenes: bool = True
) -> Path:
    """
    Convierte un documento a cualquier extensión soportada, preservando la jerarquía tipográfica,
    tablas y activos visuales (imágenes) en la posición original.
    """
    if not ruta_origen.exists():
        raise FormatConverterError(f"Archivo de origen no existe: {ruta_origen}")

    ext_dest = formato_destino.lower().strip()
    if not ext_dest.startswith("."):
        ext_dest = f".{ext_dest}"

    if ext_dest not in FORMATOS_VALIDOS:
        raise FormatConverterError(f"Formato destino '{ext_dest}' no soportado. Válidos: {', '.join(sorted(FORMATOS_VALIDOS))}")

    # Determinar ruta de salida
    if not ruta_salida:
        ruta_salida = ruta_origen.parent / f"{ruta_origen.stem}_convertido{ext_dest}"
    else:
        ruta_salida = ruta_salida.with_suffix(ext_dest)

    try:
        # 1. Extraer texto estructurado a Markdown
        texto_md = convertir_a_markdown(ruta_origen)

        # 2. Si se solicita preservar imágenes y el formato lo permite, extraer e inyectar anclas
        if preservar_imagenes and ruta_origen.suffix.lower() in {".pdf", ".docx"}:
            dir_assets = ruta_salida.parent / "assets_convert"
            dir_assets.mkdir(parents=True, exist_ok=True)
            assets = extraer_imagenes_documento(ruta_origen, dir_assets)
            if assets:
                texto_md = inyectar_anclas_imagenes_en_markdown(texto_md, assets)
                logger.info(f"Transformación: {len(assets)} imágenes ancladas en la conversión.")

        # 3. Compilar al formato destino
        ruta_final = exportar_documento_formato(
            texto_markdown=texto_md,
            ruta_destino=ruta_salida,
            formato=ext_dest
        )

        logger.info(f"Conversión exitosa: '{ruta_origen.name}' -> '{ruta_final.name}'")
        return ruta_final

    except Exception as e:
        logger.error(f"Fallo al transformar formato de {ruta_origen.name} a {ext_dest}: {e}", exc_info=True)
        raise FormatConverterError(f"Error transformando formato: {e}") from e
