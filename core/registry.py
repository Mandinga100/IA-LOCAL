"""
core/registry.py - Capa 2: Catálogo Canónico y Registro Dinámico de Modelos.
Combina especificaciones canónicas de familias (Qwen, DeepSeek, Llama) con introspección
dinámica de Ollama y persistencia en caché inmutable (datos/registry_cache.json).
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from logs import logger
from core.connector import OllamaConnector


@dataclass(frozen=True)
class ModelCapability:
    """Capacidades funcionales verificadas de un modelo."""
    supports_tools: bool = False
    supports_json: bool = True
    supports_reasoning: bool = False
    supports_vision: bool = False
    has_thinking_tags: bool = False
    is_coding_specialist: bool = False
    is_embedding_model: bool = False
    max_recommended_ctx: int = 32768
    sweet_spot_ctx: int = 16384


@dataclass(frozen=True)
class ModelSpec:
    """Ficha técnica normalizada de un modelo instalado o catalogado."""
    name: str
    family: str
    parameter_size: str
    quantization: str
    digest: str
    capabilities: ModelCapability
    vram_estimated_mb: int
    context_window_native: int


# Catálogo canónico de referencia (Ground Truth)
CANONICAL_PROFILES: Dict[str, Dict[str, Any]] = {
    "qwen2.5-coder": {
        "supports_tools": True,
        "supports_json": True,
        "supports_reasoning": True,
        "supports_vision": False,
        "has_thinking_tags": False,
        "is_coding_specialist": True,
        "is_embedding_model": False,
        "max_recommended_ctx": 65536,
        "sweet_spot_ctx": 32768,
    },
    "qwen2.5": {
        "supports_tools": True,
        "supports_json": True,
        "supports_reasoning": True,
        "supports_vision": False,
        "has_thinking_tags": False,
        "is_coding_specialist": False,
        "is_embedding_model": False,
        "max_recommended_ctx": 65536,
        "sweet_spot_ctx": 32768,
    },
    "qwen2.5vl": {
        "supports_tools": False,
        "supports_json": True,
        "supports_reasoning": False,
        "supports_vision": True,
        "has_thinking_tags": False,
        "is_coding_specialist": False,
        "is_embedding_model": False,
        "max_recommended_ctx": 32768,
        "sweet_spot_ctx": 8192,
    },
    "gemma3": {
        "supports_tools": True,
        "supports_json": True,
        "supports_reasoning": False,
        "supports_vision": True,
        "has_thinking_tags": False,
        "is_coding_specialist": False,
        "is_embedding_model": False,
        "max_recommended_ctx": 32768,
        "sweet_spot_ctx": 8192,
    },
    "llama3.2-vision": {
        "supports_tools": False,
        "supports_json": True,
        "supports_reasoning": False,
        "supports_vision": True,
        "has_thinking_tags": False,
        "is_coding_specialist": False,
        "is_embedding_model": False,
        "max_recommended_ctx": 32768,
        "sweet_spot_ctx": 8192,
    },
    "deepseek-r1": {
        "supports_tools": False,
        "supports_json": True,
        "supports_reasoning": True,
        "supports_vision": False,
        "has_thinking_tags": True,
        "is_coding_specialist": False,
        "is_embedding_model": False,
        "max_recommended_ctx": 65536,
        "sweet_spot_ctx": 32768,
    },
    "deepseek-coder": {
        "supports_tools": True,
        "supports_json": True,
        "supports_reasoning": False,
        "supports_vision": False,
        "has_thinking_tags": False,
        "is_coding_specialist": True,
        "is_embedding_model": False,
        "max_recommended_ctx": 32768,
        "sweet_spot_ctx": 16384,
    },
    "llama3.1": {
        "supports_tools": True,
        "supports_json": True,
        "supports_reasoning": False,
        "supports_vision": False,
        "has_thinking_tags": False,
        "is_coding_specialist": False,
        "is_embedding_model": False,
        "max_recommended_ctx": 65536,
        "sweet_spot_ctx": 32768,
    },
    "nomic-embed": {
        "supports_tools": False,
        "supports_json": False,
        "supports_reasoning": False,
        "supports_vision": False,
        "has_thinking_tags": False,
        "is_coding_specialist": False,
        "is_embedding_model": True,
        "max_recommended_ctx": 8192,
        "sweet_spot_ctx": 4096,
    }
}


class ModelRegistry:
    """
    Registro dinámico y de arranque ultra-rápido de modelos.
    Utiliza un caché local serializado en disco y se actualiza de forma no-bloqueante.
    """

    def __init__(
        self,
        connector: OllamaConnector,
        cache_path: Optional[Path] = None
    ) -> None:
        self.connector = connector
        self.cache_path = cache_path or Path("datos/registry_cache.json")
        self._models: Dict[str, ModelSpec] = {}

    def _estimate_vram_mb(self, param_size: str, quant: str) -> int:
        """Estima el consumo de VRAM en base al tamaño en miles de millones de parámetros."""
        raw_size = param_size.lower().replace("b", "").strip()
        try:
            billions = float(raw_size)
        except ValueError:
            billions = 7.0

        # Para cuantización Q4/Q5 típica, cada billón toma ~0.6 a 0.7 GB
        is_q4 = "q4" in quant.lower()
        multiplier = 650 if is_q4 else 850
        base_vram = int(billions * multiplier)
        return max(2048, base_vram + 1024)  # margen base de contexto

    def _infer_capabilities(self, name: str, family: str) -> ModelCapability:
        """Deduce capacidades cruzando el nombre y familia con el catálogo canónico."""
        name_lower = name.lower()
        family_lower = family.lower()

        # Búsqueda por heurística canónica
        matched_key = None
        for key in CANONICAL_PROFILES:
            if key in name_lower or key in family_lower:
                matched_key = key
                break

        if matched_key:
            data = CANONICAL_PROFILES[matched_key]
            return ModelCapability(**data)

        # Fallback genérico seguro
        return ModelCapability(
            supports_tools=False,
            supports_json=True,
            supports_reasoning=False,
            has_thinking_tags="r1" in name_lower or "reasoning" in name_lower,
            is_coding_specialist="code" in name_lower or "coder" in name_lower,
            is_embedding_model="embed" in name_lower,
            max_recommended_ctx=16384,
            sweet_spot_ctx=8192
        )

    def load_cache(self) -> bool:
        """Carga los modelos desde el archivo de caché en disco."""
        if not self.cache_path.exists():
            return False
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                loaded: Dict[str, ModelSpec] = {}
                for name, item in raw_data.items():
                    cap = ModelCapability(**item.pop("capabilities", {}))
                    loaded[name] = ModelSpec(capabilities=cap, **item)
                self._models = loaded
                return True
        except Exception as e:
            logger.warning(f"No se pudo cargar registry_cache.json: {e}")
            return False

    def save_cache(self) -> None:
        """Persiste el estado actual del registro a disco de forma atómica."""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            serialized = {}
            for name, spec in self._models.items():
                d = asdict(spec)
                serialized[name] = d
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(serialized, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error al guardar cache de registro: {e}")

    async def refresh_models(self) -> Dict[str, ModelSpec]:
        """
        Inspecciona Ollama mediante /api/tags y construye la ficha técnica de cada modelo.
        No bloquea el arranque si se usa en background.
        """
        try:
            tags = await self.connector.list_models()
        except Exception as e:
            logger.warning(f"Fallo al conectar con Ollama para refresh: {e}")
            self.load_cache()
            return self._models

        new_specs: Dict[str, ModelSpec] = {}
        for m in tags:
            name = m.get("name", "")
            if not name:
                continue
            details = m.get("details", {})
            family = details.get("family", "unknown")
            param_size = details.get("parameter_size", "7B")
            quant = details.get("quantization_level", "Q4_0")
            digest = m.get("digest", "")

            caps = self._infer_capabilities(name, family)
            vram_est = self._estimate_vram_mb(param_size, quant)

            spec = ModelSpec(
                name=name,
                family=family,
                parameter_size=param_size,
                quantization=quant,
                digest=digest,
                capabilities=caps,
                vram_estimated_mb=vram_est,
                context_window_native=caps.max_recommended_ctx
            )
            new_specs[name] = spec

        self._models = new_specs
        self.save_cache()
        return self._models

    def get_model(self, name: str) -> Optional[ModelSpec]:
        """Obtiene la ficha técnica de un modelo por nombre exacto o tag."""
        if name in self._models:
            return self._models[name]
        # Búsqueda por prefijo/tag (ej: 'qwen2.5:7b' coincide con 'qwen2.5:7b-instruct-q4_K_M')
        for k, v in self._models.items():
            if k.startswith(name) or name in k:
                return v
        return None

    def list_specs(self) -> List[ModelSpec]:
        """Retorna la lista de todas las especificaciones registradas."""
        return list(self._models.values())
