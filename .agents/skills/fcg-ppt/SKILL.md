---
name: fcg-ppt
description: "Generador de presentaciones PPTX ejecutivas con formato corporativo e identidad visual de Faro Consulting Group (FaroCG). Incluye plantilla 16:9, paleta oficial, helpers de python-pptx y patrones visuales predefinidos."
tags:
  - pptx
  - presentations
  - faro-consulting
  - corporate-branding
  - python-pptx
---

# Skill: Generador de PPT con formato Faro Consulting Group

## Que hace este skill

Empaqueta la identidad visual de FaroCG y un conjunto de helpers Python para producir presentaciones `.pptx` consistentes con el branding de Faro:

- **Plantilla `.pptx` oficial** con masters y layouts FCG — en `assets/template_fcg.pptx`.
- **Paleta de colores oficial y constantes tipográficas** — en `scripts/fcg_helpers.py`.
- **Helpers reutilizables**:
  - `set_shape_text(shape, text, font_size, font_color, bold, align)`
  - `add_rect(slide, left, top, width, height, fill_color, border_color)`
  - `add_circle(slide, left, top, size, fill_color)`
  - `add_card(slide, left, top, width, height)`
  - `set_notes(slide, notes_text)`
  - `set_title(slide, text, subtitle, category)`
  - `set_portada(slide, title, subtitle, author, date, client)`
  - `add_portada_slide(prs, title, subtitle, author, date, client)`
  - `add_content_slide(prs, title, subtitle, category)`
  - `load_fcg_template(template_path)`
  - `save_with_normal_view(prs, output_path)`
  - `dated_filename(base_name, ext)`
  - `set_language_es_cl(prs)`
  - `validate_layout(slide)`
- **Patrones de slide listos**:
  - Header bar institucional con franja de acento ámbar.
  - Cards de 2 columnas (`add_pattern_two_columns`).
  - Bullet circles numerados para fases metodológicas (`add_pattern_bullet_circles`).
  - Cards de métricas y KPIs (`add_pattern_metric_cards`).
  - Bloque de contenido con franja y takeaway estratégico (`add_pattern_content_with_stripe`).
  - Diapositiva de cierre y agradecimiento (`add_cierre_slide`).

---

## Estructura del Skill

```
fcg-ppt/
├── SKILL.md                 # Documentación e instrucciones operativas
├── assets/
│   └── template_fcg.pptx   # Plantilla base 16:9 Widescreen con masters FaroCG
└── scripts/
    ├── fcg_helpers.py       # Módulo Python con helpers, paleta y patrones
    └── example_deck.py      # Script de demostración con mazo de 6 diapositivas
```

---

## Identidad Visual y Paleta de Colores

| Color | Hex | RGB | Uso Recomendado |
| :--- | :--- | :--- | :--- |
| **Faro Navy** | `#0B2545` | `(11, 37, 69)` | Fondo de portadas, títulos principales, texto institucional |
| **Faro Ocean** | `#133C55` | `(19, 60, 85)` | Encabezados secundarios, contrastes |
| **Faro Royal** | `#1D4ED8` | `(29, 78, 216)` | Elementos de acento primario, tags de categoría |
| **Faro Sky** | `#38BDF8` | `(56, 189, 248)` | Subtítulos luminosos en fondos oscuros, detalles |
| **Faro Amber** | `#D97706` | `(217, 119, 6)` | Destellos, callouts, indicadores de avance y acentos clave |
| **Faro Slate Dark** | `#1E293B` | `(30, 41, 59)` | Texto de cuerpo principal |
| **Faro Muted** | `#64748B` | `(100, 116, 139)` | Subtítulos, descripciones secundarias, pies de página |
| **Faro BG** | `#F8FAFC` | `(248, 250, 252)` | Fondo de diapositivas de contenido |
| **Faro White** | `#FFFFFF` | `(255, 255, 255)` | Tarjetas y contenedores de datos |
| **Faro Border** | `#E2E8F0` | `(226, 232, 240)` | Bordes sutiles de cards |

**Tipografía**: `Calibri` (Predeterminada para máxima portabilidad universal sin dependencias de fuentes instaladas).

---

## Guía Rápida de Uso en Python

```python
from fcg_helpers import (
    load_fcg_template,
    add_portada_slide,
    add_content_slide,
    add_pattern_two_columns,
    add_pattern_metric_cards,
    dated_filename,
    save_with_normal_view
)

# 1. Cargar plantilla 16:9
prs = load_fcg_template()

# 2. Agregar portada
add_portada_slide(
    prs,
    title="Plan Estratégico 2026",
    subtitle="Consultoría de Dirección",
    author="Faro Consulting Group"
)

# 3. Agregar slide con métricas
slide_kpi = add_content_slide(prs, "Métricas Clave", "Resultados del Q3", "DESEMPEÑO")
add_pattern_metric_cards(slide_kpi, [
    {"number": "+32%", "label": "EBITDA", "desc": "Crecimiento interanual"},
    {"number": "99.4%", "label": "Disponibilidad", "desc": "SLA en producción"}
])

# 4. Guardar con vista normal y lenguaje es-CL
out_file = dated_filename("presentacion_estrategica")
save_with_normal_view(prs, out_file)
```

---

## Reglas de Diseño Obligatorias para Agentes

1. **Aspect Ratio**: Siempre 16:9 widescreen (`13.333` x `7.5` pulgadas). Nunca utilizar 4:3.
2. **Jerarquía Visual**:
   - Títulos de diapositiva: 20–24pt en `FCG_NAVY`, negrita.
   - Categoría / Kicker: 9–10pt en `FCG_ROYAL`, mayúsculas.
   - Texto de cuerpo: 11–13pt en `FCG_DARK`.
   - Números de métricas: 32–40pt en negrita con color de acento.
3. **Márgenes Seguros**:
   - Margen izquierdo mínimo: `0.8` pulgadas.
   - Margen derecho máximo: `12.53` pulgadas (`13.333 - 0.8`).
   - Margen superior contenido: `1.8` a `2.0` pulgadas.
   - Margen inferior: `6.8` a `7.0` pulgadas.
4. **Idioma de Corrección**: Aplicar siempre `set_language_es_cl(prs)` para evitar que PowerPoint subraye texto en español con líneas rojas.
5. **Apertura de Archivo**: Utilizar siempre `save_with_normal_view(prs, path)` para garantizar que el archivo se abra con el panel de diapositivas y miniaturas activo.
