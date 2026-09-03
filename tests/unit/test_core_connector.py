"""
tests/unit/test_core_connector.py
Pruebas unitarias para la Capa 1: OllamaConnector con mocks de respx.
"""

import pytest
import respx
import httpx
from core.connector import OllamaConnector, ConnectorError


@pytest.mark.anyio
class TestOllamaConnector:
    async def test_check_health_online(self) -> None:
        connector = OllamaConnector(base_url="http://localhost:11434")
        with respx.mock:
            respx.get("http://localhost:11434/api/version").mock(
                return_value=httpx.Response(200, json={"version": "0.3.14"})
            )
            health = await connector.check_health()
            assert health["online"] is True
            assert health["version"] == "0.3.14"

    async def test_list_models_exitoso(self) -> None:
        connector = OllamaConnector(base_url="http://localhost:11434")
        with respx.mock:
            respx.get("http://localhost:11434/api/tags").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "models": [
                            {
                                "name": "qwen2.5:7b",
                                "details": {"family": "qwen2", "parameter_size": "7B", "quantization_level": "Q4_K_M"}
                            }
                        ]
                    }
                )
            )
            models = await connector.list_models()
            assert len(models) == 1
            assert models[0]["name"] == "qwen2.5:7b"

    async def test_generate_inyecta_opciones_ada(self) -> None:
        connector = OllamaConnector(base_url="http://localhost:11434", enable_flash_attn=True, kv_cache_type="q8_0")
        with respx.mock:
            route = respx.post("http://localhost:11434/api/generate").mock(
                return_value=httpx.Response(200, json={"response": "Texto generado correctamente"})
            )
            resp = await connector.generate(
                model="qwen2.5:7b",
                prompt="Prueba prompt",
                num_ctx=8192
            )
            assert resp["response"] == "Texto generado correctamente"
            # Verificar que se enviaron las opciones flash_attn y kv_cache_type
            request = route.calls.last.request
            import json
            body = json.loads(request.content)
            assert body["options"]["flash_attn"] is True
            assert body["options"]["kv_cache_type"] == "q8_0"
            assert body["options"]["num_ctx"] == 8192
