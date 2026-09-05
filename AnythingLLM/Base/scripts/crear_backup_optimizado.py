"""
crear_backup_optimizado.py - Creador de Respaldo Criptográfico y Optimizado del Proyecto.
Excluye dependencias voluminosas (node_modules, .venv, caches) y preserva el 100%
del código fuente, configuraciones, bases de datos SQLite y especificaciones ECC.
"""

import os
import sys
import time
import io
import zipfile
import hashlib
from pathlib import Path
from typing import Set

# Configurar salida UTF-8
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKUP_DIR = ROOT_DIR / "backup"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Patrones o carpetas a excluir estrictamente del backup
EXCLUDE_DIRS: Set[str] = {
    "node_modules",
    ".venv",
    "venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".coverage",
    ".cache",
    "backup",
    ".user_uploaded",
    ".system_generated"
}

EXCLUDE_EXTS: Set[str] = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
    ".tmp"
}

def calcular_sha256(archivo_path: Path) -> str:
    sha = hashlib.sha256()
    with open(archivo_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

def crear_backup() -> Path:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    nombre_zip = f"backup_plataforma_ia_{timestamp}.zip"
    ruta_zip = BACKUP_DIR / nombre_zip

    print("==================================================================")
    print(" GENERANDO BACKUP OPTIMIZADO DE PLATAFORMA IA LOCAL")
    print("==================================================================")
    print(f"Directorio Raíz : {ROOT_DIR}")
    print(f"Destino Backup  : {ruta_zip}")
    print("Exclusiones     : node_modules, .venv, .git, caches, logs temporales")
    print("------------------------------------------------------------------")

    archivos_incluidos = 0
    bytes_totales_sin_comprimir = 0

    t0 = time.time()
    with zipfile.ZipFile(ruta_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(ROOT_DIR):
            # Filtrar carpetas excluidas in-place para que os.walk no entre en ellas
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".venv")]

            rel_dir = Path(root).relative_to(ROOT_DIR)
            if any(part in EXCLUDE_DIRS for part in rel_dir.parts):
                continue

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in EXCLUDE_EXTS:
                    continue
                if file_path.name.endswith(".zip"):
                    continue

                rel_path = file_path.relative_to(ROOT_DIR)
                try:
                    tamano = file_path.stat().st_size
                    # Si algún archivo de prueba o temporal pesa más de 50MB, omitirlo
                    if tamano > 50 * 1024 * 1024:
                        print(f"  [OMITIDO >50MB] {rel_path} ({tamano / 1024 / 1024:.1f} MB)")
                        continue

                    zipf.write(file_path, arcname=str(rel_path))
                    archivos_incluidos += 1
                    bytes_totales_sin_comprimir += tamano
                except Exception as e:
                    print(f"  [ERROR ARCHIVO] {rel_path}: {e}")

    t1 = time.time()
    duracion = t1 - t0
    tamano_comprimido = ruta_zip.stat().st_size
    ratio = (1 - (tamano_comprimido / bytes_totales_sin_comprimir)) * 100 if bytes_totales_sin_comprimir > 0 else 0
    sha256_hash = calcular_sha256(ruta_zip)

    # Generar manifiesto de integridad
    ruta_manifest = BACKUP_DIR / f"manifest_{timestamp}.json"
    manifest_data = {
        "archivo_backup": nombre_zip,
        "timestamp": timestamp,
        "sha256": sha256_hash,
        "archivos_incluidos": archivos_incluidos,
        "peso_original_bytes": bytes_totales_sin_comprimir,
        "peso_original_mb": round(bytes_totales_sin_comprimir / (1024 * 1024), 2),
        "peso_comprimido_bytes": tamano_comprimido,
        "peso_comprimido_mb": round(tamano_comprimido / (1024 * 1024), 2),
        "ratio_compresion_porcentaje": round(ratio, 2),
        "duracion_segundos": round(duracion, 2),
        "exclusiones": list(EXCLUDE_DIRS)
    }

    import json
    ruta_manifest.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n------------------------------------------------------------------")
    print(f"✅ BACKUP CREADO EXITOSAMENTE EN: {duracion:.2f}s")
    print(f"📁 Archivo: {ruta_zip.name}")
    print(f"📊 Archivos incluidos : {archivos_incluidos}")
    print(f"📦 Tamaño original    : {bytes_totales_sin_comprimir / (1024 * 1024):.2f} MB")
    print(f"🗜️ Tamaño comprimido : {tamano_comprimido / (1024 * 1024):.2f} MB ({ratio:.1f}% de ahorro)")
    print(f"🔒 Checksum SHA-256   : {sha256_hash}")
    print(f"📋 Manifiesto creado  : {ruta_manifest.name}")
    print("==================================================================")

    return ruta_zip

if __name__ == "__main__":
    crear_backup()
