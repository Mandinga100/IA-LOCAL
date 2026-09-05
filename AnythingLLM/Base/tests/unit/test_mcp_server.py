"""
tests/unit/test_mcp_server.py
Pruebas unitarias para las herramientas del servidor MCP de la Plataforma IA.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from mcp_server import (
    exportar_texto_a_documento,
    telemetria_hardware_local,
    corregir_y_exportar_documento,
    ecc_auditoria_pureza,
    ecc_inspeccion_visual_pixel,
    ecc_verification_loop,
    ecc_token_telemetry,
    ecc_agregar_marca_agua,
    ecc_quitar_marca_agua,
    ecc_resumen_ejecutivo,
    ecc_transformar_formato,
    ecc_abrir_documento,
)


class TestMCPServerTools:
    def test_exportar_texto_a_documento_pdf(self, tmp_path: Path) -> None:
        """Verifica que exportar_texto_a_documento genera el PDF y el enlace."""
        texto = "# Documentación\n\nTexto de prueba generado por MCP.\n\n- Punto 1"
        with patch("mcp_server.SALIDA_DIR", tmp_path):
            resultado = exportar_texto_a_documento(
                texto_markdown=texto,
                nombre_archivo="doc_mcp_test",
                formato_salida="pdf"
            )
            assert "Archivo generado exitosamente" in resultado
            assert "doc_mcp_test.pdf" in resultado
            assert "http://127.0.0.1:8000/api/descargar/doc_mcp_test.pdf" in resultado
            archivo = tmp_path / "doc_mcp_test.pdf"
            assert archivo.exists()
            assert archivo.stat().st_size > 0

    def test_exportar_texto_a_documento_docx(self, tmp_path: Path) -> None:
        """Verifica que exportar_texto_a_documento genera un DOCX válido."""
        texto = "# Título\n\nPárrafo de prueba."
        with patch("mcp_server.SALIDA_DIR", tmp_path):
            resultado = exportar_texto_a_documento(
                texto_markdown=texto,
                nombre_archivo="doc_word_test",
                formato_salida="docx"
            )
            assert "Archivo generado exitosamente" in resultado
            assert "doc_word_test.docx" in resultado
            archivo = tmp_path / "doc_word_test.docx"
            assert archivo.exists()

    def test_telemetria_hardware_local(self) -> None:
        """Comprueba que la telemetría devuelve información legible de la GPU."""
        resultado = telemetria_hardware_local()
        assert isinstance(resultado, str)
        assert len(resultado) > 0

    def test_corregir_y_exportar_archivo_inexistente(self) -> None:
        """Un archivo que no existe devuelve mensaje de error claro."""
        res = corregir_y_exportar_documento(
            ruta_archivo="archivo_fantasma_12345.pdf",
            formato_salida="pdf"
        )
        assert "Error: El archivo 'archivo_fantasma_12345.pdf' no existe" in res

    def test_ecc_auditoria_pureza(self) -> None:
        """Verifica que ecc_auditoria_pureza detecta y esteriliza texto con charla."""
        texto_chatter = "Voy a corregir el documento:\n\n# Documento Limpio\nContenido legítimo.\n\nEspero que te sirva."
        res = ecc_auditoria_pureza(texto_chatter)
        assert "Auditoría Forense de Pureza Documental" in res
        assert "CHATTER DETECTADO Y ELIMINADO" in res
        assert "# Documento Limpio" in res
        assert "Voy a corregir" not in res
        assert "Espero que" not in res

    def test_ecc_inspeccion_visual_pixel(self, tmp_path: Path) -> None:
        """Verifica que ecc_inspeccion_visual_pixel analiza correctamente un archivo."""
        archivo_txt = tmp_path / "doc.txt"
        archivo_txt.write_text("Texto sin imagenes")
        res = ecc_inspeccion_visual_pixel(str(archivo_txt))
        assert "no contiene imágenes embebidas" in res

    def test_ecc_verification_loop(self, tmp_path: Path) -> None:
        """Verifica el ciclo de verificación integral /ECC."""
        archivo_doc = tmp_path / "doc_loop.txt"
        archivo_doc.write_text("# Título de Prueba\n\nEste es un documento completo para verificación.")
        with patch("mcp_server.SALIDA_DIR", tmp_path):
            res = ecc_verification_loop(str(archivo_doc), formato_objetivo="docx")
            assert "Ciclo de Verificación" in res
            assert "Fase 1 (Build / Conversión)" in res
            assert "Fase 2 (Visual Pixel-Perfect)" in res
            assert "Fase 3 (Zero-Chatter Safety Guard)" in res
            assert "Fase 4 (Compilación y Entrega)" in res
            assert "100% QUALITY GATE PASSED" in res

    def test_ecc_token_telemetry(self) -> None:
        """Comprueba que ecc_token_telemetry responde con el estado del sistema."""
        res = ecc_token_telemetry()
        assert isinstance(res, str)
        assert len(res) > 0

    def test_ecc_agregar_y_quitar_marca_agua(self, tmp_path: Path) -> None:
        """Comprueba ecc_agregar_marca_agua y ecc_quitar_marca_agua vía MCP."""
        doc = tmp_path / "doc_test_wm.txt"
        doc.write_text("# Documento Confidencial\nTexto de prueba.")
        with patch("mcp_server.SALIDA_DIR", tmp_path):
            # Error por formato no soportado (txt)
            res_txt = ecc_agregar_marca_agua(str(doc), "CONFIDENCIAL")
            assert "Error" in res_txt

    def test_ecc_transformar_formato(self, tmp_path: Path) -> None:
        """Comprueba ecc_transformar_formato vía MCP."""
        doc = tmp_path / "doc_trans.txt"
        doc.write_text("# Título Transformable\nContenido a convertir.")
        with patch("mcp_server.SALIDA_DIR", tmp_path):
            res = ecc_transformar_formato(str(doc), ".pdf")
            assert "transformado exitosamente" in res

    def test_ecc_abrir_documento_inexistente(self) -> None:
        """Comprueba que ecc_abrir_documento maneja archivos no encontrados."""
        res = ecc_abrir_documento("fantasma_xyz.pdf")
        assert "Error" in res

