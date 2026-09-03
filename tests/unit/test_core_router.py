"""
tests/unit/test_core_router.py
Pruebas unitarias para la Capa 4: TaskRouter, afinidad Zero-Swap y tolerancia a fallos.
"""

import pytest
import respx
import httpx
from pathlib import Path
from core.connector import OllamaConnector
from core.registry import ModelRegistry, ModelSpec, ModelCapability
from core.profiles import ProfileType, resolver_perfil
from core.router import TaskRouter


@pytest.mark.anyio
class TestTaskRouter:
    def test_afinidad_zero_swap_prioriza_modelo_caliente(self, tmp_path: Path) -> None:
        connector = OllamaConnector()
        registry = ModelRegistry(connector=connector, cache_path=tmp_path / "cache.json")
        router = TaskRouter(connector=connector, registry=registry)

        # Simular que el modelo ancla qwen2.5-coder:32b ya reside caliente en VRAM
        router._current_loaded_model = "qwen2.5-coder:32b"
        installed = ["qwen2.5:7b", "qwen2.5-coder:32b", "deepseek-r1:14b"]

        perfil_doc_main = resolver_perfil("doc_main")
        seleccionado = router._select_best_available_model(perfil_doc_main, installed)

        # Debe elegir qwen2.5-coder:32b porque está caliente en VRAM y es el primario
        assert seleccionado == "qwen2.5-coder:32b"

    async def test_execute_task_flujo_completo(self, tmp_path: Path) -> None:
        connector = OllamaConnector()
        registry = ModelRegistry(connector=connector, cache_path=tmp_path / "cache.json")
        router = TaskRouter(connector=connector, registry=registry)

        with respx.mock:
            respx.post("http://localhost:11434/api/generate").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "response": "<think>Analizando texto</think># Documento Tecnico\n\nContenido verificado y limpio."
                    }
                )
            )

            decision = await router.execute_task(
                perfil_nombre="doc_fast",
                prompt="Por favor procesa este documento",
                longitud_original=50
            )

            assert decision.perfil_utilizado == ProfileType.DOC_FAST
            assert decision.razonamiento_traza == "Analizando texto"
            assert "# Documento Tecnico" in decision.texto_final
            assert decision.auditoria.es_valido is True
            assert router.get_currently_resident_model() is not None

    async def test_execute_task_vlm_con_imagenes(self, tmp_path: Path) -> None:
        connector = OllamaConnector()
        registry = ModelRegistry(connector=connector, cache_path=tmp_path / "cache.json")
        router = TaskRouter(connector=connector, registry=registry)

        with respx.mock:
            route = respx.post("http://localhost:11434/api/generate").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "response": '{"visual_type": "diagrama", "caption": "Flujo de datos", "overall_confidence": 0.9}'
                    }
                )
            )

            decision = await router.execute_task(
                perfil_nombre="doc_vlm",
                prompt="Analiza la estructura del diagrama",
                images=["base64_fake_image_bytes"]
            )

            assert route.called
            req_body = route.calls.last.request.read().decode("utf-8")
            assert "base64_fake_image_bytes" in req_body
            assert decision.perfil_utilizado == ProfileType.DOC_VLM
            assert "diagrama" in decision.texto_final
            assert decision.auditoria.es_valido is True
