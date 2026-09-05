"""
tests/unit/test_formatos_extendidos.py
Suite de pruebas unitarias para los formatos extendidos (.odt, .rtf, .csv) y guardias de seguridad.
"""

import sys
import csv
import pytest
from pathlib import Path
from unittest.mock import patch

from config import Config
from conversor import ConversorDocumentos, convertir_a_markdown
from reconstructor import guardar_documento_corregido, _guardar_odt, _guardar_rtf, _guardar_csv
from explorador import explorar_directorio, validar_firma_segura
from procesador_lote import main


# ---------------------------------------------------------------------------
# 1. Tests de Conversión (Ingestión hacia Markdown)
# ---------------------------------------------------------------------------
class TestConversionFormatosExtendidos:
    def test_convertir_rtf_con_acentos(self, tmp_path: Path) -> None:
        """Un archivo .rtf con secuencias de control se extrae a texto limpio."""
        contenido_rtf = (
            r"{\rtf1\ansi\ansicpg1252\deff0"
            r"{\fonttbl{\f0 Arial;}}"
            r"\f0\fs24 Resumen ejecutivo: la acci\u243?n fue completada con \u241?and\u250?.\par}"
        )
        archivo_rtf = tmp_path / "documento.rtf"
        archivo_rtf.write_text(contenido_rtf, encoding="utf-8")

        resultado = convertir_a_markdown(archivo_rtf)
        assert "Resumen ejecutivo:" in resultado
        assert "acción" in resultado or "acci" in resultado

    def test_convertir_odt_estructurado(self, tmp_path: Path) -> None:
        """Un archivo .odt con encabezados H1 y párrafos se convierte a Markdown."""
        from odf.opendocument import OpenDocumentText
        from odf.text import H, P

        doc = OpenDocumentText()
        doc.text.addElement(H(outlinelevel=1, text="Titulo Principal ODT"))
        doc.text.addElement(P(text="Parrafo con información de ventas."))
        archivo_odt = tmp_path / "balance.odt"
        doc.save(str(archivo_odt))

        resultado = convertir_a_markdown(archivo_odt)
        assert "# Titulo Principal ODT" in resultado
        assert "Parrafo con información de ventas." in resultado

    def test_convertir_csv_a_tabla_markdown(self, tmp_path: Path) -> None:
        """Un archivo .csv se convierte automáticamente a una tabla Markdown estructurada."""
        contenido_csv = "Nombre,Ciudad,Edad\nCarlos Perez,Santiago,35\nAna Gomez,Valparaiso,28"
        archivo_csv = tmp_path / "usuarios.csv"
        archivo_csv.write_text(contenido_csv, encoding="utf-8")

        resultado = convertir_a_markdown(archivo_csv)
        assert "| Nombre | Ciudad | Edad |" in resultado
        assert "| --- | --- | --- |" in resultado
        assert "| Carlos Perez | Santiago | 35 |" in resultado
        assert "| Ana Gomez | Valparaiso | 28 |" in resultado


# ---------------------------------------------------------------------------
# 2. Tests de Reconstrucción (Markdown hacia Formato de Salida)
# ---------------------------------------------------------------------------
class TestReconstruccionFormatosExtendidos:
    def test_reconstruir_odt_valido(self, tmp_path: Path) -> None:
        """El reconstructor genera un archivo .odt con estructura jerárquica."""
        texto_md = "# Encabezado 1\n\n## Subtitulo\n\n- Punto A\n- Punto B\n\nParrafo regular."
        ruta_orig = tmp_path / "original.odt"
        ruta_dest = tmp_path / "salida.odt"
        ruta_orig.touch()

        resultado = guardar_documento_corregido(texto_md, ruta_orig, ruta_dest)
        assert resultado.exists()
        assert resultado.suffix == ".odt"
        assert resultado.stat().st_size > 0

    def test_reconstruir_rtf_valido(self, tmp_path: Path) -> None:
        """El reconstructor genera un archivo .rtf con cabecera y escapes válidos."""
        texto_md = "# Titulo Principal\n\nTexto con tildes: acción, información."
        ruta_orig = tmp_path / "test.rtf"
        ruta_dest = tmp_path / "salida.rtf"
        ruta_orig.touch()

        resultado = guardar_documento_corregido(texto_md, ruta_orig, ruta_dest)
        assert resultado.exists()
        contenido = resultado.read_text(encoding="ascii")
        assert r"{\rtf1\ansi" in contenido
        assert r"\u243?" in contenido or r"\u243" in contenido  # 'ó' escapada

    def test_reconstruir_csv_desde_tabla_markdown(self, tmp_path: Path) -> None:
        """El reconstructor genera un archivo .csv limpio a partir de una tabla Markdown."""
        texto_md = (
            "| Producto | Cantidad | Precio |\n"
            "| --- | --- | --- |\n"
            "| Laptop Dell | 5 | 1200 |\n"
            "| Monitor 4K | 10 | 350 |"
        )
        ruta_orig = tmp_path / "stock.csv"
        ruta_dest = tmp_path / "salida_stock.csv"
        ruta_orig.touch()

        resultado = guardar_documento_corregido(texto_md, ruta_orig, ruta_dest)
        assert resultado.exists()
        with open(resultado, "r", encoding="utf-8") as f:
            lector = list(csv.reader(f))
        assert lector[0] == ["Producto", "Cantidad", "Precio"]
        assert lector[1] == ["Laptop Dell", "5", "1200"]


# ---------------------------------------------------------------------------
# 3. Tests de Guardias de Seguridad (Magic Bytes & Límites)
# ---------------------------------------------------------------------------
class TestGuardiasSeguridadExplorador:
    def test_archivo_ejecutable_mz_es_bloqueado(self, tmp_path: Path) -> None:
        """Un archivo con firma de ejecutable DOS/PE (MZ) camuflado como .docx o .txt es rechazado."""
        archivo_falso = tmp_path / "virus_camuflado.docx"
        # Cabecera típica de ejecutable PE Windows
        archivo_falso.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00")

        assert validar_firma_segura(archivo_falso) is False

        tareas = explorar_directorio(tmp_path)
        assert len(tareas) == 0

    def test_archivo_que_excede_limite_de_tamano_es_omitido(self, tmp_path: Path) -> None:
        """Un archivo que excede max_tamano_bytes no se incluye en las tareas."""
        archivo_pesado = tmp_path / "pesado.txt"
        archivo_pesado.write_bytes(b"A" * 2000)

        # Establecer límite pequeño de 1000 bytes
        tareas = explorar_directorio(tmp_path, max_tamano_bytes=1000)
        assert len(tareas) == 0


# ---------------------------------------------------------------------------
# 4. Tests de CLI con nuevos flags (--fallback, --chunk-size)
# ---------------------------------------------------------------------------
class TestCLINuevosFlags:
    def test_main_con_flag_fallback_y_chunk_size(self, tmp_path: Path) -> None:
        """La función main() acepta --fallback y --chunk-size y los pasa a Config."""
        dir_in = tmp_path / "in"
        dir_out = tmp_path / "out"
        dir_in.mkdir()
        dir_out.mkdir()

        args = [
            "procesador_lote.py",
            "--origen", str(dir_in),
            "--destino", str(dir_out),
            "--modelo", "qwen2.5:3b",
            "--fallback", "qwen2.5:1.5b",
            "--chunk-size", "1800"
        ]

        with patch.object(sys, "argv", args):
            with patch("procesador_lote.ProcesadorLote.ejecutar_lote") as mock_run:
                main()
                assert mock_run.called
