# Contexto y Arquitectura de Hardware de Producción: RTX PRO 4000 24 GB + i9-14900

**Documento:** `produccion/01_contexto_produccion_rtx_pro4000_24gb.md`  
**Estado:** PRODUCCIÓN OBJETIVO / WORKSTATION  
**Gobernanza:** SDP-U / Arquitectura /ECC  

---

## 1. Especificaciones Técnicas del Host de Producción

| Componente | Especificación Técnica | Ventaja Operativa |
|---|---|---|
| **GPU Primaria** | **PNY NVIDIA Quadro RTX PRO 4000 24 GB GDDR7 ECC** (VCNRTXPRO4000B-PB) | Arquitectura Blackwell, 8.960 núcleos CUDA, Tensor Cores 5.ª Gen (FP4/FP8 nativo), 140W TDP, Memoria ECC contra corrupción de bits en inferencia continua. |
| **VRAM Total** | **24.576 MiB GDDR7** | Capacidad para albergar modelos de 32B (Q4_K_M ~19.5 GB) anclados en caliente con margen para KV-Cache masivo. |
| **CPU** | **Intel Core i9-14900** | 24 núcleos (8 P-Cores + 16 E-Cores), 32 hilos lógicos, hasta 5.8 GHz, 36 MB Intel Smart Cache. Paralelización masiva de preprocesamiento y extracción. |
| **RAM del Sistema** | **128 GB DDR5** | Ingestión masiva de documentos en RAM, offload sin penalización y buffer de concurrencia ultra-amplio. |
| **Almacenamiento** | SSD NVMe PCIe 4.0/5.0 | Carga instantánea de pesos de modelos (>6.000 MB/s de lectura secuencial). |
| **Sistema Operativo** | Windows 10/11 Pro 64-bit / Windows Server | PowerShell Core 7+, Docker Desktop WSL2 con GPU Passthrough (NVIDIA Container Toolkit). |

---

## 2. Presupuesto Matemático de VRAM para 10+ Usuarios Concurrentes

A diferencia del MVP local (restringido a 4 GB VRAM en la GTX 1650), la estación de producción cuenta con un **techo de 24 GB VRAM**:

$$\text{VRAM Total} = \text{Pesos del Modelo} + (N_{\text{slots}} \times \text{KV-Cache}) + \text{Overhead CUDA}$$

### Caso A: Modelo Troncal de Alta Calidad (Qwen 2.5 14B Q5_K_M / Q8_0)
- **Pesos del modelo (14B Q5_K_M):** ~10.5 GB.
- **Ventana de contexto:** `num_ctx = 32.768` tokens con FlashAttention y KV-cache `q8_0`.
- **KV-Cache por slot (32K ctx):** ~1.2 GB.
- **Concurrencia con `OLLAMA_NUM_PARALLEL=4`:** $4 \times 1.2\text{ GB} = 4.8\text{ GB}$.
- **Overhead CUDA / Driver:** ~800 MB.
- **Consumo Total:** $10.5\text{ GB} + 4.8\text{ GB} + 0.8\text{ GB} = \mathbf{16.1\text{ GB}} < 24.0\text{ GB}$.
- **Margen Libre:** **~8.4 GB libres** en VRAM para picos de contexto o carga simultánea de modelo de visión (`qwen2.5vl:7b`).

### Caso B: Modelo Ancla de Máxima Capacidad (Qwen 2.5 32B / Qwen 2.5 Coder 32B Q4_K_M)
- **Pesos del modelo (32B Q4_K_M):** ~19.5 GB.
- **Ventana de contexto:** `num_ctx = 16.384` tokens.
- **KV-Cache por slot (16K ctx con FlashAttention):** ~950 MB.
- **Concurrencia con `OLLAMA_NUM_PARALLEL=2`:** ~1.9 GB.
- **Overhead CUDA:** ~800 MB.
- **Consumo Total:** $19.5\text{ GB} + 1.9\text{ GB} + 0.8\text{ GB} = \mathbf{22.2\text{ GB}} < 24.0\text{ GB}$.
- **Resultado:** 100% de residencia en VRAM sin degradación a CPU ni paginación a RAM.

---

## 3. Matriz Comparativa: MVP vs Producción

| Parámetro | Perfil MVP (Desarrollo Local) | Perfil Producción (Workstation) |
|---|---|---|
| **GPU** | NVIDIA GeForce GTX 1650 | PNY Quadro RTX PRO 4000 Blackwell |
| **VRAM** | 4 GB GDDR5 | 24 GB GDDR7 ECC |
| **CPU / RAM** | Ryzen 5 3600 (6C/12T) / 16 GB DDR4 | Core i9-14900 (24C/32T) / 128 GB DDR5 |
| **Modelo Ofimática** | `qwen2.5:3b` | `qwen2.5:14b` o `qwen2.5:32b` |
| **Modelo Código** | `qwen2.5-coder:3b` | `qwen2.5-coder:32b` |
| **Modelo Razonamiento** | `qwen2.5:3b` (Zero-Chatter) | `deepseek-r1:14b` o `deepseek-r1:32b` |
| **Modelo VLM / Visión** | `qwen2.5vl:3b` | `qwen2.5vl:7b` / `qwen2.5vl:32b` |
| **Embeddings RAG** | `nomic-embed-text` (~270 MB) | `bge-m3` o `nomic-embed-text` |
| **Contexto (`num_ctx`)** | 2.048 tokens | 32.768 a 65.536 tokens |
| **Tamaño de Chunk** | 1.800 – 2.200 caracteres | 3.500 – 6.000 caracteres |
| **Slots Concurrencia** | 2 slots (`OLLAMA_NUM_PARALLEL=2`) | 4 a 6 slots (`OLLAMA_NUM_PARALLEL=4`) |
| **Throughput Estimado** | ~35 tokens/seg (3B) | ~80 tokens/seg (14B) / ~40 tokens/seg (32B) |
