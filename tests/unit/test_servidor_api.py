"""
tests/unit/test_servidor_api.py
Suite de pruebas unitarias para el API Gateway y Servidor Web Local (FastAPI).
"""

import io
import pytest
import respx
import httpx
from pathlib import Path
from fastapi.testclient import TestClient
from servidor_api import app, UPLOAD_DIR, SALIDA_DIR

client = TestClient(app)

class TestServidorApi:
    def test_root_entrega_index_html(self) -> None:
        """GET / devuelve el frontend HTML con status 200."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Plataforma IA Local" in response.text
        assert "text/html" in response.headers["content-type"]

    def test_api_salud_responde_json(self) -> None:
        """GET /api/salud retorna estado y lista de modelos."""
        response = client.get("/api/salud")
        assert response.status_code == 200
        data = response.json()
        assert "estado" in data
        assert "ollama" in data
        assert "modelos_disponibles" in data

    @respx.mock
    def test_api_procesar_archivo_texto_exitoso(self) -> None:
        """POST /api/procesar convierte, infiere con IA y devuelve el resultado."""
        respx.post("http://localhost:11434/api/generate").mock(
            return_value=httpx.Response(
                200,
                json={"response": "Texto corregido exitosamente por el modelo de IA local."}
            )
        )

        contenido = "Texto con faltas ortograficas para correccion."
        archivo_simulado = io.BytesIO(contenido.encode("utf-8"))

        response = client.post(
            "/api/procesar",
            files={"archivo": ("documento_prueba.txt", archivo_simulado, "text/plain")},
            data={"tipo_documento": "general", "modelo": "qwen2.5:3b", "chunk_size": "1800"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exito"] is True
        assert data["nombre_archivo"] == "documento_prueba.txt"
        assert "Texto corregido exitosamente" in data["texto_corregido"]
        assert data["archivo_descarga"] == "documento_prueba.txt"

    def test_api_procesar_rechaza_binario_ejecutable_mz(self) -> None:
        """POST /api/procesar bloquea archivos con firma de ejecutable PE (MZ)."""
        binario_malicioso = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff")
        response = client.post(
            "/api/procesar",
            files={"archivo": ("payload.docx", binario_malicioso, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"tipo_documento": "general", "modelo": "qwen2.5:3b"}
        )

        assert response.status_code == 400
        assert "firmas ejecutables" in response.json()["detail"]

    def test_api_descargar_archivo_existente(self) -> None:
        """GET /api/descargar/{nombre} descarga el archivo generado."""
        test_file = SALIDA_DIR / "descarga_test.txt"
        test_file.write_text("Contenido de prueba descargable", encoding="utf-8")

        response = client.get(f"/api/descargar/{test_file.name}")
        assert response.status_code == 200
        assert response.text == "Contenido de prueba descargable"

        test_file.unlink(missing_ok=True)

    def test_api_descargar_archivo_inexistente_retorna_404(self) -> None:
        """GET /api/descargar/no_existe.docx devuelve 404 Not Found."""
        response = client.get("/api/descargar/archivo_fantasma_12345.docx")
        assert response.status_code == 404

    def test_api_ver_documento_pdf_existente(self) -> None:
        """GET /api/ver/{nombre_archivo} entrega página HTML con visor de PDF."""
        salida_dir = Path("datos/salida_web")
        salida_dir.mkdir(parents=True, exist_ok=True)
        test_pdf = salida_dir / "prueba_visor.pdf"
        test_pdf.write_bytes(b"%PDF-1.4 test")

        response = client.get("/api/ver/prueba_visor.pdf")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Previsualizador | prueba_visor.pdf" in response.text
        assert 'iframe src="/api/descargar/prueba_visor.pdf#toolbar=1"' in response.text
        test_pdf.unlink(missing_ok=True)

    def test_api_ver_documento_inexistente_retorna_404(self) -> None:
        """GET /api/ver/{nombre_archivo} devuelve 404 si el archivo no existe."""
        response = client.get("/api/ver/archivo_no_existente.pdf")
        assert response.status_code == 404

    def test_api_asset_inexistente_retorna_404(self) -> None:
        """GET /api/asset/{doc}/{archivo} devuelve 404 si no existe."""
        response = client.get("/api/asset/doc123/img_falsa.png")
        assert response.status_code == 404

    def test_api_abrir_documento_inexistente_retorna_404(self) -> None:
        """GET /api/abrir/{nombre} devuelve 404 si el archivo no existe."""
        response = client.get("/api/abrir/inexistente_9876.docx")
        assert response.status_code == 404

