# Separación entre MVP local y documentación de producción

## Propósito de la separación

La base documental original del proyecto fue redactada para un entorno con 8–12 GB VRAM como mínimo recomendado, con `qwen2.5:7b` y `llama3.1:8b` como línea principal de trabajo. Ese perfil sigue siendo válido como referencia para el servidor real o para una estación más potente, pero no debe confundirse con la configuración del equipo local actual. [cite:16][cite:17][cite:44]

## Regla documental

A partir de ahora deben coexistir dos perfiles claramente diferenciados:

| Perfil | Destino | Hardware esperado | Estado |
|---|---|---|---|
| **MVP local** | Desarrollo y pruebas parciales | GTX 1650 4 GB, 16 GB RAM | Activo en esta carpeta |
| **Producción / servidor real** | Ejecución final y rendimiento objetivo | GPU superior, 8–12 GB VRAM o más | Se mantiene en la documentación original |

## Reglas operativas

- La documentación original **no se elimina** ni se reescribe; se conserva como línea de capacidad media/alta. [cite:44][cite:16]
- La documentación MVP local vive en una carpeta separada y debe citar explícitamente GTX 1650 4 GB como baseline. [cite:34]
- Ningún parámetro de producción debe copiarse automáticamente al perfil local sin recalcular VRAM, contexto y chunks. [cite:16][cite:34]
- La comparación de resultados entre ambos perfiles debe hacerse como trazabilidad técnica, no como sustitución de uno por otro. [cite:18]

## Diferencias clave

| Variable | MVP local GTX 1650 | Producción / GPU potente |
|---|---|---|
| Modelo principal | `qwen2.5:3b` | `qwen2.5:7b` o `llama3.1:8b` |
| Fallback | `qwen2.5:1.5b` | `llama3.1:8b` o equivalente definido en producción |
| `num_ctx` inicial | 2048 | 4096 |
| `chunk_chars` | 1500–2200 | 3000–3500 |
| Concurrencia | 1 | 1, con margen superior en hardware potente |
| Objetivo | Validación parcial | Ejecución productiva |

## Convención sugerida de carpetas

```text
/docs
  /produccion_gpu_media_alta
  /mvp_local_gtx1650
```

Esta convención facilita que el agente y futuros operadores distingan rápidamente entre el perfil de desarrollo restringido y el perfil de despliegue real. [cite:44][cite:34]
