# Guía operativa MVP local GTX 1650

## Preparación del entorno

La preparación base sigue el enfoque ya documentado para Windows 10, PowerShell, `uv` y Python 3.13, incluyendo forzado de UTF-8 al inicio de sesión. [cite:17]

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
```

```powershell
uv venv .venv --python 3.13
uv pip install --python .venv -r requirements.txt
uv pip install --python .venv "markitdown[all]"
```

## Modelos a instalar para MVP local

```powershell
ollama pull qwen2.5:3b
ollama pull qwen2.5:1.5b
ollama pull llama3.2:3b
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:1.5b
```

Ollama soporta aceleración GPU NVIDIA y en Windows requiere soporte CUDA en GPUs compatibles; la GTX 1650 entra dentro del rango utilizable para pruebas locales, aunque con fuerte limitación de VRAM. [cite:19][cite:34]

## Arranque operativo

```powershell
ollama serve
```

Verificaciones rápidas:

```powershell
Invoke-RestMethod -Uri "http://localhost:11434/api/version" -Method Get
Invoke-RestMethod -Uri "http://localhost:11434/api/tags"
ollama list
ollama ps
```

## Monitoreo obligatorio durante pruebas

En una segunda consola:

```powershell
nvidia-smi -l 1
```

Objetivos de observación:

- Confirmar que sube el uso de VRAM al ejecutar el modelo. [cite:34]
- Confirmar que la GPU entra en carga real y no queda toda la inferencia en CPU. [cite:34]
- Detectar rápidamente picos de memoria, thermal throttling o procesos competidores. [cite:34]

## Perfil de ejecución recomendado

### Perfil general

```text
modelo principal: qwen2.5:3b
modelo fallback: qwen2.5:1.5b
num_ctx: 2048
chunk_chars: 1800
concurrencia: 1
```

### Perfil técnico / código

```text
modelo principal: qwen2.5-coder:3b
modelo fallback: qwen2.5-coder:1.5b
num_ctx: 2048
chunk_chars: 2000
concurrencia: 1
```

### Perfil de contingencia

```text
modelo principal: qwen2.5:1.5b
num_ctx: 1024
chunk_chars: 1500
concurrencia: 1
```

## Ejecución del pipeline

La CLI actual soporta `--origen`, `--destino`, `--tipo`, `--modelo` y `--url`, pero no ofrece todavía un `--fallback` nativo. El fallback debe configurarse a nivel de `Config` en código Python. [cite:17][cite:18]

Ejemplo de prueba general:

```powershell
.\.venv\Scripts\python.exe procesador_lote.py `
  --origen "datos/prueba" `
  --destino "datos/salida_mvp_local" `
  --tipo "general" `
  --modelo "qwen2.5:3b" `
  --url "http://localhost:11434"
```

Ejemplo técnico:

```powershell
.\.venv\Scripts\python.exe procesador_lote.py `
  --origen "datos/prueba_tecnica" `
  --destino "datos/salida_mvp_codigo" `
  --tipo "tecnico" `
  --modelo "qwen2.5-coder:3b" `
  --url "http://localhost:11434"
```

## Política operativa local

- Cerrar navegador con muchas pestañas, Discord, OBS, juegos y procesos 3D antes de probar.
- No ejecutar más de una corrida pesada a la vez.
- Usar directorios de entrada pequeños, idealmente 3–10 documentos por tanda.
- Reiniciar Ollama entre comparativas si se observa memoria retenida.
- Conservar logs y ledger para análisis de estabilidad. [cite:17][cite:18][cite:34]

## Troubleshooting adaptado

| Problema | Causa probable | Acción recomendada |
|---|---|---|
| `InferenciaError` o timeout | Modelo demasiado pesado o contexto alto | Bajar a `qwen2.5:1.5b`, reducir `num_ctx` a 1024 y chunk a 1500. |
| OOM / VRAM al límite | 4 GB dedicados insuficientes | Cerrar apps con GPU, reiniciar Ollama, usar modelo 1.5B. |
| Muy lento | Descarga parcial a CPU/RAM | Probar modelo más pequeño y lote más corto. |
| Resultado inconsistente | Prompt o chunk excesivo | Reducir tamaño de chunk y evaluar documentos más homogéneos. |
| Aceleración dudosa | GPU no está tomando carga | Confirmar con `nvidia-smi` y `ollama ps`. |

La guía operativa base ya contempla que, ante OOM, se reduzca chunk o se pase a un modelo más ligero cuantizado. En este perfil local, esa recomendación deja de ser contingencia y pasa a ser política por defecto. [cite:17]
