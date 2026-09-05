"""
tests/unit/test_core_guardrails.py
Pruebas unitarias para la Capa 5: Guardrails, extracción de <think>, JSON y Markdown.
"""

import pytest
from core.guardrails import (
    separar_razonamiento_y_respuesta,
    extraer_bloque_json,
    validar_json_estricto,
    reparar_json_incompleto,
    validar_markdown_estructurado,
)


class TestGuardrails:
    def test_separar_razonamiento_completo(self) -> None:
        raw = "<think>Analizando el documento legal para hallar clausulas abusivas.</think>Este es el texto limpio final."
        razonamiento, limpio = separar_razonamiento_y_respuesta(raw)
        assert razonamiento == "Analizando el documento legal para hallar clausulas abusivas."
        assert limpio == "Este es el texto limpio final."

    def test_separar_razonamiento_incompleto_truncado(self) -> None:
        raw = "<think>Pensando en el algoritmo de ordenacion sin cerrar el tag"
        razonamiento, limpio = separar_razonamiento_y_respuesta(raw)
        assert razonamiento == "Pensando en el algoritmo de ordenacion sin cerrar el tag"
        assert limpio == ""

    def test_texto_sin_razonamiento(self) -> None:
        raw = "Respuesta directa sin etiquetas de pensamiento."
        razonamiento, limpio = separar_razonamiento_y_respuesta(raw)
        assert razonamiento is None
        assert limpio == "Respuesta directa sin etiquetas de pensamiento."

    def test_validar_json_estricto_fenced(self) -> None:
        raw = '```json\n{"status": "ok", "items": [1, 2, 3]}\n```'
        valido, data, err = validar_json_estricto(raw)
        assert valido is True
        assert data is not None
        assert data["status"] == "ok"
        assert err is None

    def test_reparar_json_incompleto_llaves(self) -> None:
        raw = '{"titulo": "Documento", "items": ["uno", "dos"'
        reparado = reparar_json_incompleto(raw)
        assert reparado is not None
        assert reparado["titulo"] == "Documento"
        assert len(reparado["items"]) == 2

    def test_validar_markdown_estructurado_valido(self) -> None:
        texto = "# Titulo Principal\n\nEste es un parrafo suficientemente largo para cumplir la longitud minima requerida."
        audit = validar_markdown_estructurado(texto, longitud_esperada_min=20)
        assert audit.es_valido is True
        assert len(audit.errores) == 0
        assert audit.score_calidad == 100.0

    def test_validar_markdown_rechaza_vacio(self) -> None:
        audit = validar_markdown_estructurado("   ", longitud_esperada_min=10)
        assert audit.es_valido is False
        assert len(audit.errores) > 0
