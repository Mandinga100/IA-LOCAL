# Guía de Testeo Visual y Auditoría Multi-Documento en Paralelo

> **Plataforma:** Windows 10 64-bit, AnythingLLM Core (:3001), Gateway Base & Dashboard 360 (:8000), Ollama (:11434)  
> **Hardware Auditado:** AMD Ryzen 5 3600 (6C/12T), 16 GB RAM DDR4, NVIDIA GeForce GTX 1650 (4 GB VRAM)  
> **Estado:** 100% Operativo y Validado en Tiempo Real.

---

## 1. Objetivo y Alcance

Este documento describe el protocolo de pruebas visuales de comparación en paralelo de dos o más documentos (en formatos `.md` y `.pdf`) dentro de la plataforma local, asegurando la preservación de contexto, evitando el truncamiento silencioso de Ollama y monitoreando el consumo de VRAM en la GPU GTX 1650.

---

## 2. Inventario de Archivos de Prueba Generados

Se han creado pares de contratos con diferencias deliberadas y críticas en montos, plazos, SLA, penalizaciones y jurisdicción:

```text
c:\Users\mandi\Documents\Proyectos\Plataforma IA local\AnythingLLM\Base\datos\entrada_web\
├── Contrato_Servicios_v1.md   (Markdown original)
├── Contrato_Servicios_v2.md   (Markdown modificado)
├── Contrato_Servicios_v1.pdf   (PDF maquetado profesionalmente, 3.67 KB)
└── Contrato_Servicios_v2.pdf   (PDF maquetado profesionalmente, 3.72 KB)
```

### Tabla de Diferencias Semánticas Inyectadas para el Test

| Cláusula / Elemento | Versión 1.0 (Original) | Versión 2.0 (Revisada) | Impacto / Riesgo |
| :--- | :--- | :--- | :--- |
| **Fecha de Emisión** | 1 de Octubre de 2026 | 15 de Octubre de 2026 | Desfase temporal de 14 días |
| **Cláusula 1 (Objeto)** | Servidores dedicados para docs | Plataforma Híbrida + Visión | Ampliación de alcance |
| **Cláusula 2 (Plazo)** | **30 días corridos** | **45 días corridos** | +15 días de retraso en entrega |
| **Cláusula 3 (Precio)** | **USD 5,000** (2 cuotas 50/50) | **USD 6,500** (3 cuotas 40/30/30) | +USD 1,500 de sobrecosto |
| **Cláusula 4 (SLA)** | **24/7** (Respuesta < 2 hrs) | **8/5** oficina (Respuesta < 6 hrs) | **Degradación crítica de soporte** |
| **Cláusula 5 (Multa)** | **1% diario** (Tope 15%) | **3% diario** (Tope 30%) | Incremento del 200% en riesgo |
| **Cláusula 6 (Leyes)** | Santiago de Chile | Valparaíso, Chile | Cambio de tribunal competente |

---

## 3. Matriz de Modelos Locales para la GTX 1650 (4 GB VRAM)

| Modelo | Modalidad de Carga | Velocidad | Contexto Seguro (`num_ctx`) | Fortalezas en Comparativas |
| :--- | :--- | :--- | :--- | :--- |
| **`deepseek-r1:1.5b`** | 100% VRAM (GPU Pura) | **50 - 60 t/s** | 32,768 - 65,536 tokens | **Razonamiento deductivo paso a paso (`<think>`)**. Excelente para desglosar por qué una cláusula perjudica al cliente. |
| **`qwen2.5:3b`** | 100% VRAM (GPU Pura) | **35 - 45 t/s** | 16,384 - 32,768 tokens | El estándar de velocidad y precisión sintáctica en español. |
| **`qwen2.5:7b`** | Híbrido GPU + RAM DDR4 | **9 - 14 t/s** | 16,384 - 32,768 tokens | Máxima agudeza analítica para textos legales extensos. |

> [!CAUTION]
> **Configuración de Contexto Obligatoria:**  
> Por defecto, Ollama utiliza `num_ctx: 2048`. Al comparar dos documentos completos, debes configurar en el Workspace de AnythingLLM (**Workspace Settings -> Chat Settings -> Context Window**) el valor **`16384`** o **`32768`** para evitar el truncamiento inadvertido.

---

## 4. Métodos de Testeo Visual en la Plataforma

### Método A: Visor Diff "Side-by-Side" en Dashboard 360 ([http://localhost:8000](http://localhost:8000))
Diseñado para la inspección visual paralela inmediata con telemetría de hardware en tiempo real:

1. Acceder a [http://localhost:8000](http://localhost:8000).
2. En la columna izquierda, arrastrar `Contrato_Servicios_v1.pdf`.
3. Seleccionar el perfil **Técnico / Jurídico** y el modelo (`qwen2.5:3b` o `deepseek-r1:1.5b`).
4. Hacer clic en **`✨ Iniciar Procesamiento IA`**.
5. Cambiar a la pestaña **`🔍 Comparativa`**:
   * Panel Izquierdo: *Original Extraído*.
   * Panel Derecho: *Resultado Procesado / Auditado*.
   * Panel Lateral Derecho: Gráfico en vivo de VRAM utilizada en la GTX 1650 y temperatura.

### Método B: Ingesta Dual y Agente en AnythingLLM ([http://localhost:3001](http://localhost:3001))
Diseñado para comparativas de múltiples archivos no idénticos mediante lenguaje natural:

1. Acceder a [http://localhost:3001](http://localhost:3001).
2. Crear un Workspace (ej: `Auditoria-Comparativa`).
3. En el gestor de documentos, subir:
   * `Contrato_Servicios_v1.pdf`
   * `Contrato_Servicios_v2.pdf`
4. Fijar ambos con el botón **"Move to Workspace"** (chincheta) y guardar cambios.
5. Ejecutar en el chat el siguiente prompt:

```text
@agent Realiza un cotejo forense exhaustivo entre Contrato_Servicios_v1.pdf y Contrato_Servicios_v2.pdf.
Genera:
1. Tabla comparativa Markdown: [Cláusula | v1.0 Original | v2.0 Revisada | Diferencia Clave | Nivel de Riesgo (Bajo/Medio/Alto)].
2. Dictamen ejecutivo sobre cuál versión es más perjudicial financieramente y por qué.
```

---

## 5. Integración con `forensic-audit-skill`

La skill de peritaje personalizada desplegada en `server/storage/plugins/agent-skills/forensic-audit-skill/` permite auditar la integridad criptográfica de ambos PDFs antes de analizarlos:

```text
Prompt de Integridad en Chat:
@agent ejecuta una auditoría forense con acción 'hash' sobre el recurso 'Contrato_Servicios_v1.pdf'
```
* **Comportamiento en UI:** El agente desplegará la tarjeta interactiva de seguridad (**Approve / Reject** con contador de 120 segundos) antes de calcular el fingerprint criptográfico.
