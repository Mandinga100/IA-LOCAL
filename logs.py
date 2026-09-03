"""
logs.py - Sistema de logging estructurado y auditoría para Windows 10.
Garantiza salida UTF-8 sin bloqueo y rotación de archivos.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

def configurar_logger(
    nombre: str = "PlataformaIA",
    ruta_log: Path | str = "logs/sistema.log",
    nivel: int = logging.INFO
) -> logging.Logger:
    """
    Configura y devuelve un logger robusto compatible con Windows 10 UTF-8.
    """
    logger = logging.getLogger(nombre)
    logger.setLevel(nivel)

    if logger.handlers:
        return logger

    formato = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Asegurar codificación UTF-8 sin fallos en streams de consola en Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Handler de consola asegurando UTF-8
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(nivel)
    console_handler.setFormatter(formato)
    logger.addHandler(console_handler)

    # Handler de archivo rotativo con encoding utf-8 explícito
    path_log = Path(ruta_log)
    path_log.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        filename=str(path_log),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(nivel)
    file_handler.setFormatter(formato)
    logger.addHandler(file_handler)

    return logger

logger = configurar_logger()
