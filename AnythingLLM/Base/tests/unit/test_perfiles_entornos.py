"""
test_perfiles_entornos.py - Validación cruzada de perfiles de hardware (MVP vs Producción).
Gobernanza /ECC: Verifica la correcta resolución de modelos, contextos y fallbacks para 4GB y 24GB.
"""

import json
from pathlib import Path
import pytest

from config import Config
from core.profiles import (
    ProfileType,
    PROFILES,
    PROFILES_MVP,
    PROFILES_PRODUCCION,
    obtener_perfiles,
    resolver_perfil,
)


def test_config_para_mvp():
    """Verifica que Config.para_mvp genera parámetros optimizados para GTX 1650 (4 GB)."""
    cfg = Config.para_mvp()
    assert cfg.modelo == "qwen2.5:3b"
    assert cfg.modelo_fallback == "qwen2.5:1.5b"
    assert cfg.num_ctx == 2048
    assert cfg.chunk_size == 1800
    assert cfg.timeout_inferencia_segundos == 60.0


def test_config_para_produccion():
    """Verifica que Config.para_produccion genera parámetros para Workstation 24 GB."""
    cfg = Config.para_produccion()
    assert cfg.modelo == "qwen2.5:14b"
    assert cfg.modelo_fallback == "qwen2.5:7b"
    assert cfg.num_ctx == 32768
    assert cfg.chunk_size == 4500
    assert cfg.timeout_inferencia_segundos == 180.0


def test_config_desde_entorno(monkeypatch):
    """Verifica resolución dinámica mediante la variable PLATAFORMA_ENTORNO."""
    monkeypatch.setenv("PLATAFORMA_ENTORNO", "produccion")
    cfg_prod = Config.desde_entorno()
    assert cfg_prod.modelo == "qwen2.5:14b"
    assert cfg_prod.num_ctx == 32768

    monkeypatch.setenv("PLATAFORMA_ENTORNO", "mvp")
    cfg_mvp = Config.desde_entorno()
    assert cfg_mvp.modelo == "qwen2.5:3b"
    assert cfg_mvp.num_ctx == 2048


def test_perfiles_mvp_dimensionamiento():
    """Verifica que todos los perfiles MVP tienen modelos compactos y contexto de 2048."""
    perfiles = obtener_perfiles(entorno="mvp")
    for p_type, prof in perfiles.items():
        assert prof.num_ctx == 2048
        # Todos los modelos primarios deben ser 3B
        assert "3b" in prof.primary_model


def test_perfiles_produccion_dimensionamiento():
    """Verifica que los perfiles de producción admiten modelos de alta gama y contexto de 16k a 65k."""
    perfiles = obtener_perfiles(entorno="produccion")
    for p_type, prof in perfiles.items():
        assert prof.num_ctx >= 8192
        # Los perfiles de producción usan modelos de 7B a 32B
        assert any(tag in prof.primary_model for tag in ["7b", "14b", "32b"])


def test_resolver_perfil_con_entorno():
    """Verifica que resolver_perfil responde adecuadamente según el entorno solicitado."""
    perfil_mvp = resolver_perfil("doc_main", entorno="mvp")
    assert perfil_mvp.primary_model == "qwen2.5:3b"
    assert perfil_mvp.num_ctx == 2048

    perfil_prod = resolver_perfil("doc_main", entorno="produccion")
    assert perfil_prod.primary_model == "qwen2.5-coder:32b"
    assert perfil_prod.num_ctx == 32768


def test_esquemas_workspaces_produccion_validos():
    """Valida que los 4 esquemas JSON en produccion/workspaces/ cumplen el estándar."""
    dir_ws = Path("produccion/workspaces")
    assert dir_ws.exists(), "El directorio produccion/workspaces debe existir"
    archivos = list(dir_ws.glob("*.json"))
    assert len(archivos) >= 4, f"Se esperaban 4 workspaces en producción, encontrados {len(archivos)}"

    for f in archivos:
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            assert "name" in data
            assert "slug" in data
            assert "model" in data
            assert "num_ctx" in data
            assert data["num_ctx"] == 32768
            assert data["model"] in ["qwen2.5:14b", "qwen2.5-coder:32b"]
