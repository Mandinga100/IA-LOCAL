# Modelos recomendados para MVP local GTX 1650

## Criterio de selección

La GPU local dispone de aproximadamente 4 GB de VRAM dedicada, por lo que la selección debe priorizar modelos compactos, contexto corto y operación estable. La meta del MVP no es la máxima calidad absoluta, sino la mejor combinación entre estabilidad, consumo y utilidad real para pruebas parciales. [cite:34]

## Modelos recomendados

| Prioridad | Modelo | Rol | Estado recomendado |
|---|---|---|---|
| 1 | `qwen2.5:3b` | General en español | Principal |
| 2 | `qwen2.5:1.5b` | Fallback general | Obligatorio |
| 3 | `qwen2.5-coder:3b` | Técnico / código | Principal técnico |
| 4 | `qwen2.5-coder:1.5b` | Fallback técnico | Obligatorio |
| 5 | `llama3.2:3b` | Comparativa secundaria | Opcional |
| 6 | `qwen2.5:0.5b` | Smoke tests y validaciones mínimas | Opcional |

Qwen2.5 es una familia multilingüe publicada en Ollama, mientras que `qwen2.5-coder` se ofrece específicamente para generación, reparación y razonamiento de código en varios tamaños, incluido 3B. [cite:35][cite:37][cite:38]

## Modelos no recomendados como perfil diario local

| Modelo | Motivo |
|---|---|
| `qwen2.5:7b` | Demasiado cerca o por encima del margen práctico de VRAM para operación cómoda diaria. [cite:36][cite:34] |
| `llama3.1:8b` | Presión de memoria superior a la GTX 1650 y mayor latencia. [cite:16][cite:34] |
| `qwen2.5:14b` | Perfil ajeno al hardware local actual. [cite:16] |
| Modelos multimodales 7B+ | Exceso de peso para pruebas MVP en 4 GB VRAM. [cite:34] |

## Perfiles recomendados por uso

### Corrección general de documentos

```text
modelo: qwen2.5:3b
fallback: qwen2.5:1.5b
num_ctx: 2048
chunk_chars: 1800
```

### Documentos técnicos y contenido con comandos

```text
modelo: qwen2.5-coder:3b
fallback: qwen2.5-coder:1.5b
num_ctx: 2048
chunk_chars: 2000
```

### Prueba mínima de infraestructura

```text
modelo: qwen2.5:0.5b o qwen2.5:1.5b
num_ctx: 1024
chunk_chars: 1200-1500
```

## Estrategia de adopción

1. Empezar todas las pruebas con `qwen2.5:3b`. [cite:34]
2. Si aparece inestabilidad, pasar directamente a `qwen2.5:1.5b`. [cite:34]
3. Reservar `qwen2.5-coder:3b` para casos donde el tipo `tecnico` de verdad necesite preservar código, variables o comandos. [cite:18][cite:37]
4. Usar `llama3.2:3b` únicamente como comparación de calidad, no como default operativo. [cite:34]
5. Evitar que el MVP local use el mismo baseline documental del servidor final, ya que ese baseline estaba diseñado para 8–12 GB VRAM. [cite:16]
