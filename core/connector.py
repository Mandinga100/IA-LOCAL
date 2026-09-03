"""
core/connector.py - Capa 1: Conector Ollama con Aceleración de Hardware (Ada SM 8.9).
Cliente asíncrono robusto con soporte para FlashAttention-2, cuantización de KV-Cache,
gestión de timeouts, streaming y reintentos adaptativos bajo gobernanza /ECC.
"""

from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
from logs import logger


class ConnectorError(Exception):
    """Error base de comunicación con el runtime de Ollama."""
    pass


class OllamaConnector:
    """
    Conector asíncrono para Ollama con conocimiento de arquitectura GPU (Ada SM 8.9).
    Gestiona llamadas HTTP directas a la API local sin pasar por librerías intermedias rígidas.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout_default_s: float = 120.0,
        enable_flash_attn: bool = True,
        kv_cache_type: str = "q8_0"
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_default_s = timeout_default_s
        self.enable_flash_attn = enable_flash_attn
        self.kv_cache_type = kv_cache_type

    def _build_options(
        self,
        num_ctx: int = 4096,
        temperature: float = 0.2,
        top_p: float = 0.9,
        num_predict: Optional[int] = None,
        custom_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Construye el payload de opciones inyectando optimizaciones Ada Lovelace."""
        opts: Dict[str, Any] = {
            "num_ctx": num_ctx,
            "temperature": temperature,
            "top_p": top_p,
        }
        if self.enable_flash_attn:
            opts["flash_attn"] = True
        if self.kv_cache_type:
            opts["kv_cache_type"] = self.kv_cache_type
        if num_predict is not None:
            opts["num_predict"] = num_predict

        if custom_options:
            opts.update(custom_options)
        return opts

    async def check_health(self) -> Dict[str, Any]:
        """Verifica la salud del runtime local de Ollama."""
        url = f"{self.base_url}/api/version"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    return {"online": True, "version": data.get("version", "desconocida")}
        except Exception as e:
            logger.debug(f"OllamaConnector health check falló: {e}")
        return {"online": False, "version": None}

    async def list_models(self) -> List[Dict[str, Any]]:
        """Consulta los modelos instalados mediante /api/tags."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("models", [])
                raise ConnectorError(f"Error al listar modelos: HTTP {res.status_code}")
        except httpx.RequestError as e:
            raise ConnectorError(f"Fallo de conexión en list_models: {e}") from e

    async def show_model(self, model_name: str) -> Dict[str, Any]:
        """Obtiene información detallada de un modelo mediante /api/show."""
        url = f"{self.base_url}/api/show"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json={"name": model_name})
                if res.status_code == 200:
                    return res.json()
                raise ConnectorError(f"Error al consultar modelo {model_name}: HTTP {res.status_code}")
        except httpx.RequestError as e:
            raise ConnectorError(f"Fallo de conexión en show_model: {e}") from e

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        images: Optional[List[str]] = None,
        num_ctx: int = 4096,
        temperature: float = 0.2,
        top_p: float = 0.9,
        num_predict: Optional[int] = None,
        format_json: bool = False,
        timeout_s: Optional[float] = None,
        custom_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Ejecuta una inferencia no-streaming mediante /api/generate con soporte multimodal."""
        url = f"{self.base_url}/api/generate"
        timeout = timeout_s or self.timeout_default_s

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": self._build_options(
                num_ctx=num_ctx,
                temperature=temperature,
                top_p=top_p,
                num_predict=num_predict,
                custom_options=custom_options
            )
        }
        if system:
            payload["system"] = system
        if images:
            payload["images"] = images
        if format_json:
            payload["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    return res.json()
                raise ConnectorError(f"Ollama retornó código {res.status_code}: {res.text}")
        except httpx.TimeoutException as e:
            raise ConnectorError(f"Timeout en inferencia con modelo {model} tras {timeout}s: {e}") from e
        except httpx.RequestError as e:
            raise ConnectorError(f"Error de red en inferencia con modelo {model}: {e}") from e

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        num_ctx: int = 4096,
        temperature: float = 0.2,
        top_p: float = 0.9,
        num_predict: Optional[int] = None,
        format_json: bool = False,
        timeout_s: Optional[float] = None,
        custom_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Ejecuta un turno de chat no-streaming mediante /api/chat."""
        url = f"{self.base_url}/api/chat"
        timeout = timeout_s or self.timeout_default_s

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": self._build_options(
                num_ctx=num_ctx,
                temperature=temperature,
                top_p=top_p,
                num_predict=num_predict,
                custom_options=custom_options
            )
        }
        if format_json:
            payload["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    return res.json()
                raise ConnectorError(f"Ollama /api/chat retornó código {res.status_code}: {res.text}")
        except httpx.TimeoutException as e:
            raise ConnectorError(f"Timeout en chat con modelo {model} tras {timeout}s: {e}") from e
        except httpx.RequestError as e:
            raise ConnectorError(f"Error de red en chat con modelo {model}: {e}") from e

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        num_ctx: int = 4096,
        temperature: float = 0.2,
        top_p: float = 0.9,
        num_predict: Optional[int] = None,
        timeout_s: Optional[float] = None,
        custom_options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Transmite la respuesta en streaming chunk a chunk para Open WebUI."""
        url = f"{self.base_url}/api/chat"
        timeout = timeout_s or self.timeout_default_s

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": self._build_options(
                num_ctx=num_ctx,
                temperature=temperature,
                top_p=top_p,
                num_predict=num_predict,
                custom_options=custom_options
            )
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        raise ConnectorError(f"Error streaming en Ollama: HTTP {response.status_code}")
                    import json
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                yield json.loads(line)
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Fallo durante chat_stream con {model}: {e}")
            raise ConnectorError(f"Error en stream de chat: {e}") from e
