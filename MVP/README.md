# Documentación separada: MVP local de pruebas parciales

Esta carpeta contiene una línea documental **exclusiva para pruebas locales parciales** sobre el hardware real actual del entorno de desarrollo: **Windows 10 Pro 64-bit, AMD Ryzen 5 3600, 16 GB RAM y NVIDIA GeForce GTX 1650 con 4 GB de VRAM dedicada**. Esta separación evita contaminar la documentación orientada a una GPU más potente y a la operación de producción final. [cite:34][cite:16][cite:18]

La documentación original del proyecto permanece orientada al escenario previsto de 8–12 GB VRAM y pruebas/operación cercanas a producción, con `qwen2.5:7b` o `llama3.1:8b` como base recomendada. Este nuevo bloque documental redefine alcance, modelos, parámetros, procedimientos y criterios de validación específicamente para un **MVP de laboratorio local**. [cite:16][cite:17][cite:18]

## Índice

| Documento | Propósito |
|---|---|
| [01_contexto_mvp_local_gtx1650.md](01_contexto_mvp_local_gtx1650.md) | Define objetivos, restricciones, alcance y stack adaptado al hardware actual. |
| [02_guia_operativa_mvp_local_gtx1650.md](02_guia_operativa_mvp_local_gtx1650.md) | Contiene instalación, arranque, pruebas operativas y monitoreo con Ollama. |
| [03_modelos_recomendados_mvp_local_gtx1650.md](03_modelos_recomendados_mvp_local_gtx1650.md) | Documenta modelos recomendados, exclusiones, parámetros y fallback para la GTX 1650. |
| [04_plan_de_pruebas_locales_mvp.md](04_plan_de_pruebas_locales_mvp.md) | Establece smoke tests, pruebas funcionales parciales, métricas y criterios de aceptación. |
| [05_separacion_con_produccion.md](05_separacion_con_produccion.md) | Define la convivencia entre documentación local MVP y la documentación de servidor/producción. |
| [06_planificacion_ejecucion_mvp.md](06_planificacion_ejecucion_mvp.md) | Planificación y hoja de ruta técnica paso a paso para ejecutar la IA local con datos reales. |

## Principio de separación

- **No reemplaza** la documentación existente. [cite:44]
- **No modifica** la línea operativa pensada para GPU de mayor VRAM y producción. [cite:16][cite:17]
- **Sí agrega** una ruta alternativa y explícita para pruebas locales con restricciones reales de 4 GB VRAM. [cite:34]
