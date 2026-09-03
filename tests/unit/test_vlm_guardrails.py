"""
tests/unit/test_vlm_guardrails.py - Pruebas unitarias para guardrails y contratos de visión.
Verifica la validación Pydantic, auto-reparación de JSON incompleto, aislamiento de <think>
y detección de revisión humana obligatoria.
"""

import pytest
from core.guardrails import (
    ElementoVisual,
    MetadatosVisuales,
    RelacionVisual,
    validar_y_reparar_metadatos_visuales,
)


def test_validar_metadatos_visuales_perfecto():
    json_valido = """
    {
        "visual_type": "diagrama_flujo",
        "title": "Arquitectura de Autenticación",
        "caption": "Flujo de inicio de sesión con token JWT.",
        "visible_text": ["Inicio", "Validar Credenciales", "Emitir JWT"],
        "elements": [
            {"id": "n1", "type": "nodo", "label": "Inicio", "location": "top", "confidence": 0.95},
            {"id": "n2", "type": "nodo", "label": "Validar", "location": "center", "confidence": 0.9}
        ],
        "relationships": [
            {"from": "n1", "to": "n2", "relation": "fluye_hacia", "confidence": 0.88}
        ],
        "overall_confidence": 0.92,
        "warnings": []
    }
    """
    meta = validar_y_reparar_metadatos_visuales(
        texto_raw=json_valido,
        image_id="doc-img-001",
        doc_name="manual.docx",
        sha256_hash="abc123hash"
    )

    assert isinstance(meta, MetadatosVisuales)
    assert meta.image_id == "doc-img-001"
    assert meta.visual_type == "diagrama_flujo"
    assert meta.title == "Arquitectura de Autenticación"
    assert len(meta.elements) == 2
    assert meta.elements[0].id == "n1"
    assert len(meta.relationships) == 1
    assert meta.relationships[0].origen == "n1"
    assert meta.overall_confidence == 0.92
    assert meta.requires_human_review is False
    assert "> [IMAGEN: doc-img-001]" in meta.reconstructed_markdown


def test_validar_metadatos_con_think_y_fences():
    texto_con_think = """
    <think>
    He analizado la imagen y parece ser una tabla de precios.
    Observo 3 columnas y 4 filas con alta claridad.
    </think>
    ```json
    {
        "visual_type": "tabla",
        "title": "Lista de Precios",
        "caption": "Precios de suscripción mensual.",
        "visible_text": ["Básico", "Pro", "Enterprise"],
        "overall_confidence": 0.85
    }
    ```
    """
    meta = validar_y_reparar_metadatos_visuales(
        texto_raw=texto_con_think,
        image_id="doc-img-002"
    )

    assert meta.visual_type == "tabla"
    assert meta.title == "Lista de Precios"
    assert meta.overall_confidence == 0.85
    assert meta.requires_human_review is False


def test_validar_metadatos_json_incompleto_reparado():
    # JSON truncado a mitad de una lista de elementos
    json_truncado = """
    {
        "visual_type": "esquema_red",
        "title": "Topología DMZ",
        "elements": [
            {"id": "e1", "label": "Firewall", "confidence": 0.8}
    """
    meta = validar_y_reparar_metadatos_visuales(
        texto_raw=json_truncado,
        image_id="doc-img-003"
    )

    assert meta.visual_type == "esquema_red"
    assert meta.title == "Topología DMZ"
    assert len(meta.elements) == 1
    assert meta.elements[0].label == "Firewall"


def test_validar_metadatos_fallo_total_fallback_seguro():
    texto_invalido = "Lo siento, no pude reconocer nada en la imagen. Es solo ruido blanco."
    meta = validar_y_reparar_metadatos_visuales(
        texto_raw=texto_invalido,
        image_id="doc-img-004"
    )

    assert meta.visual_type == "no_reconocido"
    assert meta.overall_confidence == 0.0
    assert meta.requires_human_review is True
    assert len(meta.warnings) > 0


def test_validar_metadatos_baja_confianza_revision_humana():
    json_baja_conf = """
    {
        "visual_type": "captura_borrosa",
        "caption": "Imagen de muy baja resolución.",
        "overall_confidence": 0.35,
        "warnings": ["Resolución insuficiente para leer texto"]
    }
    """
    meta = validar_y_reparar_metadatos_visuales(
        texto_raw=json_baja_conf,
        image_id="doc-img-005"
    )

    assert meta.overall_confidence == 0.35
    assert meta.requires_human_review is True
