"""
scripts/generar_backup.py
Generador automatizado de backup único y optimizado en formato .tar.gz (GZIP nivel 9).
Mantiene un único backup consolidado y elimina versiones obsoletas para no acumular peso.
"""

import os
import tarfile
import time
from pathlib import Path

def crear_backup() -> Path:
    raiz = Path(__file__).resolve().parent.parent
    dir_backup = raiz / "backup"
    dir_backup.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    archivo_salida = dir_backup / f"backup_plataforma_ia_local_{timestamp}.tar.gz"

    # Carpetas y archivos a excluir para máxima optimización de peso
    EXCLUIR_DIRS = {
        ".venv",
        "node_modules",
        "backup",
        "__pycache__",
        ".pytest_cache",
        ".git",
        ".vscode",
        "coverage",
        ".system_generated",
        "docker_storage",
        "docker_storage_prod",
    }
    EXCLUIR_EXTS = {".pyc", ".pyo", ".pyd"}

    archivos_a_incluir = []
    for root, dirs, files in os.walk(raiz):
        # Modificar dirs in-place para que os.walk no descienda en directorios excluidos
        dirs[:] = [d for d in dirs if d not in EXCLUIR_DIRS]
        for file in files:
            if file.startswith(".coverage") or any(file.endswith(ext) for ext in EXCLUIR_EXTS):
                continue
            ruta_completa = Path(root) / file
            ruta_relativa = ruta_completa.relative_to(raiz)
            archivos_a_incluir.append((ruta_completa, ruta_relativa))

    print(f"Empaquetando {len(archivos_a_incluir)} archivos esenciales...")

    with tarfile.open(archivo_salida, "w:gz", compresslevel=9) as tar:
        for ruta_completa, ruta_relativa in archivos_a_incluir:
            tar.add(ruta_completa, arcname=str(Path("plataforma_ia_local") / ruta_relativa))

    # Política de retención: Eliminar backups anteriores para mantener solo el más reciente
    for viejo_backup in dir_backup.glob("backup_plataforma_ia_local_*.tar.gz"):
        if viejo_backup != archivo_salida:
            try:
                viejo_backup.unlink()
                print(f"Eliminado backup anterior: {viejo_backup.name}")
            except Exception as e:
                print(f"No se pudo eliminar {viejo_backup.name}: {e}")

    tam_mb = archivo_salida.stat().st_size / (1024 * 1024)
    print(f"Backup consolidado generado en: {archivo_salida}")
    print(f"Tamano optimizado: {tam_mb:.2f} MB")
    return archivo_salida

if __name__ == "__main__":
    crear_backup()
