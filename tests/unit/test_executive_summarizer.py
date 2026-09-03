"""
tests/unit/test_executive_summarizer.py - Pruebas unitarias para el generador de resúmenes ejecutivos C-Level.
"""

from pathlib import Path
import pytest
import respx
import httpx
from core.executive_summarizer import (
    generar_resumen_ejecutivo,
    exportar_resumen_ejecutivo,
    ExecutiveSummaryError
)


@respx.mock
def test_generar_resumen_ejecutivo_con_mock(tmp_path: Path):
    respx.post("http://127.0.0.1:11434/api/generate").mock(
        return_value=httpx.Response(
            200,
            json={
                "response": (
                    "# 📊 RESUMEN EJECUTIVO DIRECTIVO: Proyecto Alfa\n\n"
                    "## 1. 🎯 Tesis Central y Propósito\n"
                    "El proyecto moderniza la infraestructura digital reduciendo costos en 40%.\n\n"
                    "## 2. 🔍 Hallazgos Clave y Puntos Críticos\n"
                    "- **Hallazgo 1:** Alta escalabilidad técnica alcanzada.\n\n"
                    "## 3. 📈 Matriz Cuantitativa e Indicadores\n"
                    "| Métrica | Estado Actual | Impacto |\n"
                    "| VRAM | 4.0 GB | Optimizado 100% |\n\n"
                    "## 4. ⚠️ Matriz de Riesgos\n"
                    "- **Riesgo:** Cuello de botella en red.\n\n"
                    "## 5. 🚀 Plan de Acción\n"
                    "1. Despliegue inmediato."
                )
            }
        )
    )

    texto_prueba = "Este es un reporte estratégico de modernización técnica con análisis detallado."
    res = generar_resumen_ejecutivo(texto_prueba, modelo="qwen2.5:3b")

    assert "RESUMEN EJECUTIVO DIRECTIVO" in res["contenido_markdown"]
    assert res["palabras_resumen"] > 10
    assert res["modelo"] == "qwen2.5:3b"


def test_exportar_resumen_ejecutivo_pdf(tmp_path: Path):
    resumen_data = {
        "contenido_markdown": (
            "# Resumen Ejecutivo\n\n"
            "## Tesis Central\n"
            "Implementación exitosa de plataforma local.\n\n"
            "| Componente | Estado |\n"
            "| Core | 100% |\n"
        )
    }
    ruta_salida = tmp_path / "resumen.pdf"
    res = exportar_resumen_ejecutivo(resumen_data, ruta_salida, formato=".pdf")
    assert res.exists()
    assert res.stat().st_size > 0


def test_resumen_texto_vacio():
    with pytest.raises(ExecutiveSummaryError):
        generar_resumen_ejecutivo("   ")
