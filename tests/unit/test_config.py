import pytest
from pathlib import Path
from config import Config

def test_config_defaults():
    cfg = Config()
    assert cfg.ollama_url == "http://localhost:11434"
    assert "qwen" in cfg.modelo.lower() or "llama" in cfg.modelo.lower()
    assert cfg.chunk_size > 500
    assert cfg.chunk_overlap >= 0
    assert ".docx" in cfg.extensiones_soportadas
    assert ".pdf" in cfg.extensiones_soportadas

def test_config_immutability():
    cfg = Config()
    with pytest.raises(Exception):
        cfg.modelo = "otro_modelo"

def test_config_paths_resolved():
    cfg = Config(ruta_entrada="datos/entrada", ruta_salida="datos/salida")
    assert isinstance(cfg.ruta_entrada, Path)
    assert isinstance(cfg.ruta_salida, Path)
