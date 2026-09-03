# Contexto operativo del MVP local GTX 1650

## Objetivo

El objetivo de esta variante es habilitar un entorno de **pruebas parciales en local** para validar flujo, estabilidad, prompts, chunking, ledger, manejo de errores y calidad mínima de inferencia sin depender del hardware del servidor final. El foco no es throughput alto ni producción, sino confirmar que el pipeline se comporta correctamente en un entorno de desarrollo restringido. [cite:18][cite:34]

## Hardware real del entorno local

| Componente | Valor |
|---|---|
| Sistema operativo | Windows 10 Pro 64-bit |
| CPU | AMD Ryzen 5 3600, 6 núcleos / 12 hilos |
| RAM | 16 GB |
| GPU | NVIDIA GeForce GTX 1650 |
| VRAM dedicada | 3.935 MB, aproximadamente 4 GB |
| Memoria compartida | 8.142 MB |
| Driver model | WDDM 2.7 |

La memoria compartida no debe tratarse como equivalente a VRAM para inferencia LLM. La restricción operativa real para selección de modelos es la **VRAM dedicada de 4 GB**. [cite:34]

## Alcance funcional del MVP

Este MVP local debe cubrir únicamente:

- Pruebas de arranque de Ollama y verificación de aceleración local. [cite:19]
- Validación del flujo `explorador -> conversor -> corrector -> reconstructor -> procesador_lote`. [cite:18]
- Procesamiento de lotes pequeños y documentos cortos. [cite:18]
- Comparación de modelos compactos para español general y tareas técnicas básicas. [cite:34]
- Verificación de ledger, logs, errores aislados y reanudación. [cite:17][cite:18]

Queda fuera del MVP local:

- Producción final masiva.
- Benchmarks representativos de servidor real.
- Modelos 14B o superiores.
- Paralelismo de documentos.
- Contextos extensos y lotes pesados. [cite:16][cite:18][cite:34]

## Reinterpretación del stack

La documentación base del proyecto define `qwen2.5:7b` y `llama3.1:8b` para GPUs de 8–12 GB VRAM y `num_ctx=4096`. Esa parametrización no corresponde al entorno local actual y debe aislarse como perfil de mayor capacidad. [cite:16]

Para el MVP local, el stack se conserva a nivel arquitectónico pero con ajuste de capacidad:

| Capa | Selección MVP local |
|---|---|
| SO | Windows 10 Pro 64-bit |
| Runtime | Python 3.13 + `uv` |
| Motor de inferencia | Ollama local |
| Modelos principales | `qwen2.5:3b`, `llama3.2:3b`, `qwen2.5-coder:3b` |
| Modelos de fallback | `qwen2.5:1.5b`, `qwen2.5-coder:1.5b` |
| Conversión | `MarkItDown` |
| Reconstrucción | `python-docx`, I/O UTF-8 |
| Testing | `pytest`, `pytest-cov`, `respx` |

Qwen2.5 en Ollama se publica en varios tamaños y `qwen2.5:7b` figura como modelo multilingüe de contexto largo, pero ese tamaño resulta excesivo para una GTX 1650 como perfil diario. [cite:35][cite:36]

## Restricciones críticas

1. **Un solo documento a la vez.** El pipeline ya está diseñado de forma secuencial; en esta máquina eso debe mantenerse estrictamente. [cite:18]
2. **Contexto reducido.** El perfil local debe comenzar en `num_ctx=2048`, bajando a `1024` si aparece presión de memoria. [cite:16][cite:34]
3. **Chunks pequeños.** El tamaño de chunk debe reducirse a 1.500–2.200 caracteres para disminuir riesgo de OOM y latencia excesiva. [cite:17][cite:34]
4. **Fallback pequeño.** El fallback debe ser de una familia menor, no un modelo más grande. La lógica del proyecto ya soporta fallback por `Config`, aunque no expone flag CLI dedicado. [cite:18]
5. **Monitoreo obligatorio.** Toda prueba local debe ejecutarse con observación de `nvidia-smi` y/o `ollama ps`. [cite:18]
