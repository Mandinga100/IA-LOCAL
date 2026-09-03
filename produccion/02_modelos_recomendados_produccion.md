# Catálogo de Modelos Homologados para Producción (24 GB VRAM)

**Documento:** `produccion/02_modelos_recomendados_produccion.md`  
**Destino:** Workstation RTX PRO 4000 24 GB GDDR7 ECC  
**Gobernanza:** SDP-U / Arquitectura /ECC  

---

## 1. Estrategia de Selección de Modelos

En la máquina de producción, con 24 GB VRAM y 128 GB RAM DDR5, la selección prioriza máxima fidelidad semántica, capacidad de razonamiento crítico profundo, análisis completo de documentos extensos (más de 50 páginas en una sola pasada) y generación de código de nivel senior.

---

## 2. Catálogo Oficial de Modelos

| Prioridad | Modelo Ollama | Peso VRAM (Q4/Q5) | Contexto Óptimo | Rol Principal |
|---|---|---|---|---|
| **1 (Troncal)** | `qwen2.5:14b` | ~9.2 – 10.5 GB | 32.768 tokens | Motor general de ofimática, síntesis ejecutiva, corrección de Word, PDF, ODT y tablas complejas. |
| **2 (Ingeniería)** | `qwen2.5-coder:32b` | ~19.5 GB | 32.768 tokens | Generación y auditoría de código Python, TypeScript, refactorizaciones y scripts de automatización. |
| **3 (Razonamiento)** | `deepseek-r1:14b` | ~9.5 GB | 32.768 – 65.536 | Auditoría forense crítica, conciliación legal/financiera y razonamiento multi-paso. |
| **4 (Máxima Síntesis)** | `qwen2.5:32b` | ~19.5 GB | 32.768 tokens | Procesamiento masivo de memorias institucionales, licitaciones y libros completos. |
| **5 (Visión VLM)** | `qwen2.5vl:7b` | ~5.5 GB | 16.384 tokens | Extracción semántica y OCR de diagramas, infografías, planos y tablas en imágenes. |
| **6 (Embeddings)** | `bge-m3` | ~1.2 GB (RAM/VRAM) | 8.192 tokens | Indexación vectorial densa para AnythingLLM RAG multi-usuario con soporte multilingüe de alta precisión. |

---

## 3. Configuración de Parámetros por Especialidad

### A. Documentos Extensos e Informes Ejecutivos (Word / PDF)
```text
modelo: qwen2.5:14b
fallback: qwen2.5:7b
num_ctx: 32768
chunk_size: 4500
chunk_overlap: 300
temperatura: 0.15
top_p: 0.9
```

### B. Razonamiento Profundo y Auditoría Forense (DeepSeek R1)
```text
modelo: deepseek-r1:14b
fallback: qwen2.5:14b
num_ctx: 65536
temperatura: 0.6
top_p: 0.95
budget_thinking_tokens: 8192
filtro_zero_chatter: activo (remueve etiquetas <think> en compilación física)
```

### C. Programación y Arquitectura de Software
```text
modelo: qwen2.5-coder:32b
fallback: qwen2.5-coder:14b
num_ctx: 32768
temperatura: 0.1
top_p: 0.9
```

### D. Tablas Financieras y Hojas de Cálculo (Excel / CSV)
```text
modelo: qwen2.5:14b
fallback: qwen2.5:7b
num_ctx: 32768
chunk_size: 5000
temperatura: 0.05
top_p: 0.85
enforce_tables: True
```

---

## 4. Política de Concurrencia y Residencia Caliente

- **Modelo Caliente Anclado:** Para evitar recargas de 10-20 segundos al cambiar de modelo, se recomienda mantener `qwen2.5:14b` anclado con `OLLAMA_KEEP_ALIVE=24h`.
- **Atención Paralela:** Con `OLLAMA_NUM_PARALLEL=4`, cuatro usuarios pueden generar inferencias simultáneas a más de 65 tokens/segundo cada uno sin interferencia.
