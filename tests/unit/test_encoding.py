"""
tests/unit/test_encoding.py
Suite de pruebas de encoding para la plataforma IA local.
Valida UTF-8 end-to-end, RotatingFileHandler, errors='replace' y caracteres especiales.
"""

import logging
import tempfile
import pytest
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import patch

from logs import configurar_logger
from conversor import convertir_a_markdown, ConversionError


# ---------------------------------------------------------------------------
# Constantes de prueba
# ---------------------------------------------------------------------------
CARACTERES_ESPECIALES = "ñ á é í ó ú ü Ñ «comillas latinas» — guion largo"
TILDES_Y_ACENTO = "acción función término índice señal comunicación"
UNICODE_EXTENDIDO = "αβγδ ∑∫∂ 中文 русский"


# ---------------------------------------------------------------------------
# Tests de UTF-8 round-trip en archivos de texto
# ---------------------------------------------------------------------------
class TestUtf8RoundTrip:
    def test_escritura_lectura_caracteres_especiales(self, tmp_path: Path) -> None:
        """Escritura y lectura de archivo UTF-8 con caracteres especiales del español."""
        archivo = tmp_path / "test_utf8.txt"
        archivo.write_text(CARACTERES_ESPECIALES, encoding="utf-8")
        leido = archivo.read_text(encoding="utf-8")
        assert leido == CARACTERES_ESPECIALES

    def test_escritura_lectura_tildes(self, tmp_path: Path) -> None:
        """Las tildes y acentos sobreviven el ciclo de escritura/lectura."""
        archivo = tmp_path / "tildes.txt"
        archivo.write_text(TILDES_Y_ACENTO, encoding="utf-8")
        leido = archivo.read_text(encoding="utf-8")
        assert leido == TILDES_Y_ACENTO

    def test_escritura_lectura_unicode_extendido(self, tmp_path: Path) -> None:
        """Unicode más allá del español (griego, chino, cirílico) también se preserva."""
        archivo = tmp_path / "unicode_ext.txt"
        archivo.write_text(UNICODE_EXTENDIDO, encoding="utf-8")
        leido = archivo.read_text(encoding="utf-8")
        assert leido == UNICODE_EXTENDIDO

    def test_comillas_latinas_y_guion_largo(self, tmp_path: Path) -> None:
        """«», "" y — (U+2014) no producen mojibake al leer con UTF-8."""
        texto = "Esto es «correcto» — sin mojibake"
        archivo = tmp_path / "tipografia.txt"
        archivo.write_text(texto, encoding="utf-8")
        assert archivo.read_text(encoding="utf-8") == texto


# ---------------------------------------------------------------------------
# Tests de RotatingFileHandler — verificación de encoding
# ---------------------------------------------------------------------------
class TestRotatingFileHandlerEncoding:
    def test_handler_tiene_encoding_utf8(self, tmp_path: Path) -> None:
        """RotatingFileHandler creado por configurar_logger usa encoding='utf-8'."""
        ruta_log = tmp_path / "test_sistema.log"
        logger = configurar_logger(
            nombre="test_encoding_logger",
            ruta_log=ruta_log,
            nivel=logging.DEBUG,
        )
        file_handlers = [
            h for h in logger.handlers if isinstance(h, RotatingFileHandler)
        ]
        assert len(file_handlers) == 1
        assert file_handlers[0].encoding == "utf-8"

    def test_logger_escribe_caracteres_especiales(self, tmp_path: Path) -> None:
        """El logger escribe caracteres especiales en el archivo sin excepción."""
        ruta_log = tmp_path / "log_especial.log"
        logger = configurar_logger(
            nombre="test_logger_chars",
            ruta_log=ruta_log,
            nivel=logging.DEBUG,
        )
        mensaje = f"Log con tildes: {CARACTERES_ESPECIALES}"
        logger.info(mensaje)

        # Forzar flush
        for handler in logger.handlers:
            handler.flush()

        contenido = ruta_log.read_text(encoding="utf-8")
        assert "ñ" in contenido
        assert "«" in contenido

    def test_logger_no_genera_mojibake(self, tmp_path: Path) -> None:
        """El archivo de log no contiene secuencias de mojibake típicas de CP1252."""
        ruta_log = tmp_path / "log_mojibake.log"
        logger = configurar_logger(
            nombre="test_no_mojibake",
            ruta_log=ruta_log,
            nivel=logging.DEBUG,
        )
        logger.warning("Término con acentuación: acción, función, señal.")
        for handler in logger.handlers:
            handler.flush()

        # Leer en bytes y verificar que "acción" está en UTF-8 (no en CP1252)
        raw = ruta_log.read_bytes()
        # 'á' en UTF-8 es 0xC3 0xA1; en CP1252 sería 0xE1 solo
        assert b"\xc3\xa1" in raw or "acción" in ruta_log.read_text(encoding="utf-8")
        # Verificar que no se leen errores al abrir como UTF-8
        texto = ruta_log.read_text(encoding="utf-8")
        assert "acci" in texto


# ---------------------------------------------------------------------------
# Tests de errors='replace' en conversor.py
# ---------------------------------------------------------------------------
class TestConversorErrorsReplace:
    def test_txt_con_bytes_invalidos_no_lanza_excepcion(self, tmp_path: Path) -> None:
        """
        Un archivo .txt con bytes inválidos para UTF-8 debe leerse con
        errors='replace' y devolver contenido (con caracteres de reemplazo U+FFFD).
        No debe lanzar UnicodeDecodeError.
        """
        archivo = tmp_path / "mojibake.txt"
        # Escribir bytes que son válidos en CP1252 pero inválidos en UTF-8
        archivo.write_bytes(b"Texto con bytes inv\xe1lidos para UTF-8.")

        # No debe lanzar excepción
        resultado = convertir_a_markdown(archivo)

        assert isinstance(resultado, str)
        assert len(resultado) > 0
        # El carácter de reemplazo U+FFFD (\ufffd) puede aparecer, pero no excepción
        assert "Texto con bytes inv" in resultado

    def test_txt_utf8_limpio_no_tiene_reemplazos(self, tmp_path: Path) -> None:
        """Un .txt UTF-8 puro no necesita reemplazos y se lee íntegramente."""
        archivo = tmp_path / "limpio.txt"
        archivo.write_text(CARACTERES_ESPECIALES, encoding="utf-8")
        resultado = convertir_a_markdown(archivo)
        assert "ñ" in resultado
        assert "«" in resultado

    def test_md_con_tildes_se_lee_correctamente(self, tmp_path: Path) -> None:
        """Un .md con tildes y ñ se convierte correctamente."""
        contenido_md = f"# {TILDES_Y_ACENTO}\n\nPárrafo de prueba con ñ."
        archivo = tmp_path / "doc.md"
        archivo.write_text(contenido_md, encoding="utf-8")
        resultado = convertir_a_markdown(archivo)
        assert "acción" in resultado
        assert "ñ" in resultado

    def test_conversor_lanza_excepcion_si_archivo_no_existe(self) -> None:
        """ConversionError si el archivo no existe."""
        from conversor import ConversionError
        with pytest.raises(ConversionError):
            convertir_a_markdown(Path("archivo_que_no_existe.txt"))
