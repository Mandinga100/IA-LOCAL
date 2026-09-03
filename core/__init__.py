"""
core - Paquete de orquestación desacoplada y gobernanza /ECC para Plataforma IA Local.
Arquitectura de 5 capas:
- Capa 1: Conector Ollama hardware-aware (core.connector)
- Capa 2: Registro de modelos y catálogo canónico (core.registry)
- Capa 3: Perfiles lógicos y contratos de tarea (core.profiles)
- Capa 4: Router de capacidad, afinidad y concurrencia (core.router)
- Capa 5: Guardrails, sanitización de razonamiento y validación (core.guardrails)
"""

from core.connector import OllamaConnector
from core.registry import ModelRegistry, ModelCapability, ModelSpec
from core.profiles import PROFILES, TaskProfile, ProfileType
from core.guardrails import (
    separar_razonamiento_y_respuesta,
    validar_json_estricto,
    reparar_json_incompleto,
    validar_markdown_estructurado,
    AuditResult,
    MetadatosVisuales,
    ElementoVisual,
    RelacionVisual,
    validar_y_reparar_metadatos_visuales,
)
from core.router import TaskRouter, RoutingDecision

__all__ = [
    "OllamaConnector",
    "ModelRegistry",
    "ModelCapability",
    "ModelSpec",
    "PROFILES",
    "TaskProfile",
    "ProfileType",
    "separar_razonamiento_y_respuesta",
    "validar_json_estricto",
    "reparar_json_incompleto",
    "validar_markdown_estructurado",
    "AuditResult",
    "MetadatosVisuales",
    "ElementoVisual",
    "RelacionVisual",
    "validar_y_reparar_metadatos_visuales",
    "TaskRouter",
    "RoutingDecision",
]
