"""
tests/unit/test_pureza_documental.py - Pruebas unitarias para el Protocolo Zero-Chatter.
"""

from core.pureza_documental import (
    eliminar_etiquetas_razonamiento,
    limpiar_preambulos_conversacionales,
    limpiar_epilogos_conversacionales,
    sanitizar_texto_documental,
    calcular_indice_pureza
)


class TestPurezaDocumental:
    def test_eliminar_etiquetas_razonamiento(self) -> None:
        texto = "<think>Analizando documento...</think># Título Real\nContenido"
        resultado = eliminar_etiquetas_razonamiento(texto)
        assert resultado == "# Título Real\nContenido"
        assert "<think>" not in resultado

    def test_limpiar_preambulo_voy_a_corregir(self) -> None:
        texto = "Voy a corregir el documento a continuación:\n\n# Manual de Usuario\nEste es el contenido."
        resultado = limpiar_preambulos_conversacionales(texto)
        assert resultado.startswith("# Manual de Usuario")
        assert "Voy a corregir" not in resultado

    def test_limpiar_chatter_complejo_detalles_tecnicos(self) -> None:
        texto = (
            "### Detalles Técnicos del Procesamiento\n"
            "- Formato Original: PDF\n"
            "- Procesamiento Realizado: Reconstrucción en Markdown\n"
            "- Versión: 1.0.3-beta (pero en realidad es 0.9.1)\n\n"
            "### Documento Reconstruido\n\n"
            "# Arquitectura de Software\n\n"
            "El sistema SaaS cuenta con 5 módulos operativos."
        )
        resultado = limpiar_preambulos_conversacionales(texto)
        assert resultado.startswith("# Arquitectura de Software")
        assert "Detalles Técnicos" not in resultado
        assert "1.0.3-beta" not in resultado

    def test_limpiar_epilogo_si_necesitas_mas_detalles(self) -> None:
        texto = (
            "# Especificación Técnica\n\n"
            "Párrafo final de la especificación.\n\n"
            "Si necesitas más detalles o tienes alguna otra solicitud, no dudes en preguntar."
        )
        resultado = limpiar_epilogos_conversacionales(texto)
        assert resultado.endswith("Párrafo final de la especificación.")
        assert "no dudes en preguntar" not in resultado

    def test_sanitizar_texto_documental_completo(self) -> None:
        texto_sucio = (
            "<think>Razonando en background</think>\n"
            "¡Hola! Claro, voy a corregir el documento de inmediato:\n\n"
            "# Política de Privacidad\n\n"
            "Esta es la política legal estricta.\n\n"
            "Espero que esta corrección te sea de gran utilidad. Saludos cordiales."
        )
        limpio = sanitizar_texto_documental(texto_sucio)
        assert limpio == "# Política de Privacidad\n\nEsta es la política legal estricta."
        assert "¡Hola!" not in limpio
        assert "Espero que" not in limpio

    def test_calcular_indice_pureza(self) -> None:
        original = "Chatter inicial # Titulo"
        sanitizado = "# Titulo"
        score = calcular_indice_pureza(original, sanitizado)
        assert 0.0 < score < 100.0

    def test_es_respuesta_de_rechazo_detecta_incapacidad(self) -> None:
        from core.pureza_documental import es_respuesta_de_rechazo

        rechazo_tipico = (
            "Lo siento, pero como asistente de inteligencia artificial, no tengo la capacidad "
            "de analizar o corregir documentos. Sin embargo, puedo ayudarte a crear un nuevo documento. "
            "Por favor, proporciona el contenido del documento que deseas que se revise y corrija."
        )
        assert es_respuesta_de_rechazo(rechazo_tipico) is True

        rechazo_ingles = "I cannot analyze or correct the attached document as an AI language model."
        assert es_respuesta_de_rechazo(rechazo_ingles) is True

        texto_valido = (
            "# Documentación Técnica - Prueba de Calidad\n\n"
            "## Introducción\n"
            "Este documento proporciona la guía técnica del sistema SaaS multi-tenant.\n\n"
            "### Características Principales:\n"
            "- Soporte multi-tenant\n- Autenticación JWT"
        )
        assert es_respuesta_de_rechazo(texto_valido) is False

    def test_sanitizar_texto_con_simulacion_generacion_archivo_y_metatextos(self) -> None:
        """Verifica que frases de 'Generando archivo PDF...', notas de campos pendientes y resúmenes sean purgados."""
        texto = (
            "Este resumen proporciona una visión clara y organizada de los elementos clave del documento, asegurando\n"
            "que la información sea precisa y profesional.\n"
            "---\n"
            "# Contrato de Servicios\n\n"
            "El proveedor entregará los módulos en fecha acordada.\n\n"
            "---\n"
            "Nota: Los campos [pendiente] deben ser completados con la información correspondiente.\n"
            "---\n"
            "Generando archivo PDF...\n"
            "[El archivo PDF se generará automáticamente a partir de esta respuesta.]\n"
            "---\n"
            "Archivo PDF Generado:\n"
            "[Archivo PDF adjunto con el resumen formateado en formato PDF]"
        )
        limpio = sanitizar_texto_documental(texto)
        assert limpio.startswith("# Contrato de Servicios")
        assert "Este resumen proporciona una visión clara" not in limpio
        assert "Nota: Los campos" not in limpio
        assert "Generando archivo PDF" not in limpio
        assert "[El archivo PDF se generará automáticamente" not in limpio
        assert "Archivo PDF Generado" not in limpio
        assert "[Archivo PDF adjunto" not in limpio

