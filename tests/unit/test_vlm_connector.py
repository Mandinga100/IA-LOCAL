"""
tests/unit/test_vlm_connector.py - Pruebas unitarias para el conector multimodal y perfiles VLM.
Verifica la inyección del parámetro images en OllamaConnector, resolución del perfil DOC_VLM
y capacidades en el ModelRegistry.
"""

import pytest
import respx
import httpx
from core.connector import OllamaConnector
from core.profiles import ProfileType, resolver_perfil, PROFILES
from core.registry import CANONICAL_PROFILES, ModelCapability


@pytest.mark.anyio
@respx.mock
async def test_connector_generate_con_imagenes():
    conector = OllamaConnector(base_url="http://localhost:11434")
    url = "http://localhost:11434/api/generate"

    mock_route = respx.post(url).mock(
        return_value=httpx.Response(200, json={"response": '{"visual_type": "diagrama"}'})
    )

    imagenes_b64 = ["iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="]
    resultado = await conector.generate(
        model="qwen2.5vl:3b",
        prompt="Analiza el diagrama",
        images=imagenes_b64,
        format_json=True
    )

    assert mock_route.called
    req_json = mock_route.calls.last.request.read().decode("utf-8")
    assert "images" in req_json
    assert imagenes_b64[0] in req_json
    assert '"format":"json"' in req_json.replace(" ", "")
    assert "visual_type" in resultado["response"]


def test_perfil_doc_vlm():
    perfil = resolver_perfil("doc_vlm")
    assert perfil.profile_type == ProfileType.DOC_VLM
    assert perfil.primary_model == "qwen2.5vl:7b"
    assert perfil.safe_fallback_model == "qwen2.5vl:3b"
    assert perfil.enforce_json is True

    # Alias
    assert resolver_perfil("vision").profile_type == ProfileType.DOC_VLM
    assert resolver_perfil("diagrama").profile_type == ProfileType.DOC_VLM


def test_registry_capacidades_vision():
    assert "qwen2.5vl" in CANONICAL_PROFILES
    assert CANONICAL_PROFILES["qwen2.5vl"]["supports_vision"] is True
    assert CANONICAL_PROFILES["gemma3"]["supports_vision"] is True
    assert CANONICAL_PROFILES["llama3.2-vision"]["supports_vision"] is True
    assert CANONICAL_PROFILES["qwen2.5"]["supports_vision"] is False
