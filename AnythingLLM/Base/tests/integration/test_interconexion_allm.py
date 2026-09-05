"""
test_interconexion_allm.py - Pruebas de integración para la interconexión AnythingLLM <-> Base.
Valida configuraciones de entorno, registro MCP, definiciones de workspaces y compatibilidad del gateway OpenAI.
"""

import json
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from servidor_api import app


def test_env_server_interconexion_consistencia():
    """Valida que server/.env está configurado correctamente para apuntar al Gateway de Base."""
    base_dir = Path(__file__).resolve().parents[2]
    allm_dir = base_dir.parent
    env_file = allm_dir / "server" / ".env"
    
    assert env_file.exists(), f"El archivo {env_file} debe existir"
    
    contenido = env_file.read_text(encoding="utf-8")
    assert "LLM_PROVIDER='generic-openai'" in contenido or 'LLM_PROVIDER="generic-openai"' in contenido
    assert "8000/v1" in contenido, "Debe apuntar al puerto 8000/v1 del gateway Base"
    assert "EMBEDDING_ENGINE='ollama'" in contenido or 'EMBEDDING_ENGINE="ollama"' in contenido
    assert "11434" in contenido, "Debe apuntar al puerto 11434 de Ollama"
    assert "VECTOR_DB='lancedb'" in contenido or 'VECTOR_DB="lancedb"' in contenido


def test_mcp_config_valida():
    """Valida que storage/plugins/anythingllm_mcp_servers.json existe y tiene el formato esperado."""
    base_dir = Path(__file__).resolve().parents[2]
    allm_dir = base_dir.parent
    mcp_file = allm_dir / "server" / "storage" / "plugins" / "anythingllm_mcp_servers.json"
    
    assert mcp_file.exists(), f"El archivo {mcp_file} debe existir"
    
    with open(mcp_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "mcpServers" in data
    assert "plataforma-ia-local" in data["mcpServers"]
    server_cfg = data["mcpServers"]["plataforma-ia-local"]
    assert "command" in server_cfg
    assert "args" in server_cfg
    assert any("mcp_server.py" in arg for arg in server_cfg["args"])


def test_workspaces_definiciones_validas():
    """Valida que los workspaces definidos son 4 y cuentan con sus campos obligatorios."""
    from scripts.sincronizar_workspaces import obtener_definiciones_workspaces
    
    workspaces = obtener_definiciones_workspaces()
    assert len(workspaces) >= 4, f"Se esperaban 4 workspaces, encontrados {len(workspaces)}"
    
    campos_requeridos = {"name", "slug", "model", "system_prompt"}
    for ws in workspaces:
        for campo in campos_requeridos:
            assert campo in ws, f"Falta el campo '{campo}' en workspace {ws.get('name')}"


def test_scripts_maestros_simetria():
    """Valida la existencia simétrica de los scripts de orquestación completa."""
    base_dir = Path(__file__).resolve().parents[2]
    script_ps1 = base_dir / "scripts" / "iniciar_plataforma_completa.ps1"
    script_sh = base_dir / "scripts" / "iniciar_plataforma_completa.sh"
    
    assert script_ps1.exists(), f"{script_ps1} debe existir"
    assert script_sh.exists(), f"{script_sh} debe existir"
    
    # Validar que no tienen caracteres corruptos (UTF-8 válido)
    content_ps1 = script_ps1.read_text(encoding="utf-8")
    content_sh = script_sh.read_text(encoding="utf-8")
    
    assert "servidor_api.py" in content_ps1
    assert "servidor_api.py" in content_sh


def test_gateway_openai_endpoint_models():
    """Verifica que el Gateway Base expone /v1/models con estructura compatible con OpenAI."""
    client = TestClient(app)
    response = client.get("/v1/models")
    
    assert response.status_code == 200
    data = response.json()
    assert "object" in data
    assert data["object"] == "list"
    assert "data" in data
    assert isinstance(data["data"], list)
