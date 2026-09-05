"""
tests/unit/test_telemetria_360.py - Pruebas unitarias para telemetría 360° y auditoría de seguridad.
"""

import pytest
from fastapi.testclient import TestClient
from servidor_api import app, registrar_evento_seguridad, _BUFFER_LOGS_SEGURIDAD


@pytest.fixture
def client():
    return TestClient(app)


def test_endpoint_telemetria_360(client):
    """Verifica que /api/telemetria/360 retorne la estructura completa de hardware, red y procesos."""
    response = client.get("/api/telemetria/360")
    assert response.status_code == 200
    data = response.json()

    # Validar claves de primer nivel
    assert "timestamp" in data
    assert "gpu" in data
    assert "cpu" in data
    assert "ram" in data
    assert "red" in data
    assert "procesos" in data

    # Validar estructura GPU
    gpu = data["gpu"]
    assert "disponible" in gpu
    assert "vram_total_mb" in gpu
    assert "vram_usada_mb" in gpu
    assert "vram_libre_mb" in gpu
    assert "gpu_temp_c" in gpu

    # Validar CPU y RAM
    assert "util_pct" in data["cpu"]
    assert "nucleos_logicos" in data["cpu"]
    assert "total_mb" in data["ram"]
    assert "util_pct" in data["ram"]

    # Validar Red
    red = data["red"]
    assert "bytes_enviados_mb" in red
    assert "bytes_recibidos_mb" in red
    assert "throughput_in_kbps" in red
    assert "throughput_out_kbps" in red

    # Validar lista de procesos
    assert isinstance(data["procesos"], list)


def test_endpoint_seguridad_logs(client):
    """Verifica que /api/seguridad/logs devuelva el feed de auditoría y estadísticas."""
    # Insertar un evento conocido
    registrar_evento_seguridad("CRITICAL", "GPU_TEMP", "Prueba de sobretemperatura 85C", {"temp": 85})

    response = client.get("/api/seguridad/logs")
    assert response.status_code == 200
    data = response.json()

    assert "total_eventos" in data
    assert "alertas_criticas" in data
    assert "eventos" in data
    assert data["alertas_criticas"] >= 1
    assert len(data["eventos"]) > 0

    primer_evento = data["eventos"][0]
    assert primer_evento["nivel"] == "CRITICAL"
    assert primer_evento["categoria"] == "GPU_TEMP"


def test_endpoint_test_alerta(client):
    """Verifica la emisión de una alerta de prueba vía POST /api/seguridad/test-alerta."""
    response = client.post(
        "/api/seguridad/test-alerta",
        data={
            "categoria": "VRAM",
            "mensaje": "Saturación simulada de memoria de video",
            "nivel": "WARN"
        }
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "ok"
    assert res_data["evento"]["categoria"] == "VRAM"
    assert res_data["evento"]["nivel"] == "WARN"
