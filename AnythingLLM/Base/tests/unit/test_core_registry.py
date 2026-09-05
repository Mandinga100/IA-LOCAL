"""
tests/unit/test_core_registry.py
Pruebas unitarias para la Capa 2: ModelRegistry y catálogo canónico.
"""

import pytest
import respx
import httpx
from pathlib import Path
from core.connector import OllamaConnector
from core.registry import ModelRegistry, CANONICAL_PROFILES


@pytest.mark.anyio
class TestModelRegistry:
    def test_inferencia_capacidades_canonicas(self, tmp_path: Path) -> None:
        connector = OllamaConnector()
        cache_file = tmp_path / "test_cache.json"
        registry = ModelRegistry(connector=connector, cache_path=cache_file)

        cap_coder = registry._infer_capabilities("qwen2.5-coder:32b", "qwen2")
        assert cap_coder.is_coding_specialist is True
        assert cap_coder.supports_tools is True
        assert cap_coder.has_thinking_tags is False

        cap_r1 = registry._infer_capabilities("deepseek-r1:14b", "deepseek")
        assert cap_r1.supports_reasoning is True
        assert cap_r1.has_thinking_tags is True

    async def test_refresh_models_guarda_cache(self, tmp_path: Path) -> None:
        connector = OllamaConnector(base_url="http://localhost:11434")
        cache_file = tmp_path / "test_cache.json"
        registry = ModelRegistry(connector=connector, cache_path=cache_file)

        with respx.mock:
            respx.get("http://localhost:11434/api/tags").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "models": [
                            {
                                "name": "qwen2.5-coder:32b",
                                "digest": "sha256:123456",
                                "details": {
                                    "family": "qwen2",
                                    "parameter_size": "32B",
                                    "quantization_level": "Q4_K_M"
                                }
                            }
                        ]
                    }
                )
            )
            specs = await registry.refresh_models()
            assert "qwen2.5-coder:32b" in specs
            spec = specs["qwen2.5-coder:32b"]
            assert spec.capabilities.is_coding_specialist is True
            assert cache_file.exists()

        # Probar carga desde caché
        nuevo_registry = ModelRegistry(connector=connector, cache_path=cache_file)
        cargado = nuevo_registry.load_cache()
        assert cargado is True
        assert nuevo_registry.get_model("qwen2.5-coder:32b") is not None
