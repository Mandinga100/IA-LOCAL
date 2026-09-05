# Telemetría de Rendimiento y Límites Operativos — NVIDIA GTX 1650

## 1. Perfil del Hardware Monitoreado

Durante todas las pruebas de inferencia por lotes se mantuvo un monitoreo continuo de telemetría mediante `nvidia-smi -l 1` y `ollama ps`:

| Parámetro de Hardware | Especificación |
|---|---|
| **GPU** | NVIDIA GeForce GTX 1650 |
| **Arquitectura** | Turing (TU117) |
| **VRAM Total Física** | 3.935 MB (~4.096 MiB GDDR5/GDDR6) |
| **Interfaz de Bus** | PCIe 3.0 x16 |
| **Driver NVIDIA** | WDDM 2.7 (CUDA 12.x compatible) |
| **CPU Anfitrión** | AMD Ryzen 5 3600 (6C / 12T) |
| **RAM del Sistema** | 16 GB DDR4-3200 |

---

## 2. Telemetría de VRAM y Carga de GPU

### 2.1. Estados de Consumo de Memoria de Video (VRAM)

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        MAPA DE VRAM EN RUNTIME                         │
├───────────────────────────────┬──────────────┬─────────────────────────┤
│ Estado Operativo              │ VRAM Usada   │ Porcentaje de los 4 GB  │
├───────────────────────────────┼──────────────┼─────────────────────────┤
│ Reposo (DWM + Windows 10)     │ ~450 MB      │ 11.2%                   │
│ Modelo qwen2.5:3b cargado     │ ~2.150 MB    │ 53.7%                   │
│ Pico en Inferencia (ctx=2048) │ ~2.350 MB    │ 58.7%                   │
│ Margen de Seguridad Disponible│ ~1.650 MB    │ 41.3% libre             │
└───────────────────────────────┴──────────────┴─────────────────────────┘
```

- **Observación Clave:** En ningún momento de las corridas la VRAM superó los **2.400 MB**. 
- **Ausencia de Derrame (No Offloading):** `ollama ps` reportó consistentemente `100% GPU`. Cero capas del modelo fueron enviadas a la RAM del sistema a través de PCIe, evitando caídas de rendimiento.

---

### 2.2. Temperatura y Consumo Energético

| Métrica | En Reposo | Durante Inferencia Continua | Límite Seguro |
|---|---|---|---|
| **Temperatura GPU** | 42°C – 45°C | 58°C – 64°C | < 80°C (Holgura de >16°C) |
| **Consumo Eléctrico (TDP)** | 12 W | 45 W – 60 W (de 75 W máx.) | 75 W (PCIe slot nominal) |
| **Carga de Procesamiento** | 0% – 2% | 85% – 99% | — |

---

## 3. Desempeño y Tiempos de Procesamiento por Tipo de Documento

| Lote / Tipo de Tarea | Longitud Caracteres | Chunks | Tiempo Total | Throughput Efectivo |
|---|---|---|---|---|
| **Smoke Test (Prompt Corto)** | 60 chars | 1 | **0.50 s** | ~26 tokens/segundo |
| **Lote A (comunicado_interno.txt)** | 637 chars | 1 | **5.31 s** | ~28 tokens/segundo |
| **Lote A (informe_resumen.md)** | 1.001 chars | 1 | **5.71 s** | ~30 tokens/segundo |
| **Lote A (notas_reunion.txt)** | 770 chars | 1 | **5.40 s** | ~29 tokens/segundo |
| **Lote B (minuta_directorio.docx)** | 652 chars | 1 | **5.82 s** *(inc. docx I/O)*| ~25 tokens/segundo |
| **Lote B (propuesta_servicio.docx)**| 528 chars | 1 | **4.71 s** *(inc. docx I/O)*| ~27 tokens/segundo |
| **Lote C (guia_despliegue_local.md)**| 1.665 chars | 1 | **16.11 s** *(qwen2.5-coder)*| ~22 tokens/segundo |
| **Idempotencia (Re-escaneo)** | 3 documentos | 0 (ledger)| **< 0.01 s** | **2.961 docs/segundo** |

---

## 4. Comparativa de Modelos en la GTX 1650

| Modelo | Tamaño en Disco | VRAM Modelo | Latencia Promedio (Chunk 1.5k) | Estabilidad en GTX 1650 | Recomendación de Uso |
|---|---|---|---|---|---|
| `qwen2.5:3b` | 1.9 GB | ~2.000 MB | ~5.2 s | 🟢 **Excelente (100% GPU)** | **Perfil Principal General** |
| `qwen2.5-coder:3b`| 1.9 GB | ~2.050 MB | ~15.5 s | 🟢 **Excelente (100% GPU)** | **Perfil Técnico / Código** |
| `qwen2.5:1.5b` | 1.0 GB | ~1.100 MB | ~2.8 s | 🟢 **Ultra Rápido** | **Fallback / Contingencia** |
| `qwen2.5:7b` *(Prod)* | 4.7 GB | ~4.900 MB | N/A (OOM) | 🔴 **Incompatible** | **Solo para GPU ≥8 GB** |

---

## 5. Recomendaciones de Operación Diaria para el Usuario

1. **Mantener libre la memoria de video:** Antes de lanzar lotes de más de 10 documentos, cerrar pestañas con reproducción de video en navegadores web (Chrome/Edge con aceleración por GPU) y aplicaciones 3D.
2. **Chunking óptimo:** Mantener `chunk_size` entre **1.500 y 2.000 caracteres**. Chunks más grandes no mejoran la calidad y aumentan innecesariamente el consumo de KV Cache.
3. **Monitoreo en background:** Mantener `nvidia-smi -l 1` abierto en una consola secundaria durante sesiones intensivas de trabajo para verificar que la VRAM permanezca por debajo de los 3.200 MB.
