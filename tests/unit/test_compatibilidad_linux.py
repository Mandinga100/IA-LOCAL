"""
tests/unit/test_compatibilidad_linux.py
Suite de pruebas TDD para verificar la paridad y compatibilidad multiplataforma
(Linux en paralelo con Windows 10/11) sin romper ni modificar el soporte existente.
"""

from pathlib import Path
import re
import pytest

from config import Config
from core.ecc_guard import es_ruta_protegida_ecc, HASH_SELLADO_DEFAULT


def test_paridad_scripts_raiz():
    """Verifica que cada script PowerShell en scripts/ tenga su homólogo Bash para Linux."""
    raiz = Path(__file__).resolve().parent.parent.parent
    dir_scripts = raiz / "scripts"

    scripts_ps1 = list(dir_scripts.glob("*.ps1"))
    assert len(scripts_ps1) >= 3, "Deben existir al menos 3 scripts .ps1 en scripts/"

    for s_ps1 in scripts_ps1:
        s_sh = dir_scripts / f"{s_ps1.stem}.sh"
        assert s_sh.exists(), f"Falta el script paralelo Linux para {s_ps1.name}: {s_sh.name}"


def test_paridad_scripts_produccion():
    """Verifica que cada script PowerShell en produccion/scripts/ tenga su homólogo Bash."""
    raiz = Path(__file__).resolve().parent.parent.parent
    dir_scripts_prod = raiz / "produccion" / "scripts"

    scripts_ps1 = list(dir_scripts_prod.glob("*.ps1"))
    assert len(scripts_ps1) >= 2, "Deben existir al menos 2 scripts .ps1 en produccion/scripts/"

    for s_ps1 in scripts_ps1:
        s_sh = dir_scripts_prod / f"{s_ps1.stem}.sh"
        assert s_sh.exists(), f"Falta el script paralelo Linux para {s_ps1.name}: {s_sh.name}"


def test_shebang_scripts_linux():
    """Todos los scripts .sh deben comenzar con el shebang estándar de Bash."""
    raiz = Path(__file__).resolve().parent.parent.parent
    scripts_sh = list((raiz / "scripts").glob("*.sh")) + list((raiz / "produccion" / "scripts").glob("*.sh"))

    assert len(scripts_sh) >= 5, "Deben existir al menos 5 scripts Bash para Linux"

    for script in scripts_sh:
        contenido = script.read_text(encoding="utf-8")
        primera_linea = contenido.splitlines()[0] if contenido.splitlines() else ""
        assert primera_linea.startswith("#!/usr/bin/env bash") or primera_linea.startswith("#!/bin/bash"), (
            f"El script {script.name} no contiene un shebang válido de Bash: '{primera_linea}'"
        )


def test_consistencia_hash_ecc_guard():
    """El script verificar_permisos_ecc.sh debe contener el mismo HASH_SELLADO_DEFAULT."""
    raiz = Path(__file__).resolve().parent.parent.parent
    script_sh = raiz / "scripts" / "verificar_permisos_ecc.sh"
    script_ps1 = raiz / "scripts" / "verificar_permisos_ecc.ps1"

    contenido_sh = script_sh.read_text(encoding="utf-8")
    contenido_ps1 = script_ps1.read_text(encoding="utf-8")

    assert HASH_SELLADO_DEFAULT in contenido_sh, (
        f"El hash {HASH_SELLADO_DEFAULT} no está presente en {script_sh.name}"
    )
    assert HASH_SELLADO_DEFAULT in contenido_ps1, (
        f"El hash {HASH_SELLADO_DEFAULT} no está presente en {script_ps1.name}"
    )


def test_consistencia_variables_ollama_mvp():
    """Las variables de concurrencia para GTX 1650 (MVP) deben ser idénticas en .ps1 y .sh."""
    raiz = Path(__file__).resolve().parent.parent.parent
    sh = (raiz / "scripts" / "optimizar_ollama_concurrencia.sh").read_text(encoding="utf-8")
    ps1 = (raiz / "scripts" / "optimizar_ollama_concurrencia.ps1").read_text(encoding="utf-8")

    assert "OLLAMA_NUM_PARALLEL=2" in sh
    assert "OLLAMA_NUM_PARALLEL" in ps1 and "2" in ps1

    assert "OLLAMA_MAX_LOADED_MODELS=1" in sh
    assert "OLLAMA_MAX_LOADED_MODELS" in ps1 and "1" in ps1

    assert "0.0.0.0:11434" in sh
    assert "0.0.0.0:11434" in ps1


def test_consistencia_variables_ollama_produccion():
    """Las variables de alto rendimiento para Producción (24GB) deben ser idénticas en .ps1 y .sh."""
    raiz = Path(__file__).resolve().parent.parent.parent
    sh = (raiz / "produccion" / "scripts" / "optimizar_ollama_produccion.sh").read_text(encoding="utf-8")
    ps1 = (raiz / "produccion" / "scripts" / "optimizar_ollama_produccion.ps1").read_text(encoding="utf-8")

    assert "OLLAMA_NUM_PARALLEL=4" in sh
    assert "OLLAMA_FLASH_ATTENTION=1" in sh
    assert 'OLLAMA_KV_CACHE_TYPE="q8_0"' in sh or "OLLAMA_KV_CACHE_TYPE=q8_0" in sh
    assert "OLLAMA_MAX_LOADED_MODELS=2" in sh
    assert "0.0.0.0:11434" in sh

    assert "OLLAMA_NUM_PARALLEL" in ps1 and "4" in ps1
    assert "OLLAMA_FLASH_ATTENTION" in ps1 and "1" in ps1
    assert "q8_0" in ps1


def test_ecc_guard_agnostico_posix_y_windows():
    """ecc_guard debe proteger rutas tanto con separadores POSIX (/) como Windows (\\)."""
    assert es_ruta_protegida_ecc("ECC") is True
    assert es_ruta_protegida_ecc("ECC/subcarpeta/archivo.txt") is True
    assert es_ruta_protegida_ecc("ECC\\subcarpeta\\archivo.txt") is True
    assert es_ruta_protegida_ecc("ai-harness/ecc") is True
    assert es_ruta_protegida_ecc("ai-harness\\ecc") is True
    assert es_ruta_protegida_ecc("ai-harness/ecc/agents/document_analyst.md") is True
    assert es_ruta_protegida_ecc("ai-harness\\ecc\\agents\\document_analyst.md") is True

    # Rutas permitidas
    assert es_ruta_protegida_ecc("datos/entrada/doc.pdf") is False
    assert es_ruta_protegida_ecc("datos\\entrada\\doc.pdf") is False
    assert es_ruta_protegida_ecc("core/ecc_guard.py") is False


def test_config_paths_multiplataforma():
    """Config debe resolver rutas a objetos Path sin importar el formato de separadores."""
    cfg_posix = Config(
        ruta_entrada="datos/entrada",
        ruta_salida="datos/salida",
        ruta_errores="datos/errores",
        ruta_logs="logs/sistema.log"
    )
    assert isinstance(cfg_posix.ruta_entrada, Path)
    assert isinstance(cfg_posix.ruta_salida, Path)

    # Validar que los objetos Path se resuelven adecuadamente
    assert cfg_posix.ruta_entrada.name == "entrada"
    assert cfg_posix.ruta_salida.name == "salida"
