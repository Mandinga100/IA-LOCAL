# Dashboard Visual Frontend 360° y Telemetría de Hardware en Tiempo Real

**Documento:** `docs/dashboard_frontend_360_y_telemetria.md`  
**Estado:** PRODUCCIÓN / OPERATIVO  
**Gobernanza:** SDP-U / Arquitectura /ECC  
**Entorno Operativo:** Windows 10 / 11 Pro 64-bit y GNU/Linux | FastAPI | Vanilla HTML5/CSS3/JS  

---

## 1. Resumen Ejecutivo

El **Dashboard Visual Frontend 360°** es la consola web unificada de operación, monitoreo y auditoría de la **Plataforma IA Local**. Provee una interfaz gráfica de alto rendimiento, 100% autónoma y sin dependencias externas (desarrollada en Vanilla HTML5 semántico, CSS moderno con estética oscura profesional y JavaScript nativo), permitiendo al operador y a los usuarios:
1. Procesar documentos de forma interactiva con selección de estilos y perfiles.
2. Monitorear el consumo de hardware en tiempo real (VRAM, GPU %, temperatura, RAM y CPU) para prevenir desbordamientos de memoria (*OOM*).
3. Inspeccionar y comparar documentos antes y después de la inferencia.
4. Auditar el cumplimiento del protocolo **Zero-Chatter** (Pureza Documental).
5. Diagnosticar el estado de los servicios locales (Ollama, API Gateway y AnythingLLM).

---

## 2. Arquitectura de las 5 Pestañas Modulares

El panel de control se organiza en cinco módulos especializados accesibles mediante navegación por pestañas:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            PLATAFORMA IA LOCAL - DASHBOARD 360°                                  │
│  [ 📄 Ingesta ]  [ 📊 Telemetría 360° ]  [ 👁️ Visor & Comparador ]  [ 🛡️ Pureza ]  [ ⚙️ Estado ] │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 📄 Pestaña 1: Ingesta y Procesamiento de Documentos
- **Carga de Archivos Drag-and-Drop:** Zona interactiva para arrastrar archivos individuales o múltiples en cualquiera de los 13 formatos admitidos (`.docx`, `.pdf`, `.odt`, `.rtf`, `.xlsx`, `.csv`, `.pptx`, `.html`, `.txt`, `.md`).
- **Selector de Perfil Estilístico:**
  - `general`: Corrección gramatical y de estilo estándar.
  - `tecnico`: Preservación rigurosa de bloques de código, parámetros y tablas.
  - `legal`: Precisión terminológica y estructura jurídica formal.
  - `comercial`: Redacción persuasiva y formal para propuestas y minutas.
  - `academico`: Rigor metodológico y citas bibliográficas.
- **Control de Inferencia:** Selección dinámica de modelo local (ej. `qwen2.5:3b`, `qwen2.5-coder:3b`, `qwen2.5-coder:32b`) y visualización de progreso con barra porcentual y logs en tiempo real.

### 📊 Pestaña 2: Monitoreo y Telemetría Hardware 360°
- **Monitoreo de GPU NVIDIA (GTX 1650 / RTX PRO 4000):**
  - **VRAM Total, Usada y Libre:** Lectura física en megabytes y porcentaje.
  - **Temperatura de la GPU:** Indicador en grados Celsius (°C) con alertas cromáticas (Verde < 65°C, Ámbar 65–78°C, Rojo > 78°C).
  - **Carga de Cómputo CUDA (%):** Porcentaje de utilización activa de los núcleos de cálculo.
- **Monitoreo de Recursos del Host:**
  - **Memoria RAM del Sistema:** Memoria ocupada, disponible y porcentaje de carga.
  - **Uso Global de CPU (%):** Lectura multi-hilo de procesadores AMD Ryzen e Intel Core i9.
- **Tasa de Refresco:** Actualización automática por sondeo asíncrono cada 3 segundos o bajo demanda.

### 👁️ Pestaña 3: Visor Interactivo y Comparador de Documentos
- **Vista Lado a Lado (Side-by-Side):** Comparación simultánea entre el texto original extraído y el texto corregido por el modelo LLM.
- **Visor PDF / DOCX Embebido:** Previsualización gráfica en línea sin salir de la plataforma mediante `<iframe>` sandboxeado.
- **Historial de Salida:** Listado con enlaces directos para **Ver en Navegador**, **Descargar Binario** o copiar la ruta local en disco.

### 🛡️ Pestaña 4: Auditoría de Pureza Documental (Zero-Chatter)
- **Índice de Pureza (%):** Métrica matemática que certifica la esterilización del documento frente a metatexto de IA.
- **Inspector de Preámbulos y Epílogos:** Muestra exactamente qué frases de cortesía o introducciones fueron podadas por `core/pureza_documental.py`.
- **Aislamiento de Razonamiento (`<think>`):** Despliega el bloque de pensamiento interno generado por modelos tipo DeepSeek-R1 para auditoría técnica, certificando que no contaminó el archivo de salida.

### ⚙️ Pestaña 5: Estado del Sistema y Registro de Modelos
- **Semáforo de Servicios:**
  - **API Gateway (FastAPI):** Estado operativo y latencia del endpoint `/api/health`.
  - **Motor de Inferencia (Ollama):** Conectividad con `http://localhost:11434`.
  - **AnythingLLM:** Estado del contenedor Docker o servicio de escritorio.
- **Catálogo de Modelos Instalados:** Lista los pesos descargados en Ollama, su tamaño en disco, la arquitectura detectada y si soportan visión multimodal (`qwen2.5vl`).

---

## 3. Endpoints de Soporte en `servidor_api.py`

El Dashboard se comunica con el backend a través de endpoints REST optimizados y no-bloqueantes:

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/telemetria/360` | `GET` | Retorna el payload JSON con métricas de GPU (`pynvml`), RAM y CPU (`psutil`). |
| `/api/documentos` | `GET` | Retorna el catálogo de documentos disponibles en `datos/salida_web/` y metadatos. |
| `/api/ver/{nombre}` | `GET` | Renderiza el visor HTML interactivo para previsualizar el documento. |
| `/api/descargar/{nombre}` | `GET` | Descarga el archivo compilado con cabecera `attachment`. |
| `/api/modelos` | `GET` | Consulta a Ollama y retorna la lista de modelos y modelos cargados en VRAM. |
| `/api/health` | `GET` | Chequeo de salud del servicio con tiempos de respuesta en milisegundos. |

---

## 4. Adecuación Corporativa y Anonimización (Clean Corporate UI)

Siguiendo las directivas de presentación comercial e institucional, el frontend fue sometido a una limpieza estética de diseño:
- Se removieron marcas públicas y leyendas internas que exponían la denominación metodológica de arquitectura hacia el usuario final.
- Se mantuvo una estética corporativa neutral de alto nivel (*"Plataforma IA Local"*), preservando la totalidad del rigor técnico en el código interno.

---

## 5. Puesta en Marcha del Dashboard

### En Windows 10 / 11 64-bit (PowerShell):
```powershell
.\Base\scripts\lanzar_frontend_visual.ps1
```

### En GNU/Linux (Bash):
```bash
chmod +x Base/scripts/lanzar_frontend_visual.sh
./Base/scripts/lanzar_frontend_visual.sh
```

El script inicia automáticamente el servidor API en segundo plano si no está activo y abre el navegador por defecto en `http://localhost:8080` (o `http://localhost:8000/dashboard`).

---

## 6. Validación Automatizada TDD

La robustez del Dashboard y su API de telemetría está cubierta por suites específicas en `Base/tests/`:
- **`tests/unit/test_telemetria_360.py`:** Verifica la recolección de métricas hardware, el manejo de hosts sin GPU dedicada (fallback suave a CPU/RAM) y la integridad del contrato JSON.
- **`tests/unit/test_servidor_api.py`:** Valida las rutas de visualización, descarga protegida contra *Path Traversal* y estabilidad de las respuestas HTTP.
