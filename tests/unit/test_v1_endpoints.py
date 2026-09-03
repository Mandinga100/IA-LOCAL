"""
tests/unit/test_v1_endpoints.py
Pruebas para los endpoints OpenAI (/v1) y orquestación por perfiles en servidor_api.py.
"""

import json
import pytest
import respx
import httpx
from fastapi.testclient import TestClient
from servidor_api import app

client = TestClient(app)


class TestV1AndOrchestrationEndpoints:
    def test_get_perfiles(self) -> None:
        """GET /api/perfiles devuelve los 5 perfiles lógicos con sus configuraciones."""
        response = client.get("/api/perfiles")
        assert response.status_code == 200
        data = response.json()
        assert "perfiles" in data
        perfiles = data["perfiles"]
        assert "doc_fast" in perfiles
        assert "doc_main" in perfiles
        assert "doc_deep" in perfiles
        assert "chat_ui" in perfiles
        assert "code_ui" in perfiles

    def test_v1_models_lista_perfiles_y_compatibilidad_openai(self) -> None:
        """GET /v1/models expone la lista de modelos para Open WebUI."""
        response = client.get("/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        model_ids = [m["id"] for m in data["data"]]
        assert "chat_ui" in model_ids
        assert "doc_deep" in model_ids
        assert "doc_fast" in model_ids

    @respx.mock
    def test_v1_chat_completions_no_stream(self) -> None:
        """POST /v1/chat/completions devuelve respuesta en formato estándar OpenAI."""
        respx.post("http://localhost:11434/api/chat").mock(
            return_value=httpx.Response(
                200,
                json={
                    "message": {
                        "role": "assistant",
                        "content": "Hola, soy el asistente técnico local."
                    },
                    "prompt_eval_count": 15,
                    "eval_count": 25
                }
            )
        )

        payload = {
            "model": "chat_ui",
            "messages": [
                {"role": "user", "content": "Hola mundo"}
            ],
            "stream": False
        }
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "chat.completion"
        assert len(data["choices"]) == 1
        assert "Hola, soy el asistente técnico local" in data["choices"][0]["message"]["content"]
        assert data["usage"]["total_tokens"] == 40

    @respx.mock
    def test_v1_chat_completions_con_intencion_exportar_pdf(self) -> None:
        """POST /v1/chat/completions detecta petición de PDF y agrega bloque de descarga."""
        respx.post("http://localhost:11434/api/chat").mock(
            return_value=httpx.Response(
                200,
                json={
                    "message": {
                        "role": "assistant",
                        "content": "# Documento Final Corregido\n\nEste es el contenido procesado para el usuario."
                    },
                    "prompt_eval_count": 20,
                    "eval_count": 30
                }
            )
        )

        payload = {
            "model": "chat_ui",
            "messages": [
                {
                    "role": "user",
                    "content": "Por favor devuélvelo en formato pdf para poder descargarlo"
                }
            ],
            "stream": False
        }
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        assert "Previsualización y Métodos de Descarga" in content
        assert "http://127.0.0.1:8000/api/descargar/" in content
        assert "http://127.0.0.1:8000/api/ver/" in content
        assert ".pdf" in content

    @respx.mock
    def test_orquestar_tarea_con_perfil(self) -> None:
        """POST /api/orquestar ejecuta la tarea mediante el TaskRouter de 5 capas."""
        respx.post("http://localhost:11434/api/generate").mock(
            return_value=httpx.Response(
                200,
                json={
                    "response": "<think>Analizando requerimientos</think># Dictamen Tecnico\n\nEl sistema es seguro."
                }
            )
        )

        payload = {
            "perfil": "doc_deep",
            "prompt": "Auditar la infraestructura local"
        }
        response = client.post("/api/orquestar", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["exito"] is True
        assert data["perfil"] == "doc_deep"
        assert data["razonamiento"] == "Analizando requerimientos"
        assert "# Dictamen Tecnico" in data["texto_final"]
        assert data["auditoria"]["es_valido"] is True
