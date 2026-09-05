"""
tests/unit/test_procesador_lote.py
Suite de pruebas unitarias para procesador_lote.py.
Target de cobertura ECC: ≥80% (estaba al 60%).
Cubre: rama de aislamiento de errores, función main() CLI con argparse.
"""

import json
import sys
import pytest
import respx
import httpx
from pathlib import Path
from unittest.mock import patch, MagicMock
from docx import Document

from config import Config
from procesador_lote import ProcesadorLote, main


# ---------------------------------------------------------------------------
# Fixtures compartidos
# ---------------------------------------------------------------------------
@pytest.fixture
def config_tmp(tmp_path: Path) -> Config:
    return Config(
        ruta_entrada=tmp_path / "entrada",
        ruta_salida=tmp_path / "salida",
        ruta_errores=tmp_path / "errores",
        ollama_url="http://localhost:11434",
        modelo="qwen2.5:7b",
        max_reintentos_inferencia=1,
    )


# ---------------------------------------------------------------------------
# Rama de aislamiento de errores
# ---------------------------------------------------------------------------
class TestAislamientoErrores:
    @respx.mock
    def test_documento_con_fallo_se_copia_a_errores(
        self, config_tmp: Config, tmp_path: Path
    ) -> None:
        """
        Si la inferencia falla permanentemente, el documento original debe
        copiarse a ruta_errores/ y el procesamiento continúa sin lanzar excepción.
        """
        dir_entrada = config_tmp.ruta_entrada
        dir_entrada.mkdir(parents=True)
        doc = dir_entrada / "fallo.txt"
        doc.write_text("Texto de prueba.", encoding="utf-8")

        # Ollama siempre responde 500
        respx.post("http://localhost:11434/api/generate").mock(
            return_value=httpx.Response(500, text="CUDA OOM")
        )

        procesador = ProcesadorLote(config_tmp, tipo_documento="general")
        resultado = procesador.procesar_documento(
            next(t for t in __import__("explorador").explorar_directorio(dir_entrada) if t.ruta_origen.name == "fallo.txt")
        )

        assert resultado is False
        # El archivo debe haberse copiado a errores/
        ruta_error = config_tmp.ruta_errores / "fallo.txt"
        assert ruta_error.exists()

    @respx.mock
    def test_lote_completo_con_un_fallo_continua(
        self, config_tmp: Config, tmp_path: Path
    ) -> None:
        """
        Un documento que falla no detiene el lote: los demás siguen procesándose.
        """
        dir_entrada = config_tmp.ruta_entrada
        dir_entrada.mkdir(parents=True)
        (dir_entrada / "ok.txt").write_text("Texto válido.", encoding="utf-8")
        (dir_entrada / "fallo.md").write_text("Texto con fallo.", encoding="utf-8")

        call_count = 0

        def side_effect(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(200, json={"response": "Texto corregido."})
            return httpx.Response(500, text="Error")

        respx.post("http://localhost:11434/api/generate").mock(side_effect=side_effect)

        procesador = ProcesadorLote(config_tmp, tipo_documento="general")
        procesador.ejecutar_lote()

        # El ledger solo debe tener 1 entrada exitosa (el que respondió 200)
        ledger_path = config_tmp.ruta_salida / "historial_procesados.json"
        assert ledger_path.exists()
        with open(ledger_path, "r", encoding="utf-8") as f:
            datos = json.load(f)
        assert len(datos) == 1

    def test_copia_a_errores_falla_silenciosamente(
        self, config_tmp: Config, tmp_path: Path
    ) -> None:
        """
        Si la copia al directorio de errores también falla,
        el procesador no lanza excepción (tolerancia a fallos en cadena).
        """
        from explorador import DocumentoTarea
        import hashlib

        dir_entrada = config_tmp.ruta_entrada
        dir_entrada.mkdir(parents=True)
        doc = dir_entrada / "doc.txt"
        doc.write_text("Texto.", encoding="utf-8")

        # Simular hash
        sha = hashlib.sha256(b"Texto.").hexdigest()
        tarea = DocumentoTarea(
            ruta_origen=doc.resolve(),
            ruta_relativa=Path("doc.txt"),
            extension=".txt",
            tamano_bytes=6,
            hash_sha256=sha,
        )

        procesador = ProcesadorLote(config_tmp, tipo_documento="general")

        with patch("procesador_lote.convertir_a_markdown", side_effect=Exception("Fallo")):
            with patch("builtins.open", side_effect=[Exception("Sin acceso a errores")]):
                # No debe propagar excepción
                resultado = procesador.procesar_documento(tarea)
        assert resultado is False


# ---------------------------------------------------------------------------
# Tests de función main() (CLI con argparse)
# ---------------------------------------------------------------------------
class TestMain:
    @respx.mock
    def test_main_con_argumentos_validos(self, tmp_path: Path) -> None:
        """main() debe parsear argumentos y ejecutar el lote sin error."""
        dir_entrada = tmp_path / "entrada"
        dir_salida = tmp_path / "salida"
        dir_entrada.mkdir(parents=True)
        (dir_entrada / "nota.txt").write_text("Texto de prueba.", encoding="utf-8")

        respx.post("http://localhost:11434/api/generate").mock(
            return_value=httpx.Response(200, json={"response": "Texto corregido."})
        )

        args = [
            "--origen", str(dir_entrada),
            "--destino", str(dir_salida),
            "--tipo", "general",
            "--modelo", "qwen2.5:7b",
            "--url", "http://localhost:11434",
        ]

        with patch.object(sys, "argv", ["procesador_lote.py"] + args):
            main()  # No debe lanzar excepción

        assert (dir_salida / "nota.txt").exists()

    def test_main_directorio_vacio_no_falla(self, tmp_path: Path) -> None:
        """main() con directorio de entrada vacío termina sin error."""
        dir_entrada = tmp_path / "entrada_vacia"
        dir_salida = tmp_path / "salida"
        dir_entrada.mkdir(parents=True)

        args = [
            "--origen", str(dir_entrada),
            "--destino", str(dir_salida),
            "--tipo", "tecnico",
        ]

        with patch.object(sys, "argv", ["procesador_lote.py"] + args):
            main()  # Sin documentos → termina limpiamente

    def test_historial_corrupto_se_reinicia(self, tmp_path: Path) -> None:
        """Un ledger JSON corrupto se detecta y el historial se reinicia a {}."""
        dir_salida = tmp_path / "salida"
        dir_salida.mkdir(parents=True)
        ledger = dir_salida / "historial_procesados.json"
        ledger.write_text("{JSON ROTO!!!", encoding="utf-8")

        cfg = Config(
            ruta_entrada=tmp_path / "entrada",
            ruta_salida=dir_salida,
            ruta_errores=tmp_path / "errores",
        )
        (cfg.ruta_entrada).mkdir(parents=True)

        procesador = ProcesadorLote(cfg)
        assert procesador.historial == {}
