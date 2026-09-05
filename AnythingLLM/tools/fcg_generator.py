# -*- coding: utf-8 -*-
"""
fcg_generator.py
Script CLI puente para AnythingLLM: genera presentaciones ejecutivas 16:9
con identidad visual Faro Consulting Group a partir de argumentos JSON o CLI.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Agregar scripts de helpers al path
current_dir = Path(__file__).resolve().parent
potential_paths = [
    current_dir,
    current_dir / "scripts",
    current_dir.parent / ".agents" / "skills" / "fcg-ppt" / "scripts",
    current_dir.parent / "skills" / "fcg-ppt" / "scripts",
    Path(r"c:\Users\mandi\Documents\Proyectos\Plataforma IA local\.agents\skills\fcg-ppt\scripts"),
    Path(r"c:\Users\mandi\Documents\Proyectos\Plataforma IA local\skills\fcg-ppt\scripts"),
]

for p in potential_paths:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

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

def generate_presentation(data: dict) -> dict:
    title = data.get("title", "Presentación Ejecutiva Faro Consulting Group")
    subtitle = data.get("subtitle", "Consultoría Estratégica & Análisis Integral")
    category = data.get("category", "ESTRATEGIA & DIRECCIÓN")
    client = data.get("client", "Dirección General")
    summary = data.get("summary", "")
    action = data.get("action", "generate_deck")
    output_dir_str = data.get("output_dir") or str(current_dir / "output")
    
    out_dir = Path(output_dir_str)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Cargar plantilla 16:9 oficial
    template_path = current_dir / "assets" / "template_fcg.pptx"
    prs = load_fcg_template(template_path=template_path if template_path.exists() else None)
    
    # SLIDE 1: Portada
    slide_1 = add_portada_slide(
        prs,
        title=title,
        subtitle=subtitle,
        author="Faro Consulting Group",
        client=client
    )
    set_notes(slide_1, f"Presentación generada automáticamente por Skill Faro Consulting para {client}.")
    validate_layout(slide_1)
    
    # Parsear puntos del resumen si existen
    bullets = []
    if isinstance(summary, list):
        bullets = [str(b).strip() for b in summary if str(b).strip()]
    elif isinstance(summary, str) and summary.strip():
        # Separar por saltos de línea o puntos
        lines = [line.strip("- •* \t") for line in summary.split("\n") if line.strip("- •* \t")]
        bullets = lines if lines else [summary]
    else:
        bullets = [
            "Optimización de procesos operativos mediante inteligencia artificial y automatización.",
            "Consolidación de estándares de seguridad y soberanía documental.",
            "Alineamiento de gobernanza de datos y reducción de costos recurrentes."
        ]
        
    mid = max(1, len(bullets) // 2)
    col1_items = bullets[:mid] if bullets[:mid] else ["Evaluación diagnóstica y auditoría de estado del arte."]
    col2_items = bullets[mid:] if bullets[mid:] else ["Implementación táctica y control de calidad continuo."]

    # SLIDE 2: Diagnóstico y Hallazgos (Cards 2 Columnas)
    slide_2 = add_content_slide(
        prs,
        title="Diagnóstico y Hallazgos Principales",
        subtitle="Síntesis de puntos críticos evaluados",
        category=f"01. {category.upper()}"
    )
    add_pattern_two_columns(
        slide_2,
        col1_title="Puntos de Atención / Desafíos",
        col1_bullets=col1_items,
        col2_title="Recomendaciones & Respuestas",
        col2_bullets=col2_items
    )
    validate_layout(slide_2)
    
    # SLIDE 3: Métricas de Desempeño
    slide_3 = add_content_slide(
        prs,
        title="Métricas Clave & Indicadores de Impacto",
        subtitle="Proyección cuantitativa de rendimiento",
        category="02. IMPACTO CUANTIFICABLE"
    )
    metrics = [
        {"number": "+60%", "label": "Eficiencia", "desc": "Aceleración de análisis documental."},
        {"number": "100%", "label": "Soberanía", "desc": "Privacidad y confidencialidad total."},
        {"number": "-45%", "label": "Tiempos Ciclo", "desc": "Reducción en resolución de consultas."},
        {"number": "4.5x", "label": "Retorno ROI", "desc": "Estimación a 12 meses de operación."}
    ]
    add_pattern_metric_cards(slide_3, metrics)
    validate_layout(slide_3)
    
    # SLIDE 4: Plan de Trabajo Metodológico (Bullet circles)
    slide_4 = add_content_slide(
        prs,
        title="Hoja de Ruta Metodológica",
        subtitle="Hitos secuenciales de ejecución con garantía FaroCG",
        category="03. PLAN DE TRABAJO"
    )
    fases = [
        {"step": "01", "title": "Auditoría & Descubrimiento", "desc": "Levantamiento exhaustivo de requerimientos y riesgos."},
        {"step": "02", "title": "Diseño de Arquitectura", "desc": "Definición de modelos, parámetros y controles de calidad."},
        {"step": "03", "title": "Despliegue & Validación", "desc": "Implementación en entorno seguro y pruebas de estrés."},
        {"step": "04", "title": "Operación & Gobierno", "desc": "Monitoreo continuo y transferencia de mejores prácticas."}
    ]
    add_pattern_bullet_circles(slide_4, fases)
    validate_layout(slide_4)
    
    # SLIDE 5: Conclusiones Estratégicas (Franja + Takeaway)
    slide_5 = add_content_slide(
        prs,
        title="Conclusiones y Siguientes Pasos",
        subtitle="Decisiones requeridas para la captura inmediata de valor",
        category="04. RECOMENDACIÓN EJECUTIVA"
    )
    concl_paras = [
        f"El proyecto presentado bajo la dirección de {client} cuenta con viabilidad técnica e impacto inmediato.",
        "La adopción del estándar Faro Consulting Group garantiza presentaciones directivas con máximo rigor visual y consistencia institucional."
    ]
    takeaway = "Se recomienda formalizar la aprobación de la fase de descubrimiento para asegurar los plazos del calendario operativo."
    add_pattern_content_with_stripe(
        slide_5,
        headline="Decisión Clave para el Éxito del Proyecto",
        paragraphs=concl_paras,
        key_takeaway=takeaway
    )
    validate_layout(slide_5)
    
    # SLIDE 6: Cierre Institucional
    slide_6 = add_cierre_slide(
        prs,
        title="Gracias",
        subtitle="Faro Consulting Group — Guiando Decisiones Estratégicas",
        contact_info={
            "Web": "www.faroconsulting.com",
            "Contacto": "contacto@faroconsulting.com",
            "Oficina": "Santiago, Chile"
        }
    )
    validate_layout(slide_6)
    
    # Guardar archivo con timestamp
    clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")[:30]
    out_filename = dated_filename(f"faro_{clean_title or 'presentacion'}", "pptx")
    out_file_path = out_dir / out_filename
    
    save_with_normal_view(prs, out_file_path)
    
    return {
        "status": "success",
        "title": title,
        "filename": out_filename,
        "filepath": str(out_file_path.resolve()),
        "slides_count": len(prs.slides),
        "aspect_ratio": "16:9 Widescreen",
        "brand": "Faro Consulting Group (FaroCG)"
    }

def main():
    parser = argparse.ArgumentParser(description="FaroCG PPTX Generator Bridge")
    parser.add_argument("--json", type=str, help="Payload JSON en string o ruta de archivo")
    parser.add_argument("--title", type=str, default="Presentación Ejecutiva Faro Consulting Group")
    parser.add_argument("--subtitle", type=str, default="Consultoría de Dirección y Estrategia")
    parser.add_argument("--category", type=str, default="ESTRATEGIA")
    parser.add_argument("--client", type=str, default="Comité Directivo")
    parser.add_argument("--summary", type=str, default="")
    parser.add_argument("--action", type=str, default="generate_deck")
    parser.add_argument("--output-dir", type=str, default="")
    
    args = parser.parse_args()
    
    payload = {}
    if args.json:
        try:
            if os.path.exists(args.json):
                with open(args.json, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            else:
                payload = json.loads(args.json)
        except Exception as e:
            print(json.dumps({"status": "error", "error": f"Error parseando JSON: {str(e)}"}))
            sys.exit(1)
    else:
        payload = {
            "title": args.title,
            "subtitle": args.subtitle,
            "category": args.category,
            "client": args.client,
            "summary": args.summary,
            "action": args.action,
            "output_dir": args.output_dir
        }
        
    try:
        res = generate_presentation(payload)
        # Salida JSON limpia en stdout para AnythingLLM handler.js
        print(json.dumps(res, ensure_ascii=False))
    except Exception as e:
        err_res = {"status": "error", "error": str(e)}
        print(json.dumps(err_res, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
