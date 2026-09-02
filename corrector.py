"""
corrector.py - Motor de corrección semántica mediante IA local (Ollama).
Gestiona chunking semántico por párrafos (\n\n), solapamiento seguro y reintentos.
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
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

def dividir_en_chunks(
    texto: str,
    max_chars: int = 3500,
    overlap: int = 200
) -> List[ChunkTexto]:
    """
    Divide un texto en chunks semánticos respetando saltos de párrafo doble (\n\n).
    Garantiza que no se dividan oraciones ni tablas arbitrariamente.
    """
    if not texto.strip():
        return []
        
    if len(texto) <= max_chars:
        return [ChunkTexto(indice=1, total_chunks=1, contenido=texto)]

    parrafos = texto.split("\n\n")
    chunks_str: List[str] = []
    chunk_actual: List[str] = []
    longitud_actual = 0

    for parrafo in parrafos:
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

class CorrectorOllama:
    """Cliente robusto para inferencia de corrección con Ollama."""

    def __init__(self, config: Config, ruta_prompts: Path | str = "prompts.json") -> None:
        self.config = config
        self.prompts = self._cargar_prompts(Path(ruta_prompts))
        self.client = httpx.Client(timeout=self.config.timeout_inferencia_segundos)

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
                    texto_corregido = data.get("response", "").strip()
                    # Limpiar posibles delimitadores que el modelo haya repetido
                    texto_corregido = texto_corregido.replace("<documento_a_corregir>", "").replace("</documento_a_corregir>", "").strip()
                    return texto_corregido
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
                    texto_fb = data_fb.get("response", "").strip()
                    texto_fb = texto_fb.replace("<documento_a_corregir>", "").replace("</documento_a_corregir>", "").strip()
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
