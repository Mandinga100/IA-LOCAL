"""
config.py - Configuración centralizada e inmutable del sistema.
Gobernanza bajo principios ECC: inmutabilidad, tipado estricto y resolución de rutas.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import FrozenSet, Optional

EXTENSIONES_SOPORTADAS: FrozenSet[str] = frozenset({
    ".pdf", ".docx", ".pptx", ".xlsx", ".html", ".txt", ".md"
})

@dataclass(frozen=True)
class Config:
    """Configuración inmutable del pipeline de procesamiento de documentos."""
    
    ruta_entrada: Path = field(default_factory=lambda: Path("datos/entrada"))
    ruta_salida: Path = field(default_factory=lambda: Path("datos/salida"))
    ruta_errores: Path = field(default_factory=lambda: Path("datos/errores"))
    ruta_logs: Path = field(default_factory=lambda: Path("logs/sistema.log"))
    
    ollama_url: str = "http://localhost:11434"
    modelo: str = "qwen2.5:7b"
    temperatura: float = 0.2
    top_p: float = 0.9
    num_ctx: int = 4096
    
    chunk_size: int = 3500
    chunk_overlap: int = 200
    
    max_reintentos_inferencia: int = 3
    timeout_inferencia_segundos: float = 120.0

    # Modelo de fallback: si se agota max_reintentos_inferencia con el modelo principal,
    # se intenta un único intento adicional con este modelo alternativo (sin backoff).
    # Dejar en None para desactivar el fallback (comportamiento por defecto).
    modelo_fallback: Optional[str] = None

    extensiones_soportadas: FrozenSet[str] = EXTENSIONES_SOPORTADAS

    def __post_init__(self) -> None:
        # Resolver a objetos Path si se suministraron strings
        if not isinstance(self.ruta_entrada, Path):
            object.__setattr__(self, "ruta_entrada", Path(self.ruta_entrada))
        if not isinstance(self.ruta_salida, Path):
            object.__setattr__(self, "ruta_salida", Path(self.ruta_salida))
        if not isinstance(self.ruta_errores, Path):
            object.__setattr__(self, "ruta_errores", Path(self.ruta_errores))
        if not isinstance(self.ruta_logs, Path):
            object.__setattr__(self, "ruta_logs", Path(self.ruta_logs))
