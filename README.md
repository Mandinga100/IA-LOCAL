# Plataforma de Procesamiento y Corrección de Documentos con IA Local

[![GitHub](https://img.shields.io/badge/GitHub-Mandinga100%2FIA--LOCAL-181717.svg?logo=github)](https://github.com/Mandinga100/IA-LOCAL)
![Python](https://img.shields.io/badge/Python-3.13.14-blue.svg)
![OS](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%2064--bit-0078D6.svg)
![Tests](https://img.shields.io/badge/Tests-159%20passed%20%7C%201%20skipped-success.svg)
![AnythingLLM](https://img.shields.io/badge/GUI-AnythingLLM%20Multi--User%20Docker-orange.svg)
![Hardware](https://img.shields.io/badge/Hardware-Dual%20(GTX%201650%204GB%20%7C%20RTX%20PRO%204000%2024GB)-brightgreen.svg)
![Governance](https://img.shields.io/badge/Governance-ECC%20Curated%20(3.5MB)-purple.svg)
![Security](https://img.shields.io/badge/CEO%20Auth-SHA256%20Cryptographic%20Guard-red.svg)

Sistema industrial, soberano y desacoplado para el procesamiento masivo, corrección ortotipográfica y síntesis de documentos ofimáticos con **Modelos de Lenguaje Locales (LLM)**, operando **100% desconectado de la nube (offline)** sobre **Windows 10 / 11 64-bit**.

Soporta despliegue multi-usuario empresarial (10+ usuarios concurrentes) mediante **AnythingLLM en Docker**, asignación granular de roles, cuatro espacios de trabajo temáticos y optimización matemática de VRAM tanto para hardware restringido (MVP) como para estaciones de producción de alta gama.

---

## 🌟 Características Principales

1. **Soberanía y Privacidad Total:** Cero transmisión de datos al exterior. Inferencia ejecutada 100% en la GPU/CPU local vía Ollama.
2. **Interfaz Gráfica Multi-Usuario (AnythingLLM en Docker):**
   - Servidor web accesible en `http://localhost:3001` (o red local `http://<IP>:3001`).
   - Gobernanza con 3 niveles de roles: *Admin*, *Manager* y *Default User*.
   - Cuatro workspaces departamentales preconfigurados:
     - **01. Documentos e Informes:** Word (`.docx`), PDF, ODT, RTF con protocolo Zero-Chatter.
     - **02. Hojas de Cálculo y Finanzas:** Excel (`.xlsx`, `.xls`) y `.csv` a tablas Markdown estructuradas.
     - **03. Presentaciones Ejecutivas:** Estructuración de diapositivas PowerPoint (`.pptx`) y síntesis ejecutiva.
     - **04. Programación y Scripts:** Automatización en Python 3.13, pruebas TDD y scripts de infraestructura.
3. **Arquitectura Bi-Entorno Calibrada:**
   - **Perfil MVP Local (`MVP/`):** Optimizado para **NVIDIA GeForce GTX 1650 (4 GB VRAM)**, modelos 3B (`qwen2.5:3b`), contexto de 2048 tokens, 2 slots paralelos y consumo de VRAM menor a 2.84 GB (100% en GPU).
   - **Perfil Producción (`produccion/`):** Diseñado para **PNY Quadro RTX PRO 4000 24 GB GDDR7 ECC** (arquitectura Blackwell), Intel Core i9-14900 (24 núcleos) y 128 GB RAM DDR5, con modelos 14B y 32B (`qwen2.5:14b`, `qwen2.5-coder:32b`, `deepseek-r1:14b`, `qwen2.5vl:7b`), contexto de 32K a 65K tokens, FlashAttention y 4 slots paralelos.
4. **Inmutabilidad y Gobernanza /ECC (Exclusividad CEO):**
   - La carpeta `/ECC` en la raíz está reservada netamente para el proyecto y es estrictamente inmutable.
   - La carpeta `ai-harness/ecc/` es la que se utilizará en producción en la máquina real con IA local.
   - Ambas zonas están blindadas criptográficamente (`core/ecc_guard.py` y `scripts/verificar_permisos_ecc.ps1`): **únicamente el CEO autenticado mediante verificación SHA-256 tiene autorización de edición**. El nombre nunca se encuentra hardcodeado en texto plano en el repositorio.
5. **Protocolo Zero-Chatter (Pureza Documental):** Poda automática de saludos, notas conversacionales y bloques `<think>` para compilación física sin contaminación de metatexto.
6. **Preservación Visual Pixel-Perfect:** Extracción de imágenes nativas en PDF/DOCX con huella SHA-256 e inserción proporcional en documentos reconstruidos.
7. **Servidor MCP Oficial (`mcp_server.py`):** Expone 14 herramientas nativas para AnythingLLM (conversión, resumen ejecutivo, marcas de agua, cirugía de imágenes y telemetría de GPU).
8. **Arnés `/ECC` Curado y Saneado:** Reducción del 99% de ruido (de 366 MB a 3.5 MB), preservando únicamente los 8 agentes y 14 skills esenciales para ofimática, presentaciones y código.
9. **Motor de Backup Consolidado:** Generador de respaldo comprimido con GZIP nivel 9 en `backup/` (~1.72 MB) con rotación automática de copias obsoletas.

---

## 🏗️ Arquitectura del Sistema

```
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                           RED LOCAL (10 USUARIOS CONCURRENTES)                         │
 │   - Acceso Web: http://192.168.x.x:3001  o  http://localhost:3001                     │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ HTTP / WebSockets
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                      ANYTHINGLLM MULTI-USER DOCKER CONTAINER                           │
 │   - Imagen: mintplexlabs/anythingllm:latest (Puerto 3001)                              │
 │   - Workspaces: Documentos (Word/PDF) | Finanzas (Excel) | Slides (PPTX) | Código      │
 └───────────────────────┬────────────────────────────────────────┬───────────────────────┘
                         │                                        │
                         │ HTTP host.docker.internal:8000         │ HTTP host.docker.internal:11434
                         ▼                                        ▼
 ┌──────────────────────────────────────────────┐ ┌───────────────────────────────────────┐
 │       GATEWAY LOCAL (servidor_api.py)        │ │         OLLAMA INFERENCE ENGINE       │
 │  - Protocolo Zero-Chatter (Pureza Documental)│ │  - MVP Local : Qwen 2.5 3B (4GB VRAM) │
 │  - Reconstructor Visual Pixel-Perfect        │ │  - Producción: Qwen 2.5 14B/32B (24GB)│
 │  - Servidor MCP con 14 herramientas /ECC     │ │  - Concurrencia paralela configurada  │
 └──────────────────────────────────────────────┘ └───────────────────────────────────────┘
```

---

## 🚀 Despliegue Rápido en Windows 10 / 11

### 1. Preparar Entorno Local
```powershell
# Configurar UTF-8 en PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

# Crear venv e instalar dependencias con uv
uv venv .venv --python 3.13
uv pip install --python .venv -r requirements.txt
```

### 2. Optimización del Motor Ollama según el Hardware

#### En Máquina de Desarrollo (GTX 1650 4 GB):
```powershell
.\scripts\optimizar_ollama_concurrencia.ps1
ollama pull qwen2.5:3b
ollama pull qwen2.5-coder:3b
```

#### En Estación de Producción (RTX PRO 4000 24 GB):
```powershell
.\produccion\scripts\optimizar_ollama_produccion.ps1
ollama pull qwen2.5:14b
ollama pull qwen2.5-coder:32b
ollama pull deepseek-r1:14b
ollama pull bge-m3
```

### 3. Levantar AnythingLLM Multi-User en Docker

#### En Desarrollo / MVP:
```powershell
.\scripts\desplegar_anythingllm_docker.ps1
```

#### En Producción:
```powershell
.\produccion\scripts\desplegar_anythingllm_produccion.ps1
```

---

## 🧪 Suite de Pruebas y Cobertura (TDD)

```powershell
.\.venv\Scripts\pytest.exe
```
- **154 pruebas unitarias e integración PASADAS** (1 omitida por entorno).
- **100% de calidad y ausencia de regresiones**.
- Incluye prueba de estrés con 10 usuarios concurrentes simultáneos (`tests/unit/test_concurrencia_10_usuarios.py`).

---

## 💾 Generar Backup Consolidado

```powershell
.\.venv\Scripts\python.exe scripts/generar_backup.py
```
*Genera un archivo `.tar.gz` ultra-optimizado de **1.72 MB** en `backup/` y purga versiones anteriores.*

---

## 📚 Base Documental del Proyecto

| Directorio / Documento | Descripción Operativa |
|---|---|
| [docs/plan_anythingllm_docker_multiusers_10pax.md](docs/plan_anythingllm_docker_multiusers_10pax.md) | Guía de arquitectura multiusuario, VRAM y gobernanza para 10 usuarios. |
| [docs/integracion_anythingllm_mcp_y_pureza.md](docs/integracion_anythingllm_mcp_y_pureza.md) | Protocolo Zero-Chatter, reconstrucción pixel-perfect y visor web. |
| [produccion/](produccion/README.md) | Entorno de producción (RTX PRO 4000 24 GB ECC + i9-14900 + 128 GB RAM). |
| [MVP/](MVP/README.md) | Entorno de desarrollo restringido (GTX 1650 4 GB VRAM). |
| [ECC/](ECC/README.md) | Arnés /ECC curado con 8 agentes y 14 skills prioritarias. |
| [docs/contexto_proyecto.md](docs/contexto_proyecto.md) | Especificaciones de ingeniería, principios ECC y stack consolidado. |
