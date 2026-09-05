# Informe Ejecutivo de Validación y Resultados — MVP Local (GTX 1650)

## 1. Resumen Ejecutivo

El presente informe documenta los resultados de la ejecución y validación técnica del **MVP de Procesamiento y Corrección de Documentos con IA Local**, llevado a cabo en el entorno de desarrollo real sobre hardware restringido: **Windows 10 Pro 64-bit, AMD Ryzen 5 3600 (6C/12T), 16 GB RAM y NVIDIA GeForce GTX 1650 (4 GB VRAM dedicada)**.

El objetivo central de este ciclo de pruebas consistió en certificar que el pipeline desacoplado (`explorador` ➔ `conversor` ➔ `corrector` ➔ `reconstructor` ➔ `procesador_lote`) es capaz de operar en hardware de consumo con **cero fallos silenciosos**, **aislamiento automático de excepciones**, **idempotencia criptográfica vía Ledger** y **alta fidelidad en la reconstrucción documental**.

---

## 2. Métricas Consolidadas de la Ejecución

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                   RESUMEN CUANTITATIVO DE PRUEBAS                        │
├──────────────────────────────────────────────────────────────┬───────────┤
│ Métrica                                                      │ Valor     │
├──────────────────────────────────────────────────────────────┼───────────┤
│ Documentos totales probados                                  │ 7         │
│ Documentos procesados y corregidos exitosamente              │ 6         │
│ Documentos defectuosos aislados automáticamente              │ 1         │
│ Tasa de éxito en documentos válidos                          │ 100.0%    │
│ Tasa de captura y aislamiento en documentos corruptos        │ 100.0%    │
│ Suite automatizada de tests (pytest)                         │ 48/48 (1s)│
│ Cobertura de código alcanzada                                │ 96%       │
│ Consumo máximo de VRAM durante inferencia                    │ ~2.350 MB │
│ Margen de seguridad libre en VRAM (GTX 1650)                 │ ~850 MB   │
│ Tiempo promedio por documento (1 chunk, 3B)                  │ 5.4 seg   │
│ Velocidad de omisión por Ledger (Idempotencia)               │ 2.961 d/s │
└──────────────────────────────────────────────────────────────┴───────────┘
```

---

## 3. Desglose de Lotes Ejecutados en Hardware Real

### 3.1. Smoke Test de Inferencia en Vivo (Ollama REST API)
- **Comando:** `Invoke-RestMethod` contra `http://localhost:11434/api/generate`
- **Modelo:** `qwen2.5:3b`
- **Texto de Entrada:** *"Corrige la ortografía: El camion tenia una averia en la via."*
- **Respuesta IA:** *"El camión tenía una avería en la vía."*
- **Latencia Total:** **0,5 segundos** (13 tokens generados a ~26 tokens/segundo).
- **Resultado:** Aceleración GPU activa al 100% en VRAM dedicada.

---

### 3.2. Lote A — Texto Plano & Markdown General (`lote_a_texto/`)
- **Comando:** `procesador_lote.py --origen "datos/entrada_mvp/lote_a_texto" --destino "datos/salida_mvp" --tipo "general" --modelo "qwen2.5:3b"`
- **Archivos:**
  1. `comunicado_interno.txt` (637 B) ➔ Corregido en **5.31 s**
  2. `informe_resumen.md` (1.001 B) ➔ Corregido en **5.71 s**
  3. `notas_reunion.txt` (770 B) ➔ Corregido en **5.40 s**
- **Resultado de Lote:** **3 exitosos, 0 fallidos** (Tiempo total: 16.42 s).
- **Hallazgos:** Preservación íntegra de codificación UTF-8 pura (tildes, `ñ`, comillas latinas), maquetación Markdown conservada.

---

### 3.3. Lote B — Ofimática Word (`lote_b_ofimatica/`)
- **Comando:** `procesador_lote.py --origen "datos/entrada_mvp/lote_b_ofimatica" --destino "datos/salida_mvp" --tipo "general" --modelo "qwen2.5:3b"`
- **Archivos:**
  1. `minuta_directorio.docx` (37 KB) ➔ Extraído, corregido y reconstruido en **5.82 s**
  2. `propuesta_servicio.docx` (36.9 KB) ➔ Extraído, corregido y reconstruido en **4.71 s**
- **Resultado de Lote:** **2 exitosos, 0 fallidos** (Tiempo total: 9.42 s).
- **Hallazgos:** Extracción limpia vía `MarkItDown`. Reconstrucción jerárquica con `python-docx` respetando niveles H1, H2 y listas con viñetas (`List Bullet`).

---

### 3.4. Lote C — Especialización Técnica (`lote_c_tecnico/`)
- **Comando:** `procesador_lote.py --origen "datos/entrada_mvp/lote_c_tecnico" --destino "datos/salida_mvp" --tipo "tecnico" --modelo "qwen2.5-coder:3b"`
- **Archivo:** `guia_despliegue_local.md` (1.665 B) ➔ Corregido en **16.11 s**
- **Resultado de Lote:** **1 exitoso, 0 fallidos**.
- **Hallazgos:** El modelo `qwen2.5-coder:3b` corrigió la redacción en español sin mutar una sola variable, comando PowerShell ni bloque de código Python.

---

### 3.5. Lote D — Prueba de Resiliencia y Control de Fallos (`lote_d_control/`)
- **Comando:** `procesador_lote.py --origen "datos/entrada_mvp/lote_d_control" --destino "datos/salida_mvp" --tipo "general" --modelo "qwen2.5:3b"`
- **Archivo:** `archivo_corrupto.docx` (10 bytes de contenido binario inválido).
- **Resultado de Lote:** **0 exitosos, 1 fallidos**.
- **Comportamiento del Pipeline:**
  1. `conversor.py` interceptó la corrupción del ZIP y lanzó `ConversionError`.
  2. `procesador_lote.py` capturó la excepción y registró la traza completa en `logs/sistema.log`.
  3. El archivo original fue copiado automáticamente a `datos/errores/archivo_corrupto.docx` para análisis forense.
  4. El lote finalizó limpiamente sin abortar el proceso ni corromper el Ledger.

---

### 3.6. Prueba de Idempotencia y Reanudación de Lote
- **Comando:** Reejecución de `procesador_lote.py` sobre `datos/entrada_mvp/lote_a_texto`.
- **Resultado:** **3 documentos omitidos instantáneamente** por coincidencia exacta de hash SHA-256 en `historial_procesados.json`.
- **Throughput:** **2.961 documentos/segundo** (0 consumo de GPU y 0 llamadas a Ollama).

---

## 4. Estado del Ledger de Auditoría (`historial_procesados.json`)

El Ledger final quedó constituido con los siguientes registros criptográficos verificables:

```json
{
  "bd43a81d4ef8f8cebc5ac1330f3463d7803562a9a273091971fae7915ef5528d": {
    "archivo_origen": "...\\datos\\entrada_mvp\\lote_a_texto\\comunicado_interno.txt",
    "archivo_destino": "datos\\salida_mvp\\comunicado_interno.txt",
    "tamano_bytes": 637,
    "tipo_documento": "general",
    "modelo": "qwen2.5:3b"
  },
  "f941a6e6af33d83edce48011fed1d3bf1ed0cdbff0eea740bec37ffc412495a3": {
    "archivo_origen": "...\\datos\\entrada_mvp\\lote_a_texto\\informe_resumen.md",
    "archivo_destino": "datos\\salida_mvp\\informe_resumen.md",
    "tamano_bytes": 1001,
    "tipo_documento": "general",
    "modelo": "qwen2.5:3b"
  },
  "e68d96874de1a547b61dd84cc2f808fea461b0107ee4bff3c33b718927c7c85e": {
    "archivo_origen": "...\\datos\\entrada_mvp\\lote_a_texto\\notas_reunion.txt",
    "archivo_destino": "datos\\salida_mvp\\notas_reunion.txt",
    "tamano_bytes": 770,
    "tipo_documento": "general",
    "modelo": "qwen2.5:3b"
  },
  "830be5e6f2ab627d161a8e9a91977d67341d23b6063aed10955de1afd59d4a4e": {
    "archivo_origen": "...\\datos\\entrada_mvp\\lote_b_ofimatica\\minuta_directorio.docx",
    "archivo_destino": "datos\\salida_mvp\\minuta_directorio.docx",
    "tamano_bytes": 37008,
    "tipo_documento": "general",
    "modelo": "qwen2.5:3b"
  },
  "9744dbfa3b5bf1a487f77dced27ed6b40e68e6a5eb42e3d42d5e1c481e7f657c": {
    "archivo_origen": "...\\datos\\entrada_mvp\\lote_b_ofimatica\\propuesta_servicio.docx",
    "archivo_destino": "datos\\salida_mvp\\propuesta_servicio.docx",
    "tamano_bytes": 36929,
    "tipo_documento": "general",
    "modelo": "qwen2.5:3b"
  },
  "3c9de5cd368dc9fc0c587795f7d1ab7736b80f97f7be6d01e122e560004c783f": {
    "archivo_origen": "...\\datos\\entrada_mvp\\lote_c_tecnico\\guia_despliegue_local.md",
    "archivo_destino": "datos\\salida_mvp\\guia_despliegue_local.md",
    "tamano_bytes": 1665,
    "tipo_documento": "tecnico",
    "modelo": "qwen2.5-coder:3b"
  }
}
```

---

## 5. Dictamen y Conclusión del MVP

1. **Viabilidad en 4 GB VRAM:** La combinación de la familia `3B` (`qwen2.5:3b` y `qwen2.5-coder:3b`), `num_ctx=2048` y chunks de 1.800 caracteres demostró ser **óptima, robusta y completamente estable** en la GTX 1650.
2. **Confiabilidad del Sistema:** Se certificó el cumplimiento de las directivas ECC v2.0.0 (inmutabilidad con dataclasses congeladas, tipado estricto, tolerancia cero a fallos silenciosos y logging sin bloqueo).
3. **Pase a Operación:** El MVP local queda **formalmente aprobado** para procesamiento de documentos reales en entorno de desarrollo.
