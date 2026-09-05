# -*- coding: utf-8 -*-
"""
example_deck.py
Demostración completa de generación de una presentación ejecutiva oficial
para Faro Consulting Group (FaroCG) utilizando fcg_helpers.
"""

import sys
from pathlib import Path

# Añadir scripts al path si se ejecuta directamente
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fcg_helpers import (
    load_fcg_template,
    dated_filename,
    add_portada_slide,
    add_content_slide,
    add_pattern_two_columns,
    add_pattern_metric_cards,
    add_pattern_bullet_circles,
    add_pattern_content_with_stripe,
    add_cierre_slide,
    set_notes,
    validate_layout,
    save_with_normal_view
)

def build_presentation():
    # 1. Cargar plantilla oficial FaroCG 16:9
    prs = load_fcg_template()
    
    # --------------------------------------------------------------------------
    # SLIDE 1: Portada Ejecutiva
    # --------------------------------------------------------------------------
    slide_portada = add_portada_slide(
        prs,
        title="Transformación Digital & Estrategia IA 2026",
        subtitle="Hoja de ruta integral para la modernización de procesos y ventaja competitiva",
        author="Faro Consulting Group — Práctica de Estrategia Digital",
        date="Septiembre 2026",
        client="Dirección General & Comité Ejecutivo"
    )
    set_notes(slide_portada, "Abrir la sesión enfatizando el objetivo estratégico: convertir las capacidades de IA local y automatización en eficiencia medible y ROI en 6 meses.")
    validate_layout(slide_portada)
    
    # --------------------------------------------------------------------------
    # SLIDE 2: Resumen Ejecutivo (Cards 2 Columnas)
    # --------------------------------------------------------------------------
    slide_resumen = add_content_slide(
        prs,
        title="Diagnóstico Estratégico y Oportunidad de Mercado",
        subtitle="Evaluación del estado actual de operaciones frente a benchmarks del sector",
        category="01. DIAGNÓSTICO EJECUTIVO"
    )
    
    col1_bullets = [
        "Sistemas heredados generan un 38% de sobrecosto operativo en tareas repetitivas.",
        "Dispersión de información documental crítica retrasa la toma de decisiones en un promedio de 4.2 días.",
        "Riesgo de cumplimiento normativo ante normativas crecientes de gobernanza y privacidad de datos."
    ]
    
    col2_bullets = [
        "Implementación de arquitectura IA soberana local con control absoluto de privacidad y seguridad.",
        "Automatización de auditorías y procesamiento de contratos reduciendo tiempos a minutos.",
        "Consolidación de un ecosistema escalable de skills que potencia al equipo multidisciplinario."
    ]
    
    add_pattern_two_columns(
        slide_resumen,
        col1_title="Desafíos Operativos Actuales",
        col1_bullets=col1_bullets,
        col2_title="Propuesta de Valor & Solución",
        col2_bullets=col2_bullets
    )
    set_notes(slide_resumen, "Puntualizar que la columna izquierda representa costos hundidos actuales y la derecha el ahorro proyectado.")
    validate_layout(slide_resumen)
    
    # --------------------------------------------------------------------------
    # SLIDE 3: Métricas y KPIs de Impacto (Metric Cards)
    # --------------------------------------------------------------------------
    slide_kpi = add_content_slide(
        prs,
        title="Impacto Proyectado y Retorno de Inversión (ROI)",
        subtitle="Métricas cuantitativas estimadas al cabo del primer año de implementación",
        category="02. IMPACTO & RENDIMIENTO"
    )
    
    kpis = [
        {
            "number": "+65%",
            "label": "Velocidad Operativa",
            "desc": "Aceleración en el análisis forense y auditoría documental integral."
        },
        {
            "number": "4.8x",
            "label": "Retorno de Inversión",
            "desc": "ROI cuantificado a 12 meses basado en reducción de horas hombre y licencias externas."
        },
        {
            "number": "100%",
            "label": "Soberanía de Datos",
            "desc": "Procesamiento totalmente local on-premise sin fuga a nubes de terceros."
        },
        {
            "number": "-40%",
            "label": "Margen de Error",
            "desc": "Disminución de discrepancias contractuales mediante validación automatizada."
        }
    ]
    
    add_pattern_metric_cards(slide_kpi, kpis)
    set_notes(slide_kpi, "Detallar que el 100% de soberanía es clave para el área legal y de auditoría interna.")
    validate_layout(slide_kpi)
    
    # --------------------------------------------------------------------------
    # SLIDE 4: Metodología de Implementación (Bullet Circles)
    # --------------------------------------------------------------------------
    slide_fases = add_content_slide(
        prs,
        title="Fases de la Metodología FaroCG",
        subtitle="Plan de despliegue progresivo estructurado en cuatro hitos críticos",
        category="03. PLAN DE TRABAJO"
    )
    
    fases = [
        {
            "step": "01",
            "title": "Auditoría & Descubrimiento de Infraestructura (Semanas 1-2)",
            "desc": "Levantamiento de capacidades de cómputo local, modelos compatibles y flujos prioritarios."
        },
        {
            "step": "02",
            "title": "Despliegue de Gateway & Agentes Especializados (Semanas 3-5)",
            "desc": "Configuración del entorno soberano, integración de skills a la medida y bases vectoriales."
        },
        {
            "step": "03",
            "title": "Piloto Operativo Multidocumental (Semanas 6-8)",
            "desc": "Pruebas de estrés de análisis documental en paralelo con retroalimentación en tiempo real."
        },
        {
            "step": "04",
            "title": "Pase a Producción & Capacitación Directiva (Semanas 9-10)",
            "desc": "Transferencia metodológica de mejores prácticas de prompting y gobernanza continua."
        }
    ]
    
    add_pattern_bullet_circles(slide_fases, fases)
    set_notes(slide_fases, "Subrayar que cada fase cuenta con entregables y criterios de aceptación formalmente auditados.")
    validate_layout(slide_fases)
    
    # --------------------------------------------------------------------------
    # SLIDE 5: Conclusiones Estratégicas (Contenido con Franja & Takeaway)
    # --------------------------------------------------------------------------
    slide_concl = add_content_slide(
        prs,
        title="Recomendaciones Finales del Consejo Consultor",
        subtitle="Síntesis directiva para la aprobación del presupuesto y calendario",
        category="04. CONCLUSIÓN ESTRATÉGICA"
    )
    
    parrafos = [
        "La adopción de una arquitectura de IA local privada representa la ruta óptima para maximizar la seguridad informática y eliminar costos recurrentes de API propietarias.",
        "La estandarización de herramientas como 'fcg-ppt' asegura coherencia de marca ininterrumpida y un estándar corporativo de excelencia en cada interacción con stakeholders."
    ]
    
    takeaway = "La aprobación del presupuesto en Q3 asegura la captura de eficiencias operativas antes del cierre fiscal, consolidando a la organización como líder tecnológico en su industria."
    
    add_pattern_content_with_stripe(
        slide_concl,
        headline="La Modernización No Es Un Costo, Es Una Ventaja Competitiva Defensiva",
        paragraphs=parrafos,
        key_takeaway=takeaway
    )
    set_notes(slide_concl, "Cerrar con llamado explícito a la acción solicitando la firma del acta de inicio de proyecto.")
    validate_layout(slide_concl)
    
    # --------------------------------------------------------------------------
    # SLIDE 6: Diapositiva de Cierre
    # --------------------------------------------------------------------------
    slide_cierre = add_cierre_slide(
        prs,
        title="Gracias",
        subtitle="Faro Consulting Group — Guiando Decisiones Estratégicas con Inteligencia y Visión",
        contact_info={
            "Web": "www.faroconsulting.com",
            "Contacto": "contacto@faroconsulting.com",
            "Sede": "Santiago, Chile"
        }
    )
    validate_layout(slide_cierre)
    
    # Guardar presentación
    out_filename = dated_filename("presentacion_faro_ejemplo", "pptx")
    out_dir = Path(__file__).resolve().parent.parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / out_filename
    
    save_with_normal_view(prs, out_path)
    return out_path

if __name__ == "__main__":
    generated_path = build_presentation()
    print(f"[EXITO] Presentacion generada en {generated_path}")
