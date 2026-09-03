"""
test_ecc_guard.py - Pruebas unitarias para la gobernanza e inmutabilidad del arnés /ecc.
Verifica que las carpetas /ECC y ai-harness/ecc estén blindadas contra escritura
y que solo el CEO autorizado pueda acceder sin que el nombre esté hardcodeado en texto plano.
"""

from pathlib import Path
import pytest

from core.ecc_guard import (
    es_ruta_protegida_ecc,
    verificar_autorizacion_ceo,
    validar_acceso_escritura_ecc,
    calcular_hash_autorizacion,
    HASH_SELLADO_DEFAULT,
)


def test_rutas_protegidas_reconocimiento():
    """Verifica que las rutas de ECC (raíz) y ai-harness/ecc sean identificadas como protegidas."""
    assert es_ruta_protegida_ecc("ECC") is True
    assert es_ruta_protegida_ecc("ECC/agents/doc-updater.md") is True
    assert es_ruta_protegida_ecc(Path("ai-harness/ecc/rules/common")) is True
    assert es_ruta_protegida_ecc(Path("ai-harness/ecc/skills/test")) is True

    # Rutas normales del proyecto no deben ser marcadas como protegidas
    assert es_ruta_protegida_ecc("datos/salida/doc.pdf") is False
    assert es_ruta_protegida_ecc("core/router.py") is False
    assert es_ruta_protegida_ecc("tests/test_pipeline.py") is False


def test_acceso_denegado_sin_autorizacion():
    """Verifica que cualquier intento sin nombre de CEO en rutas protegidas lanza PermissionError."""
    with pytest.raises(PermissionError) as excinfo:
        validar_acceso_escritura_ecc("ECC/README.md", nombre_ceo_candidato=None)
    assert "ACCESO DENEGADO A GOBERNANZA" in str(excinfo.value)

    with pytest.raises(PermissionError) as excinfo:
        validar_acceso_escritura_ecc("ai-harness/ecc/config.py", nombre_ceo_candidato="Usuario Desconocido")
    assert "ACCESO DENEGADO A GOBERNANZA" in str(excinfo.value)


def test_acceso_permitido_ruta_normal_sin_credenciales():
    """Verifica que rutas normales del proyecto no requieren verificación de CEO."""
    # No debe lanzar ninguna excepción
    validar_acceso_escritura_ecc("datos/salida/test.docx", nombre_ceo_candidato=None)
    validar_acceso_escritura_ecc("core/intent_detector.py", nombre_ceo_candidato=None)


def test_autorizacion_criptografica_ceo():
    """Verifica que el hash coincidente autoriza la escritura."""
    # Verificación de que el hash sellado corresponde exactamente a la normalización
    nombre_autorizado = "Daniel Misle"
    assert verificar_autorizacion_ceo(nombre_autorizado) is True

    # Comprobar variantes con mayúsculas/minúsculas y espacios
    assert verificar_autorizacion_ceo("  daniel   misle  ") is True
    assert verificar_autorizacion_ceo("DANIEL MISLE") is True

    # Nombres erróneos deben ser rechazados
    assert verificar_autorizacion_ceo("Juan Perez") is False
    assert verificar_autorizacion_ceo("Admin") is False
    assert verificar_autorizacion_ceo("") is False


def test_no_hardcoding_de_nombre_en_codigo_fuente():
    """
    Regla imperativa: El nombre en texto plano del CEO JAMÁS debe estar hardcodeado
    en el código fuente de core/ecc_guard.py.
    """
    ruta_guard = Path("core/ecc_guard.py")
    assert ruta_guard.exists()
    contenido = ruta_guard.read_text(encoding="utf-8").lower()

    # Verificar que el nombre y apellido en texto plano no existan en el código
    assert "daniel" not in contenido
    assert "misle" not in contenido

    # Verificar que sí contenga el hash criptográfico SHA-256
    assert HASH_SELLADO_DEFAULT in contenido
