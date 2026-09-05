"""
conversor.py - Conversión universal de múltiples formatos a Markdown estructurado.
Soporta: DOCX, DOC, ODT, RTF, PPTX, PPT, XLSX, XLS, CSV, PDF, HTML, TXT, MD.
Incorpora decodificación adaptativa anti-mojibakes (UTF-8 -> CP1252 -> Latin-1).
"""

import csv
import warnings
from pathlib import Path
from typing import Any
from logs import logger

def _leer_texto_auto_encoding(ruta: Path) -> str:
    """
    Lee un archivo de texto detectando automáticamente su codificación
    para prevenir mojibakes en documentos ANSI/Windows y UTF-8.
    """
    bytes_archivo = ruta.read_bytes()
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return bytes_archivo.decode(enc)
        except UnicodeDecodeError:
            continue
    return bytes_archivo.decode("utf-8", errors="replace")

class ConversionError(Exception):
    """Excepción de dominio cuando falla la conversión de un documento."""
    pass

class ConversorDocumentos:
    """Conversor universal a Markdown con soporte multiformato extendido."""

    def __init__(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            from markitdown import MarkItDown
            self._md_engine = MarkItDown()

    def _convertir_odt(self, ruta: Path) -> str:
        """Extrae texto estructurado desde OpenDocument Text (.odt)."""
        from odf.opendocument import load
        from odf import teletype

        doc: Any = load(str(ruta.resolve()))
        doc_text: Any = getattr(doc, "text", None)
        if not doc_text:
            return ""

        lineas = []
        for elem in getattr(doc_text, "childNodes", []):
            tag = elem.tagName if hasattr(elem, "tagName") else ""
            if tag == "text:h":
                nivel = int(elem.getAttribute("outlinelevel") or 1)
                texto_h = teletype.extractText(elem).strip()
                if texto_h:
                    lineas.append(f"{'#' * nivel} {texto_h}\n")
            elif tag == "text:p":
                texto_p = teletype.extractText(elem).strip()
                if texto_p:
                    lineas.append(f"{texto_p}\n")
            elif tag == "text:list":
                for item in getattr(elem, "childNodes", []):
                    texto_item = teletype.extractText(item).strip()
                    if texto_item:
                        lineas.append(f"- {texto_item}")
                lineas.append("")

        return "\n".join(lineas).strip()

    def _convertir_rtf(self, ruta: Path) -> str:
        """Extrae texto desde archivos Rich Text Format (.rtf) sin pérdida de codificación."""
        from striprtf.striprtf import rtf_to_text

        contenido_rtf = _leer_texto_auto_encoding(ruta)
        texto_plano = rtf_to_text(contenido_rtf, errors="replace")
        return texto_plano.strip()

    def _convertir_csv(self, ruta: Path) -> str:
        """Convierte un archivo CSV a tabla Markdown estructurada."""
        contenido_csv = _leer_texto_auto_encoding(ruta)
        lineas_csv = contenido_csv.splitlines()
        if not lineas_csv:
            return ""

        muestra = "\n".join(lineas_csv[:10])
        try:
            dialecto = csv.Sniffer().sniff(muestra)
            delimitador = dialecto.delimiter
        except Exception:
            delimitador = ","

        lector = csv.reader(lineas_csv, delimiter=delimitador)
        filas = [fila for fila in lector if any(celda.strip() for celda in fila)]

        if not filas:
            return ""

        encabezado = filas[0]
        num_cols = len(encabezado)
        lineas_md = []
        lineas_md.append("| " + " | ".join(encabezado) + " |")
        lineas_md.append("| " + " | ".join(["---"] * num_cols) + " |")

        for fila in filas[1:]:
            if len(fila) < num_cols:
                fila = fila + [""] * (num_cols - len(fila))
            elif len(fila) > num_cols:
                fila = fila[:num_cols]
            lineas_md.append("| " + " | ".join(fila) + " |")

        return "\n".join(lineas_md)

    def _convertir_xls(self, ruta: Path) -> str:
        """Convierte un libro Excel legacy (.xls) a tablas Markdown."""
        import xlrd  # type: ignore[import-untyped,import-not-found]

        libro = xlrd.open_workbook(str(ruta.resolve()))
        tablas_md = []

        for hoja in libro.sheets():
            if hoja.nrows == 0:
                continue
            tablas_md.append(f"## {hoja.name}\n")
            filas = []
            for r in range(hoja.nrows):
                filas.append([str(hoja.cell_value(r, c)).strip() for c in range(hoja.ncols)])

            if filas:
                encabezado = filas[0]
                num_cols = len(encabezado)
                tablas_md.append("| " + " | ".join(encabezado) + " |")
                tablas_md.append("| " + " | ".join(["---"] * num_cols) + " |")
                for fila in filas[1:]:
                    tablas_md.append("| " + " | ".join(fila) + " |")
                tablas_md.append("\n")

        return "\n".join(tablas_md).strip()

    def convertir(self, ruta_archivo: Path | str) -> str:
        """
        Convierte cualquier formato soportado a Markdown con encoding UTF-8 garantizado.
        
        Args:
            ruta_archivo: Ruta al documento a convertir.
            
        Returns:
            Contenido del documento en formato Markdown con encoding UTF-8.
            
        Raises:
            ConversionError: Si el archivo no existe o la conversión falla.
        """
        ruta = Path(ruta_archivo)
        if not ruta.exists():
            raise ConversionError(f"El archivo no existe: {ruta}")

        ext = ruta.suffix.lower()
        logger.debug(f"Iniciando conversión de {ruta.name} (ext: {ext})...")

        try:
            # 1. Caso nativo: texto plano y Markdown directo con detección anti-mojibakes
            if ext in {".txt", ".md"}:
                contenido = _leer_texto_auto_encoding(ruta)
                logger.info(f"Conversión nativa completada para {ruta.name} ({len(contenido)} caracteres)")
                return contenido

            # 2. Caso OpenDocument Text (.odt)
            if ext == ".odt":
                contenido_odt = self._convertir_odt(ruta)
                logger.info(f"Conversión ODT completada para {ruta.name} ({len(contenido_odt)} caracteres)")
                return contenido_odt

            # 3. Caso Rich Text Format (.rtf)
            if ext == ".rtf":
                contenido_rtf = self._convertir_rtf(ruta)
                logger.info(f"Conversión RTF completada para {ruta.name} ({len(contenido_rtf)} caracteres)")
                return contenido_rtf

            # 4. Caso Valores Separados por Comas (.csv)
            if ext == ".csv":
                contenido_csv = self._convertir_csv(ruta)
                logger.info(f"Conversión CSV completada para {ruta.name} ({len(contenido_csv)} caracteres)")
                return contenido_csv

            # 5. Caso Excel Legacy (.xls)
            if ext == ".xls":
                contenido_xls = self._convertir_xls(ruta)
                logger.info(f"Conversión XLS completada para {ruta.name} ({len(contenido_xls)} caracteres)")
                return contenido_xls

            # 6. Caso MarkItDown: DOCX, PPTX, PPT, XLSX, HTML, PDF
            resultado = self._md_engine.convert(str(ruta.resolve()))
            texto_md = resultado.text_content

            if not texto_md or not texto_md.strip():
                logger.warning(f"La conversión de {ruta.name} produjo contenido vacío.")
                return ""

            logger.info(f"Conversión MarkItDown completada para {ruta.name} ({len(texto_md)} caracteres)")
            return texto_md

        except Exception as e:
            logger.error(f"Fallo crítico al convertir {ruta.name}: {e}", exc_info=True)
            raise ConversionError(f"Error convirtiendo {ruta.name} a Markdown: {e}") from e

def convertir_a_markdown(ruta_archivo: Path | str) -> str:
    """Función de utilidad funcional para conversión directa con desinfección de mojibake."""
    from core.pureza_documental import normalizar_mojibake
    conversor = ConversorDocumentos()
    texto = conversor.convertir(ruta_archivo)
    return normalizar_mojibake(texto)
