"""
core/ecc_guard.py - Módulo de Gobernanza e Inmutabilidad del Arnés /ECC.
Protege las rutas /ECC (raíz) y ai-harness/ecc (producción).
Solo el CEO autenticado mediante verificación criptográfica (SHA-256) tiene autorización
para realizar modificaciones. El nombre nunca se hardcodea en texto plano.
"""

import hashlib
import os
import unicodedata
from pathlib import Path
from typing import Optional, Union

# Hash SHA-256 sellado para validación criptográfica sin exponer texto plano
# Se puede sobreescribir mediante la variable de entorno CEO_AUTH_HASH si fuera necesario
HASH_SELLADO_DEFAULT = "b42c3725f996d2937b402298812f10ac4207c47992d73f0bd81d5eea07d1e8dd"

RUTAS_PROTEGIDAS_ECC = (
    Path("ECC"),
    Path("ai-harness/ecc"),
    Path("ai-harness\\ecc"),
)


def _normalizar_texto(texto: str) -> str:
    """Normaliza un texto eliminando tildes, diacríticos y espacios redundantes en minúsculas."""
    if not texto:
        return ""
    # Descomposición canónica (NFD) para separar letras de tildes
    nfkd = unicodedata.normalize("NFKD", texto.strip().lower())
    # Filtrar marcas diacríticas
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Colapsar espacios múltiples
    return " ".join(sin_tildes.split())


def calcular_hash_autorizacion(candidato: str) -> str:
    """Calcula el hash SHA-256 de la cadena normalizada."""
    normalizado = _normalizar_texto(candidato)
    return hashlib.sha256(normalizado.encode("utf-8")).hexdigest()


def verificar_autorizacion_ceo(nombre_candidato: Optional[str]) -> bool:
    """
    Verifica criptográficamente si el candidato corresponde al CEO autorizado.
    No expone el nombre en texto plano bajo ninguna circunstancia.
    """
    if not nombre_candidato:
        # Permitir bypass si existe una sesión válida en entorno temporal
        token_env = os.getenv("CEO_AUTH_SESSION_TOKEN")
        if token_env:
            hash_esperado = os.getenv("CEO_AUTH_HASH", HASH_SELLADO_DEFAULT)
            return hashlib.sha256(token_env.strip().encode("utf-8")).hexdigest() == hash_esperado
        return False

    hash_candidato = calcular_hash_autorizacion(nombre_candidato)
    hash_esperado = os.getenv("CEO_AUTH_HASH", HASH_SELLADO_DEFAULT)
    return hash_candidato.lower() == hash_esperado.lower()


def es_ruta_protegida_ecc(ruta: Union[str, Path]) -> bool:
    """Determina si una ruta pertenece a los directorios inmutables del arnés /ecc."""
    p = Path(ruta).resolve()
    base = Path.cwd().resolve()
    try:
        rel = p.relative_to(base)
    except ValueError:
        rel = p

    partes = rel.parts
    if not partes:
        return False

    # Caso 1: Carpeta raíz ECC (o subcarpetas)
    if partes[0].upper() == "ECC":
        return True

    # Caso 2: Carpeta ai-harness/ecc (o subcarpetas)
    if len(partes) >= 2 and partes[0].lower() == "ai-harness" and partes[1].lower() == "ecc":
        return True

    return False


def validar_acceso_escritura_ecc(
    ruta: Union[str, Path],
    nombre_ceo_candidato: Optional[str] = None
) -> None:
    """
    Valida si se permite la escritura en la ruta indicada.
    Lanza PermissionError si se intenta modificar el arnés sin la autorización del CEO.
    """
    if not es_ruta_protegida_ecc(ruta):
        return  # Rutas fuera del arnés no están bloqueadas por este guard

    if not verificar_autorizacion_ceo(nombre_ceo_candidato):
        raise PermissionError(
            f"⛔ ACCESO DENEGADO A GOBERNANZA: La ruta '{ruta}' pertenece al arnés /ecc "
            f"(inmutable tanto en raíz como en ai-harness). "
            f"Únicamente el CEO autorizado tiene permisos de edición tras verificar su identidad."
        )
