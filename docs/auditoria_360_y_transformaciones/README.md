# Auditoría Forense 360° y Matriz de Transformación Universal de Formatos

Esta carpeta alberga la investigación arquitectónica, auditorías forenses de rendimiento y seguridad, y las especificaciones técnicas para llevar la **Plataforma de IA Local** hacia la compatibilidad universal de formatos ofimáticos y optimización multidimensional.

---

## 📚 Índice de la Sección

| Documento | Enfoque Principal |
|---|---|
| [01. Auditoría Forense y Plan de Optimización 360°](01_auditoria_forense_optimizaciones_360.md) | Análisis en 5 dimensiones: Rendimiento VRAM, Ciberseguridad/Zip-bombs, Arquitectura desacoplada, Calidad de IA/Tablas y Experiencia CLI/Dashboard. |
| [02. Matriz de Compatibilidad y Transformaciones](02_matriz_compatibilidad_y_transformaciones.md) | Especificación técnica para 14 extensiones (`.doc`, `.docx`, `.odt`, `.rtf`, `.txt`, `.md`, `.pdf`, `.ppt`, `.pptx`, `.xls`, `.xlsx`, `.csv`, `.epub`, `.html`), patrón Registry y dependencias recomendadas. |
| [03. Auditoría Forense Integral de Código y Flujos](03_auditoria_forense_integral_codigo_y_flujos.md) | Auditoría 360° de base de código: anti-mojibakes multicapa, chunking jerárquico, ciclo de vida de sockets y verificación de 60 tests. |

---

## 🎯 Síntesis Estratégica

1. **Pivote Central en Markdown:** Todo formato de entrada se normaliza a Markdown UTF-8 antes de la inferencia, garantizando consistencia absoluta en las correcciones ortográficas y de estilo.
2. **Seguridad en Fronteras:** Incorporación de *Magic Bytes Sniffer* y *Zip-Bomb Guards* para blindar el pipeline contra archivos binarios maliciosos o corruptos.
3. **Arquitectura por Plugins (`DocumentFormatRegistry`):** Transición hacia un diseño desacoplado que permita incorporar nuevos formatos sin modificar el código del núcleo.
