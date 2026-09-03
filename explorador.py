"""
explorador.py - Escaneo recursivo y detección de documentos soportados.
Filtra archivos temporales (~$*), valida extensiones, firmas mágicas (Magic Bytes) y path traversal.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set
from config import EXTENSIONES_SOPORTADAS
from logs import logger

# Firmas de ejecutables binarios no permitidos (MZ para DOS/PE Windows, ELF para Linux)
FIRMAS_EJECUTABLES_PROHIBIDAS = (b"MZ", b"\x7fELF")

# Límite máximo de tamaño de documento individual (50 MB por defecto para entornos restringidos)
MAX_TAMANO_BYTES_DEFECTO = 50 * 1024 * 1024

@dataclass(frozen=True)
class DocumentoTarea:
    """Representa una tarea de documento inmutable para el pipeline."""
    ruta_origen: Path
    ruta_relativa: Path
    extension: str
    tamano_bytes: int
    hash_sha256: str

def calcular_hash_sha256(ruta: Path) -> str:
    """Calcula el hash SHA-256 de un archivo en bloques de 64 KB."""
    sha256 = hashlib.sha256()
    with open(ruta, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()

def validar_firma_segura(ruta: Path) -> bool:
    """Valida que el archivo no contenga firmas de ejecutables disfrazados."""
    try:
        with open(ruta, "rb") as f:
            cabecera = f.read(4)
        if any(cabecera.startswith(firma) for firma in FIRMAS_EJECUTABLES_PROHIBIDAS):
            logger.warning(f"Archivo rechazado por contener firma de ejecutable binario: {ruta.name}")
            return False
        return True
    except (PermissionError, OSError) as e:
        logger.warning(f"No se pudo leer la cabecera del archivo {ruta}: {e}")
        return False

def explorar_directorio(
    ruta_base: Path | str,
    extensiones: Optional[Set[str]] = None,
    max_tamano_bytes: int = MAX_TAMANO_BYTES_DEFECTO
) -> List[DocumentoTarea]:
    """
    Recorre recursivamente un directorio buscando documentos soportados y seguros.
    
    Args:
        ruta_base: Directorio raíz a explorar.
        extensiones: Conjunto opcional de extensiones permitidas.
        max_tamano_bytes: Límite máximo de tamaño por archivo.
        
    Returns:
        Lista de DocumentoTarea inmutables.
    """
    ruta = Path(ruta_base)
    exts = extensiones or EXTENSIONES_SOPORTADAS

    if not ruta.exists():
        logger.warning(f"El directorio especificado no existe: {ruta}")
        return []

    if not ruta.is_dir():
        logger.warning(f"La ruta no es un directorio: {ruta}")
        return []

    tareas: List[DocumentoTarea] = []
    logger.info(f"Iniciando escaneo en: {ruta}")

    ruta_resuelta_base = ruta.resolve()

    for archivo in ruta.rglob("*"):
        # Ignorar directorios, archivos ocultos y archivos temporales de Office (~$*)
        if not archivo.is_file():
            continue
        if archivo.name.startswith("~$") or archivo.name.startswith("."):
            continue

        ext = archivo.suffix.lower()
        if ext in exts:
            # 1. Guardia de Path Traversal: bloquear symlinks que escapen del directorio raíz
            try:
                archivo_resuelto = archivo.resolve()
                if not archivo_resuelto.is_relative_to(ruta_resuelta_base):
                    logger.warning(
                        f"Path traversal bloqueado: '{archivo}' resuelve fuera del directorio base '{ruta_resuelta_base}'"
                    )
                    continue
            except (OSError, ValueError) as e:
                logger.warning(f"No se pudo resolver la ruta '{archivo}': {e}. Omitiendo.")
                continue

            try:
                tamano = archivo.stat().st_size

                # 2. Guardia de tamaño de documento
                if tamano > max_tamano_bytes:
                    logger.warning(
                        f"Documento '{archivo.name}' excede el tamaño máximo permitido ({tamano} > {max_tamano_bytes} bytes). Omitiendo."
                    )
                    continue

                # 3. Guardia de Magic Bytes / Firmas no ejecutables
                if not validar_firma_segura(archivo):
                    continue

                relativa = archivo.relative_to(ruta)
                hash_val = calcular_hash_sha256(archivo)

                tarea = DocumentoTarea(
                    ruta_origen=archivo_resuelto,
                    ruta_relativa=relativa,
                    extension=ext,
                    tamano_bytes=tamano,
                    hash_sha256=hash_val
                )
                tareas.append(tarea)
                logger.debug(f"Documento detectado: {relativa} ({tamano} bytes)")
            except (PermissionError, OSError) as e:
                logger.error(f"Error accediendo al archivo {archivo}: {e}")

    logger.info(f"Escaneo finalizado. Total documentos detectados: {len(tareas)}")
    return tareas
