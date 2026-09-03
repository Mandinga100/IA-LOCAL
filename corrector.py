"""
corrector.py - Motor de corrección semántica mediante IA local (Ollama).
Gestiona chunking semántico jerárquico (párrafos -> oraciones), solapamiento seguro, reintentos y fallback.
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Any
import httpx

from config import Config
from logs import logger

class InferenciaError(Exception):
    """Excepción de dominio lanzada ante fallos no recuperables con Ollama."""
    pass

@dataclass(frozen=True)
class ChunkTexto:
    """Representa un fragmento de texto con contexto para inferencia."""
    indice: int
    total_chunks: int
    contenido: str

def _subdividir_parrafo_largo(parrafo: str, max_chars: int) -> List[str]:
    """Subdivide un párrafo continuo que excede max_chars utilizando oraciones o líneas."""
    if len(parrafo) <= max_chars:
        return [parrafo]

    # Intentar división por saltos de línea simples
    if "\n" in parrafo:
        sub_lineas = parrafo.split("\n")
        bloques: List[str] = []
        actual: List[str] = []
        long_actual = 0
        for linea in sub_lineas:
            tam = len(linea) + 1
            if long_actual + tam > max_chars and actual:
                bloques.append("\n".join(actual))
                actual = [linea]
                long_actual = tam
            else:
                actual.append(linea)
                long_actual += tam
        if actual:
            bloques.append("\n".join(actual))
        return bloques

    # Intentar división por oraciones (punto seguido)
    partes = parrafo.split(". ")
    bloques = []
    actual = []
    long_actual = 0

    for parte in partes:
        oracion = parte + ". "
        tam = len(oracion)
        if long_actual + tam > max_chars and actual:
            bloques.append("".join(actual).strip())
            actual = [oracion]
            long_actual = tam
        else:
            actual.append(oracion)
            long_actual += tam

    if actual:
        bloques.append("".join(actual).strip())

    return bloques if bloques else [parrafo]

def dividir_en_chunks(
    texto: str,
    max_chars: int = 3500,
    overlap: int = 200
) -> List[ChunkTexto]:
    """
    Divide un texto en chunks semánticos respetando saltos de párrafo (\n\n)
    y subdividiendo párrafos anómalos que excedan max_chars.
    """
    if not texto.strip():
        return []

    if len(texto) <= max_chars:
        return [ChunkTexto(indice=1, total_chunks=1, contenido=texto)]

    parrafos_crudos = texto.split("\n\n")
    parrafos_procesados: List[str] = []

    for p in parrafos_crudos:
        if len(p) > max_chars:
            parrafos_procesados.extend(_subdividir_parrafo_largo(p, max_chars))
        else:
            parrafos_procesados.append(p)

    chunks_str: List[str] = []
    chunk_actual: List[str] = []
    longitud_actual = 0

    for parrafo in parrafos_procesados:
        tam_parrafo = len(parrafo) + 2  # +2 por \n\n

        if longitud_actual + tam_parrafo > max_chars and chunk_actual:
            chunks_str.append("\n\n".join(chunk_actual))
            chunk_actual = [parrafo]
            longitud_actual = tam_parrafo
        else:
            chunk_actual.append(parrafo)
            longitud_actual += tam_parrafo

    if chunk_actual:
        chunks_str.append("\n\n".join(chunk_actual))

    total = len(chunks_str)
    return [
        ChunkTexto(indice=i + 1, total_chunks=total, contenido=contenido)
        for i, contenido in enumerate(chunks_str)
    ]

def _limpiar_respuesta_llm(texto: str) -> str:
    """Elimina delimitadores de prompt o envoltorios markdown redundantes generados por el LLM."""
    limpio = texto.replace("<documento_a_corregir>", "").replace("</documento_a_corregir>", "").strip()

    # Desempaquetar si el modelo envolvió toda la respuesta en un bloque ```markdown ... ```
    if limpio.startswith("```markdown\n") and limpio.endswith("\n```"):
        limpio = limpio[len("```markdown\n"):-len("\n```")].strip()
    elif limpio.startswith("```\n") and limpio.endswith("\n```"):
        limpio = limpio[len("```\n"):-len("\n```")].strip()

    return limpio

class CorrectorOllama:
    """Cliente robusto para inferencia de corrección con Ollama y gestión de ciclo de vida."""

    def __init__(self, config: Config, ruta_prompts: Path | str = "prompts.json") -> None:
        self.config = config
        self.prompts = self._cargar_prompts(Path(ruta_prompts))
        self.client = httpx.Client(timeout=self.config.timeout_inferencia_segundos)

    def close(self) -> None:
        """Cierra el cliente HTTP y libera conexiones de red subyacentes."""
        self.client.close()

    def __enter__(self) -> "CorrectorOllama":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def _cargar_prompts(self, ruta: Path) -> dict:
        if not ruta.exists():
            logger.warning(f"Archivo de prompts no encontrado en {ruta}. Usando prompt general base.")
            return {
                "general": "Eres un asistente experto en lengua española. Corrige ortografía y estilo manteniendo formato Markdown."
            }
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)

    def _ejecutar_inferencia_chunk(self, chunk: str, prompt_sistema: str) -> str:
        url = f"{self.config.ollama_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.config.modelo,
            "system": prompt_sistema,
            "prompt": f"<documento_a_corregir>\n{chunk}\n</documento_a_corregir>",
            "stream": False,
            "options": {
                "temperature": self.config.temperatura,
                "top_p": self.config.top_p,
                "num_ctx": self.config.num_ctx
            }
        }

        intentos = 0
        backoff = 2.0

        while intentos < self.config.max_reintentos_inferencia:
            try:
                intentos += 1
                logger.debug(f"Llamando a Ollama (intento {intentos}/{self.config.max_reintentos_inferencia})...")
                response = self.client.post(url, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    raw_text = data.get("response", "").strip()
                    return _limpiar_respuesta_llm(raw_text)
                else:
                    logger.warning(f"Error HTTP {response.status_code} desde Ollama: {response.text}")
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as e:
                logger.warning(f"Fallo de conexión o timeout con Ollama en intento {intentos}: {e}")

            if intentos < self.config.max_reintentos_inferencia:
                time.sleep(backoff)
                backoff *= 2.0

        # --- Fallback de modelo ---
        if self.config.modelo_fallback:
            modelo_fallback = self.config.modelo_fallback
            logger.warning(
                f"Modelo principal '{self.config.modelo}' agotó {self.config.max_reintentos_inferencia} "
                f"intentos. Activando fallback con '{modelo_fallback}'."
            )
            payload_fallback = {**payload, "model": modelo_fallback}
            try:
                response_fb = self.client.post(url, json=payload_fallback)
                if response_fb.status_code == 200:
                    data_fb = response_fb.json()
                    raw_fb = data_fb.get("response", "").strip()
                    texto_fb = _limpiar_respuesta_llm(raw_fb)
                    logger.info(f"Fallback '{modelo_fallback}' respondió exitosamente.")
                    return texto_fb
                else:
                    logger.error(
                        f"Fallback '{modelo_fallback}' también falló con HTTP {response_fb.status_code}."
                    )
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as e:
                logger.error(f"Fallback '{modelo_fallback}' lanzó excepción de conexión: {e}")

            raise InferenciaError(
                f"No fue posible obtener respuesta de Ollama tras {self.config.max_reintentos_inferencia} "
                f"intentos con '{self.config.modelo}' y 1 intento de fallback con '{modelo_fallback}'."
            )

        raise InferenciaError(f"No fue posible obtener respuesta de Ollama tras {self.config.max_reintentos_inferencia} intentos.")

    def corregir_texto(self, texto: str, tipo_documento: str = "general") -> str:
        """
        Corrige un texto completo dividiéndolo en chunks semánticos y procesando cada uno.
        """
        if not texto.strip():
            return texto

        prompt_sistema = self.prompts.get(tipo_documento, self.prompts.get("general", ""))
        chunks = dividir_en_chunks(texto, max_chars=self.config.chunk_size, overlap=self.config.chunk_overlap)

        logger.info(f"Procesando texto dividido en {len(chunks)} chunk(s)...")
        resultados_chunks: List[str] = []

        for chk in chunks:
            logger.debug(f"Procesando chunk {chk.indice}/{chk.total_chunks}...")
            chunk_corregido = self._ejecutar_inferencia_chunk(chk.contenido, prompt_sistema)
            resultados_chunks.append(chunk_corregido)

        return "\n\n".join(resultados_chunks)
