import pytest
from pathlib import Path
from config import Config
from corrector import dividir_en_chunks, _limpiar_respuesta_llm, CorrectorOllama

def test_dividir_en_chunks_texto_corto():
    texto = "Este es un texto corto que cabe en un solo chunk."
    chunks = dividir_en_chunks(texto, max_chars=1000, overlap=100)
    assert len(chunks) == 1
    assert chunks[0].contenido == texto

def test_dividir_en_chunks_respetando_parrafos():
    p1 = "Párrafo 1 con acentos á, é, í, ó, ú, y ñ." * 20
    p2 = "Párrafo 2 con información crítica sin mojibakes." * 20
    texto = f"{p1}\n\n{p2}"

    # Límite que fuerza la separación pero permite cada párrafo entero
    chunks = dividir_en_chunks(texto, max_chars=len(p1) + 50, overlap=20)
    assert len(chunks) >= 2
    # Comprobar que no se cortó en medio de una palabra aleatoria sino en el salto de párrafo
    assert chunks[0].contenido.startswith("Párrafo 1")
    assert chunks[1].contenido.startswith("Párrafo 2") or "Párrafo 2" in chunks[1].contenido

def test_chunking_preserva_caracteres_especiales():
    texto_especial = "Caracteres: «guillemets», “comillas”, —guión largo—, año 2026."
    chunks = dividir_en_chunks(texto_especial, max_chars=1000, overlap=50)
    assert chunks[0].contenido == texto_especial

def test_chunking_parrafo_gigante_sin_doble_salto():
    """Un párrafo continuo de 5000 caracteres sin \\n\\n se subdivide por oraciones."""
    oracion = "Esta es una oración larga que describe un proceso técnico en detalle. "
    texto_largo = oracion * 50  # ~3500 caracteres
    chunks = dividir_en_chunks(texto_largo, max_chars=1000)

    assert len(chunks) >= 3
    for chk in chunks:
        # Ningún chunk debe exceder el límite máximo
        assert len(chk.contenido) <= 1200

def test_limpieza_envoltorio_markdown_redundante():
    """_limpiar_respuesta_llm remueve wrappers ```markdown ... ``` añadidos por el modelo."""
    raw = "```markdown\n# Titulo\n\nTexto corregido.\n```"
    limpio = _limpiar_respuesta_llm(raw)
    assert limpio == "# Titulo\n\nTexto corregido."

def test_corrector_context_manager(tmp_path: Path):
    """CorrectorOllama soporta with context manager y método close()."""
    config = Config(ruta_entrada=tmp_path, ruta_salida=tmp_path)
    with CorrectorOllama(config) as corrector:
        assert corrector.client is not None
