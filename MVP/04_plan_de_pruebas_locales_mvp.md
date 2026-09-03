# Plan de pruebas locales MVP

## Objetivo de validación

Este plan valida que el sistema puede ejecutar pruebas parciales útiles en local con una GTX 1650 sin corromper documentos, sin fallos silenciosos y con un nivel aceptable de estabilidad operativa. La arquitectura ya posee mecanismos de ledger, reintentos, aislamiento de errores y reconstrucción, por lo que el MVP debe concentrarse en verificar que esos mecanismos siguen siendo funcionales bajo hardware restringido. [cite:18]

## Lotes de prueba sugeridos

| Lote | Contenido | Cantidad |
|---|---|---:|
| Lote A | `.txt` y `.md` cortos | 3–5 |
| Lote B | `.docx` de 1–3 páginas | 3–5 |
| Lote C | 1 documento técnico con comandos o código | 1–2 |
| Lote D | 1 archivo problemático o corrupto controlado | 1 |

## Secuencia de prueba

1. **Smoke test Ollama** con `qwen2.5:1.5b`. [cite:19][cite:34]
2. **Prueba general** con `qwen2.5:3b` y lote A. [cite:34]
3. **Prueba documental** con lote B y control de reconstrucción. [cite:18]
4. **Prueba técnica** con `qwen2.5-coder:3b` y lote C. [cite:37][cite:38]
5. **Prueba de error** con lote D para verificar aislamiento en `datos/errores/`. [cite:17][cite:18]
6. **Prueba de reanudación** interrumpiendo manualmente una corrida y verificando ledger. [cite:17][cite:18]

## Métricas mínimas a registrar

| Métrica | Método |
|---|---|
| VRAM máxima | `nvidia-smi -l 1` |
| Uso de GPU | `nvidia-smi -l 1` |
| Tiempo por documento | reloj manual o logs |
| Errores por lote | revisión de logs y `datos/errores/` |
| Reanudación correcta | verificación de `historial_procesados.json` |
| Fidelidad del texto | revisión humana de salida |

## Criterios de aceptación MVP

Se considera aceptable para laboratorio local cuando se cumplen estas condiciones:

- El servicio Ollama responde establemente durante una tanda corta. [cite:19]
- Al menos un modelo principal y uno fallback funcionan en local. [cite:34]
- El pipeline procesa documentos cortos sin bloquear el sistema. [cite:18][cite:34]
- Los errores quedan aislados y no interrumpen por completo el lote. [cite:17][cite:18]
- El ledger permite reanudar sin reprocesar archivos ya completados. [cite:17][cite:18]
- La calidad de corrección es suficiente para pruebas funcionales, aunque no necesariamente final para producción. [cite:18][cite:34]

## Criterios de no aceptación

- OOM recurrente incluso con modelos de 1.5B. [cite:34]
- Uso predominante de CPU con degradación extrema. [cite:34]
- Salidas truncadas o vacías de forma frecuente. [cite:18]
- Reconstrucción defectuosa en formatos base. [cite:18]
- Imposibilidad de sostener lotes pequeños de prueba. [cite:34]
