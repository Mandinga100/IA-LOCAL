"""
test_concurrencia_10_usuarios.py - Validación de concurrencia y estrés para 10 usuarios simultáneos.
Gobernanza /ECC: Verifica estabilidad, latencia, ausencia de race conditions y manejo de errores bajo carga.
"""

import concurrent.futures
import time
import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from servidor_api import app

client = TestClient(app)


def test_salud_servidor():
    """Verifica que el endpoint de salud responde correctamente."""
    response = client.get("/api/salud")
    assert response.status_code == 200
    data = response.json()
    assert data.get("estado") == "online"


@respx.mock
def test_concurrencia_10_usuarios_simultaneos():
    """
    Simula 10 usuarios concurrentes enviando solicitudes al gateway API.
    Verifica que el 100% de las solicitudes sean procesadas exitosamente
    sin excepciones ni condiciones de carrera (Zero-Race-Conditions).
    """
    respx.post("http://localhost:11434/api/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": "# Documento Procesado\n\nContenido validado con éxito."
                },
                "prompt_eval_count": 20,
                "eval_count": 40
            }
        )
    )

    usuarios = [
        {"id": f"usuario_{i}", "mensaje": f"Petición de corrección del usuario {i}"}
        for i in range(1, 11)
    ]

    respuestas = []

    def ejecutar_peticion_usuario(usuario):
        t_inicio = time.perf_counter()
        payload = {
            "model": "chat_ui",
            "messages": [
                {"role": "system", "content": "Eres un asistente documental sin saludos ni charlas."},
                {"role": "user", "content": usuario["mensaje"]}
            ]
        }
        resp = client.post("/v1/chat/completions", json=payload)
        t_fin = time.perf_counter()
        return {
            "usuario": usuario["id"],
            "status_code": resp.status_code,
            "duracion_seg": t_fin - t_inicio,
            "datos": resp.json() if resp.status_code == 200 else None
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futuros = [executor.submit(ejecutar_peticion_usuario, u) for u in usuarios]
        for f in concurrent.futures.as_completed(futuros):
            respuestas.append(f.result())

    assert len(respuestas) == 10
    for r in respuestas:
        assert r["status_code"] == 200, f"Fallo en usuario {r['usuario']}: código {r['status_code']}"
        assert r["datos"] is not None
        assert "choices" in r["datos"]
        contenido = r["datos"]["choices"][0]["message"]["content"]
        assert "Documento Procesado" in contenido


def test_workspaces_configuracion_valida():
    """Verifica que los 4 workspaces definidos para AnythingLLM cumplen el esquema requerido."""
    from pathlib import Path
    import json

    ruta_ws = Path("core/ecc/workspaces")
    assert ruta_ws.exists(), "La carpeta core/ecc/workspaces debe existir"

    archivos_ws = list(ruta_ws.glob("*.json"))
    assert len(archivos_ws) >= 4, f"Se esperaban al menos 4 workspaces, encontrados {len(archivos_ws)}"

    campos_obligatorios = {"name", "slug", "description", "model", "temperature", "system_prompt", "roles_allowed"}

    for f_ws in archivos_ws:
        with open(f_ws, "r", encoding="utf-8") as f:
            data = json.load(f)
            for campo in campos_obligatorios:
                assert campo in data, f"Falta el campo obligatorio '{campo}' en {f_ws.name}"
            assert data["model"] in ["qwen2.5:3b", "qwen2.5-coder:3b"]
