"""
core/router.py - Capa 4: Router Inteligente por Capacidad, Afinidad y Concurrencia.
Implementa selección en cascada (primario -> secundario -> safe fallback),
política de afinidad para evitar thrashing de VRAM en GPU Ada SM 8.9 (24 GB)
y serialización segura de inferencia mediante semáforos asíncronos bajo /ECC.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from logs import logger
from core.connector import OllamaConnector, ConnectorError
from core.registry import ModelRegistry, ModelSpec
from core.profiles import PROFILES, ProfileType, TaskProfile, resolver_perfil
from core.guardrails import (
    validar_markdown_estructurado,
    validar_json_estricto,
    reparar_json_incompleto,
    AuditResult,
)


@dataclass
class RoutingDecision:
    """Resultado completo de la ejecución orquestada por el Router."""
    perfil_utilizado: ProfileType
    modelo_ejecutado: str
    es_fallback: bool
    texto_final: str
    razonamiento_traza: Optional[str]
    tiempo_total_ms: float
    reintentos_realizados: int
    auditoria: AuditResult
    metadata_gpu: Dict[str, Any] = field(default_factory=dict)


class TaskRouter:
    """
    Orquestador central de tareas de IA.
    Administra la selección de modelos, la mitigación de swapping de VRAM
    y la tolerancia a fallos en cascada.
    """

    def __init__(
        self,
        connector: OllamaConnector,
        registry: ModelRegistry,
        max_concurrent_inferences: int = 1
    ) -> None:
        self.connector = connector
        self.registry = registry
        self._semaphore = asyncio.Semaphore(max_concurrent_inferences)
        self._current_loaded_model: Optional[str] = None

    def get_currently_resident_model(self) -> Optional[str]:
        """Informa el último modelo ejecutado que probablemente reside caliente en VRAM."""
        return self._current_loaded_model

    def _select_best_available_model(
        self,
        profile: TaskProfile,
        installed_names: List[str]
    ) -> str:
        """
        Elige el mejor modelo disponible considerando:
        1. Modelos instalados en Ollama.
        2. Cadena de fallback del perfil.
        3. Afinidad de VRAM (Zero-Swap): si el modelo residente es capaz de suplir la tarea.
        """
        chain = profile.get_effective_models()

        # Si no hay modelos detectados en Ollama (offline o mock), devuelve el primario
        if not installed_names:
            return chain[0]

        # 1. Regla de Afinidad Zero-Swap:
        # Si el modelo ancla residente (ej: qwen2.5-coder:32b o qwen2.5:7b) ya está en VRAM
        # y está en la cadena válida de este perfil, lo priorizamos para ahorrar el swap de 20 GB.
        if self._current_loaded_model and self._current_loaded_model in installed_names:
            for candidate in chain:
                if candidate in self._current_loaded_model or self._current_loaded_model.startswith(candidate):
                    logger.info(f"Zero-Swap activado: Reutilizando modelo caliente {self._current_loaded_model}")
                    return self._current_loaded_model

        # 2. Búsqueda secuencial en la cadena de fallback
        for candidate in chain:
            for inst in installed_names:
                if inst == candidate or inst.startswith(candidate) or candidate in inst:
                    return inst

        # 3. Fallback a cualquier modelo instalado disponible (priorizando modelos de texto sobre VLM)
        text_models = [m for m in installed_names if "vl" not in m.lower() and "vision" not in m.lower()]
        target = text_models[0] if text_models else installed_names[0]
        logger.warning(f"Ningún modelo de la cadena {chain} encontrado en Ollama. Usando fallback {target}")
        return target

    async def execute_task(
        self,
        perfil_nombre: str,
        prompt: str,
        system_override: Optional[str] = None,
        images: Optional[List[str]] = None,
        contexto_adicional: Optional[Dict[str, Any]] = None,
        longitud_original: Optional[int] = None,
        max_reintentos: int = 2
    ) -> RoutingDecision:
        """
        Ejecuta una tarea documental bajo control de concurrencia y tolerancia a fallos.
        Soporta tareas textuales y multimodales (VLM).
        """
        profile = resolver_perfil(perfil_nombre)
        specs = self.registry.list_specs()
        installed_names = [s.name for s in specs]

        system_prompt = system_override or profile.system_prompt
        selected_model = self._select_best_available_model(profile, installed_names)
        candidate_chain = profile.get_effective_models()

        t_start = time.perf_counter()
        reintentos = 0
        ultimo_error: Optional[Exception] = None
        es_fallback = False

        async with self._semaphore:
            # Iterar sobre los modelos de la cadena de fallback si ocurren fallos severos
            for model_to_try in [selected_model] + [m for m in candidate_chain if m != selected_model]:
                for intento in range(max_reintentos + 1):
                    try:
                        logger.info(f"Iniciando inferencia con perfil {profile.profile_type.value} en modelo {model_to_try} (intento {intento})")
                        
                        resp = await self.connector.generate(
                            model=model_to_try,
                            prompt=prompt,
                            system=system_prompt,
                            images=images,
                            num_ctx=profile.num_ctx,
                            temperature=profile.temperature,
                            top_p=profile.top_p,
                            num_predict=profile.num_predict,
                            format_json=profile.enforce_json,
                            timeout_s=180.0
                        )

                        texto_crudo = resp.get("response", "")
                        self._current_loaded_model = model_to_try

                        # Aplicar Capa 5: Guardrails y Auditoría de salida
                        audit = validar_markdown_estructurado(
                            texto=texto_crudo,
                            longitud_esperada_min=10,
                            longitud_original=longitud_original
                        )

                        # Si se exigía JSON, validar/reparar
                        if profile.enforce_json:
                            es_val, parsed_json, err_json = validar_json_estricto(audit.texto_limpio)
                            if not es_val:
                                rep = reparar_json_incompleto(audit.texto_limpio)
                                if rep is None:
                                    audit.es_valido = False
                                    audit.errores.append(f"JSON inválido irremediable: {err_json}")

                        # Si la salida es válida, retornamos inmediatamente
                        if audit.es_valido:
                            t_total_ms = round((time.perf_counter() - t_start) * 1000, 2)
                            return RoutingDecision(
                                perfil_utilizado=profile.profile_type,
                                modelo_ejecutado=model_to_try,
                                es_fallback=es_fallback,
                                texto_final=audit.texto_limpio,
                                razonamiento_traza=audit.razonamiento_capturado,
                                tiempo_total_ms=t_total_ms,
                                reintentos_realizados=reintentos,
                                auditoria=audit,
                                metadata_gpu={"modelo_residente": self._current_loaded_model}
                            )

                        logger.warning(f"Salida rechazada por auditoría en {model_to_try}: {audit.errores}. Reintentando...")
                        reintentos += 1

                    except ConnectorError as e:
                        logger.error(f"Fallo de conexión o timeout en {model_to_try}: {e}")
                        ultimo_error = e
                        reintentos += 1
                        await asyncio.sleep(0.5)

                es_fallback = True

        t_total_ms = round((time.perf_counter() - t_start) * 1000, 2)
        # Si se agotaron todos los fallbacks sin éxito
        raise RuntimeError(f"Fallo crítico en TaskRouter tras {reintentos} reintentos: {ultimo_error}")
