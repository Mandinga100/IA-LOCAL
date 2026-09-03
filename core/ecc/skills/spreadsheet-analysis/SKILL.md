---
name: spreadsheet-analysis
description: "Análisis determinista de hojas de cálculo (Excel, CSV, XLSX) con validación de fórmulas, balance contable y formateo Markdown tabular para AnythingLLM"
---

# Spreadsheet Analysis Skill

## 1. Principios Operativos
1. **Determinismo Numérico:** Nunca alucinar cálculos ni totales. Las fórmulas aritméticas deben resolverse de forma exacta o delegar a funciones Python/Pandas.
2. **Formato Tabular Estricto:** Toda salida debe estructurarse en tablas Markdown alineadas (`| Columna 1 | Columna 2 |`) o sintaxis CSV estándar.
3. **Validación de Mojibakes y Separadores:** Detectar automáticamente si el separador es coma (`,`), punto y coma (`;`) o tabulador (`\t`). Manejar encoding CP1252 y UTF-8.
4. **Resumen Financiero y KPIs:** Extraer métricas clave (Total, Media, Desviación, Mínimo, Máximo, Balance general).

## 2. Flujo de Trabajo
- Ingestión va `conversor.py` (`.xlsx`, `.xls`, `.csv`).
- Conversión a tabla Markdown estructurada.
- Corrección de anomalías tipográficas y validación de tipos de datos.
- Reconstrucción opcional a `.xlsx` o `.csv` descargable va `exportar_documento_formato()`.
