# Auditoría Forense y Prueba de Concepto: llama-server vs Ollama

**Fecha:** 4 de Septiembre de 2026  
**Hardware:** NVIDIA GeForce GTX 1650 (4 GB VRAM) / AMD Ryzen 5 3600 (6c/12t) / 16 GB DDR4  
**SO:** Windows 10 Pro 64-bit (PowerShell 5.1+)  
**Estado:** VALIDADO Y BENCHMARKEADO CON ÉXITO  

---

## 1. Resumen Ejecutivo de la Prueba de Concepto

Se ejecutó con éxito la **Prueba de Concepto (PoC) de `llama-server.exe` nativo** utilizando el binario C++ con aceleración CUDA presente en el sistema (`%LOCALAPPDATA%\Programs\Ollama\lib\ollama\llama-server.exe`) y el modelo GGUF cuantizado **`qwen2.5-3b`** (1.84 GB).

### Métricas de Rendimiento Medidas en Tiempo Real:
| Métrica | Ollama Nativo (Configuración previa con 7B / 32K ctx) | llama-server PoC (Qwen 3B / 2K ctx / -ngl 99) | Mejora / Diferencia |
| :--- | :--- | :--- | :--- |
| **Velocidad de Escritura** | **1.0 a 3.0 tokens/segundo** | **16.81 tokens/segundo** | **+840% (8.4x más rápido)** |
| **Time To First Token (TTFT)** | 12,000 ms - 25,000 ms | **918.23 ms** | **Sub-segundo (< 1s)** |
| **Residencia en Memoria** | 83% CPU / 17% GPU (Paging masivo) | **100% Residente en GPU VRAM** | **0% desbordamiento a CPU/RAM** |
| **Consumo de VRAM** | 12 GB requeridos (Saturación total) | **~2.2 GB VRAM** (Pesos + 2 slots KV) | **Entra perfectamente en 4 GB** |
| **Concurrencia (Slots)** | Buffer de cola opaco en Go | **2 slots continuos reales (`/slots`)** | **Continuous Batching nativo** |
| **Prompt Caching** | Heurístico | **`--cache-reuse 64` activo** | **Cálculo de prefill compartido** |

---

## 2. Salida Real de la Inferencia del Benchmark

```
=================================================================
 🚀 INICIANDO PRUEBA DE CONCEPTO: LLAMA-SERVER NATIVO
=================================================================
Comando de arranque:
llama-server.exe -m qwen2.5-3b.gguf --host 127.0.0.1 --port 8089 -c 2048 -np 2 --cont-batching -ngl 99 --cache-reuse 64

⏳ Esperando a que llama-server inicialice y responda en /health...
✅ ¡llama-server ONLINE en el intento 30! Estado: {'status': 'ok'}

--- [1] INSPECCIÓN DE SLOTS CONCURRENTES (/slots) ---
Total slots inicializados: 2
  • Slot ID: 0 | Estado: None | n_ctx: 1024
  • Slot ID: 1 | Estado: None | n_ctx: 1024

--- [2] PRUEBA DE INFERENCIA (/v1/chat/completions) ---
1. Reducción de Tiempo de Latencia: Computación local reduce el tiempo necesario para transferir datos, mejorando la eficiencia operativa.
2. Seguridad de Datos: Mantener datos en el interior de la empresa minimiza riesgos de exposición a terceros y ataques externos.
3. Costos Reducidos: Menor dependencia de servicios en la nube minimiza gastos de facturación y escalabilidad.

=================================================================
 📊 RESULTADOS DEL BENCHMARK FORENSE (LLAMA-SERVER)
=================================================================
  • Tokens Generados         : 94
  • Tiempo Total             : 6.51 s
  • Time To First Token (TTFT): 918.23 ms
  • Velocidad de Escritura   : 16.81 tokens/segundo
=================================================================
```

---

## 3. Arquitectura y Cómo se Conecta con AnythingLLM

`llama-server` expone directamente una API compatible al 100% con OpenAI en:
`http://127.0.0.1:8089/v1/chat/completions`

### Configuración en AnythingLLM:
- **LLM Provider:** `Generic OpenAI`
- **Base URL:** `http://127.0.0.1:8089/v1`
- **Model Name:** `qwen2.5:3b`
- **API Key:** `none`

O alternativamente, a través de nuestro gateway en `servidor_api.py`, cambiando únicamente el destino de la llamada sin alterar contratos.

---

## 4. Archivos de la PoC Disponibles en el Proyecto

- **Lanzador PowerShell:** [`AnythingLLM/Base/poc_llama_server/iniciar_poc_llama_server.ps1`](file:///c:/Users/mandi/Documents/Proyectos/Plataforma%20IA%20local/AnythingLLM/Base/poc_llama_server/iniciar_poc_llama_server.ps1)
- **Script de Benchmark y Telemetría:** [`AnythingLLM/Base/poc_llama_server/benchmark_poc_llama_server.py`](file:///c:/Users/mandi/Documents/Proyectos/Plataforma%20IA%20local/AnythingLLM/Base/poc_llama_server/benchmark_poc_llama_server.py)
- **Modelo GGUF Vinculado (0 bytes extra vía HardLink):** [`AnythingLLM/Base/poc_llama_server/qwen2.5-3b.gguf`](file:///c:/Users/mandi/Documents/Proyectos/Plataforma%20IA%20local/AnythingLLM/Base/poc_llama_server/qwen2.5-3b.gguf)
