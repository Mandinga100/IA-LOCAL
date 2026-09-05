import pytest
import respx
import httpx
from unittest.mock import patch, call
from corrector import CorrectorOllama, InferenciaError
from config import Config


@respx.mock
def test_corrector_exitoso():
    cfg = Config(ollama_url="http://localhost:11434", modelo="qwen2.5:7b")
    corrector = CorrectorOllama(cfg)

    # Mockear endpoint de Ollama /api/generate
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(200, json={"response": "Texto corregido sin errores ortográficos."})
    )

    resultado = corrector.corregir_texto("Texto con herrores.", tipo_documento="general")
    assert resultado == "Texto corregido sin errores ortográficos."


@respx.mock
def test_corrector_falla_servidor_lanza_excepcion():
    cfg = Config(ollama_url="http://localhost:11434", modelo="qwen2.5:7b")
    corrector = CorrectorOllama(cfg)

    # Simular caída 500 persistente en Ollama
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(500, text="Internal CUDA Error")
    )

    with pytest.raises(InferenciaError):
        corrector.corregir_texto("Texto de prueba.", tipo_documento="general")


# ---------------------------------------------------------------------------
# Sprint 2-D: Backoff exponencial
# ---------------------------------------------------------------------------
@respx.mock
def test_backoff_exponencial_tiempos_correctos():
    """
    Verifica que time.sleep se llama con 2.0s y 4.0s entre reintentos fallidos.
    Con max_reintentos=3: intento 1 -> sleep(2.0), intento 2 -> sleep(4.0), intento 3 -> raise.
    """
    cfg = Config(
        ollama_url="http://localhost:11434",
        modelo="qwen2.5:7b",
        max_reintentos_inferencia=3,
    )
    corrector = CorrectorOllama(cfg)
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(500, text="Error persistente")
    )

    with patch("corrector.time.sleep") as mock_sleep:
        with pytest.raises(InferenciaError):
            corrector.corregir_texto("Texto.", tipo_documento="general")

    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0] == call(2.0)
    assert mock_sleep.call_args_list[1] == call(4.0)


@respx.mock
def test_backoff_no_ejecuta_sleep_en_ultimo_intento():
    """
    En el ultimo intento no se debe llamar a time.sleep antes de lanzar InferenciaError.
    Con max_reintentos=1: 1 intento -> sin sleep -> raise.
    """
    cfg = Config(
        ollama_url="http://localhost:11434",
        modelo="qwen2.5:7b",
        max_reintentos_inferencia=1,
    )
    corrector = CorrectorOllama(cfg)
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(500, text="Error")
    )

    with patch("corrector.time.sleep") as mock_sleep:
        with pytest.raises(InferenciaError):
            corrector.corregir_texto("Texto.", tipo_documento="general")

    mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# Sprint 2-D: Fallback de modelo
# ---------------------------------------------------------------------------
@respx.mock
def test_fallback_modelo_responde_exitosamente():
    """
    Cuando el modelo principal agota reintentos y hay modelo_fallback configurado,
    el resultado debe provenir del modelo de fallback.
    """
    cfg = Config(
        ollama_url="http://localhost:11434",
        modelo="qwen2.5:7b",
        modelo_fallback="llama3.1:8b",
        max_reintentos_inferencia=1,
    )
    corrector = CorrectorOllama(cfg)

    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        body = request.content
        if b"qwen2.5:7b" in body:
            return httpx.Response(500, text="CUDA OOM")
        if b"llama3.1:8b" in body:
            return httpx.Response(200, json={"response": "Texto via fallback llama."})
        return httpx.Response(500, text="Unknown")

    respx.post("http://localhost:11434/api/generate").mock(side_effect=side_effect)

    with patch("corrector.time.sleep"):
        resultado = corrector.corregir_texto("Texto.", tipo_documento="general")

    assert resultado == "Texto via fallback llama."


@respx.mock
def test_fallback_modelo_tambien_falla_lanza_inferencia_error():
    """
    Si tanto el modelo principal como el fallback fallan,
    InferenciaError debe incluir ambos modelos en el mensaje.
    """
    cfg = Config(
        ollama_url="http://localhost:11434",
        modelo="qwen2.5:7b",
        modelo_fallback="llama3.1:8b",
        max_reintentos_inferencia=1,
    )
    corrector = CorrectorOllama(cfg)
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(500, text="Fallo total")
    )

    with patch("corrector.time.sleep"):
        with pytest.raises(InferenciaError) as exc_info:
            corrector.corregir_texto("Texto.", tipo_documento="general")

    assert "qwen2.5:7b" in str(exc_info.value)
    assert "llama3.1:8b" in str(exc_info.value)


@respx.mock
def test_sin_fallback_configurado_lanza_excepcion_simple():
    """
    Sin modelo_fallback, InferenciaError se lanza con el mensaje estandar
    sin mencion de fallback.
    """
    cfg = Config(
        ollama_url="http://localhost:11434",
        modelo="qwen2.5:7b",
        modelo_fallback=None,
        max_reintentos_inferencia=1,
    )
    corrector = CorrectorOllama(cfg)
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(500, text="Error")
    )

    with patch("corrector.time.sleep"):
        with pytest.raises(InferenciaError) as exc_info:
            corrector.corregir_texto("Texto.", tipo_documento="general")

    assert "fallback" not in str(exc_info.value).lower()
