# Reportes de Ejecución y Auditoría del MVP Local (GTX 1650)

Esta carpeta contiene la documentación técnica oficial y las auditorías de rendimiento, calidad y telemetría generadas a partir de las pruebas en hardware real de desarrollo (**Windows 10 Pro 64-bit, AMD Ryzen 5 3600, 16 GB RAM y NVIDIA GeForce GTX 1650 4 GB VRAM**).

---

## 📚 Índice de Reportes de Ejecución

| Reporte | Descripción |
|---|---|
| [01. Informe Ejecutivo de Resultados](01_informe_ejecutivo_mvp.md) | Resumen cuantitativo de lotes, tasas de éxito, tiempos por documento, resumen de Ledger y certificación del MVP. |
| [02. Auditoría Forense de Calidad de Inferencia](02_auditoria_calidad_inferencia.md) | Análisis cualitativo antes/después, preservación de encabezados/viñetas Word y prueba de no-mutación de código técnico. |
| [03. Telemetría de Rendimiento y Límites Operativos](03_telemetria_rendimiento_gtx1650.md) | Datos de consumo de VRAM, temperatura de GPU, tiempos por chunk, comparativa de modelos y recomendaciones operativas. |

---

## 🛡️ Síntesis de Resultados Clave

- **Tasa de éxito en documentos válidos:** **100%** (6 de 6 documentos procesados y corregidos).
- **Tolerancia a fallos:** **100%** (1 de 1 documento corrupto capturado y aislado en `datos/errores/`).
- **Idempotencia:** **2.961 documentos/segundo** mediante Ledger criptográfico SHA-256.
- **Aceleración GPU:** **100% GPU en VRAM** con un pico máximo de ~2.350 MB (margen de ~850 MB libres en la GTX 1650).
