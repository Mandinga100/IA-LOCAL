"""
tests/unit/test_intent_detector.py
Pruebas unitarias para el detector de intenciones documentales y exportación automática.
"""

from pathlib import Path
import pytest
from core.intent_detector import (
    detectar_intencion_exportacion,
    ejecutar_exportacion_automatica,
    generar_bloque_descarga_markdown,
    ExportIntent,
)


class TestIntentDetector:
    def test_detectar_intencion_pdf_con_ruta_local(self) -> None:
        """Detecta petición de PDF y extrae la ruta del documento original."""
        messages = [
            {"role": "system", "content": "Asistente documental"},
            {
                "role": "user",
                "content": (
                    "Contexto: localfile://C:\\Users\\mandi\\Desktop\\documentacion_corrupta.pdf\n"
                    "Pregunta: ahora necesito que esta misma documentacion, me la devuelvas en .pdf para poder descargarlo"
                ),
            },
        ]
        intent = detectar_intencion_exportacion(messages)
        assert intent is not None
        assert intent.es_exportacion is True
        assert intent.formato == ".pdf"
        assert intent.nombre_base == "documentacion_corrupta"
        assert intent.ruta_fuente is not None
        assert "documentacion_corrupta.pdf" in str(intent.ruta_fuente)

    def test_detectar_intencion_docx_sin_ruta(self) -> None:
        """Detecta petición de exportar a Word/DOCX sin ruta previa."""
        messages = [
            {"role": "user", "content": "Por favor genera el documento en formato docx para descargar"}
        ]
        intent = detectar_intencion_exportacion(messages)
        assert intent is not None
        assert intent.formato == ".docx"
        assert intent.nombre_base == "documento_corregido"

    def test_no_detecta_si_es_chat_comun(self) -> None:
        """Una consulta común de chat no debe activar la exportación."""
        messages = [
            {"role": "user", "content": "Hola, ¿cuál es la capital de Francia?"}
        ]
        intent = detectar_intencion_exportacion(messages)
        assert intent is None

    def test_ejecutar_exportacion_automatica_pdf(self, tmp_path: Path) -> None:
        """Verifica que se genera físicamente el PDF y el bloque de descarga."""
        intent = ExportIntent(
            es_exportacion=True,
            formato=".pdf",
            nombre_base="informe_test"
        )
        texto = "# Informe Técnico\n\nEste es un documento corregido.\n\n- Punto 1\n- Punto 2"
        res = ejecutar_exportacion_automatica(
            intent=intent,
            texto_markdown=texto,
            salida_dir=tmp_path
        )
        assert res["exito"] is True
        assert res["nombre_archivo"] == "informe_test.pdf"
        archivo_generado = Path(res["ruta_absoluta"])
        assert archivo_generado.exists()
        assert archivo_generado.stat().st_size > 0
        assert "Descargar informe_test.pdf" in res["bloque_markdown"]
        assert "http://127.0.0.1:8000/api/descargar/informe_test.pdf" in res["url_descarga"]
        assert "http://127.0.0.1:8000/api/ver/informe_test.pdf" in res["url_visor"]
        assert "Previsualización del Contenido Corregido" in res["bloque_markdown"]
