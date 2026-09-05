# Entorno de Producción: Workstation 24 GB VRAM (RTX PRO 4000 + i9-14900)

Esta carpeta contiene la configuración completa, parámetros de modelos, orquestación Docker y scripts operativos para el despliegue en la máquina de producción de alta gama.

---

## 📁 Estructura del Directorio

```
produccion/
├── 01_contexto_produccion_rtx_pro4000_24gb.md  # Especificaciones de hardware y análisis matemático de VRAM
├── 02_modelos_recomendados_produccion.md       # Catálogo de modelos 14B, 32B, DeepSeek R1 y visión
├── 03_guia_operativa_produccion.md            # Guía paso a paso de puesta en marcha y monitoreo
├── docker-compose.yml                         # Orquestación AnythingLLM Multi-User optimizada para 32 GB RAM
├── workspaces/                                # Esquemas JSON de workspaces temáticos de producción
│   ├── 01_documentos_informes_prod.json      # Word/PDF con Qwen 2.5 14B y contexto de 32K
│   ├── 02_hojas_calculo_datos_prod.json      # Excel/CSV con validación cuantitativa y tablas
│   ├── 03_presentaciones_pptx_prod.json      # PowerPoint con síntesis ejecutiva y narrativa
│   └── 04_programacion_scripts_prod.json     # Python/DevOps con Qwen 2.5 Coder 32B
└── scripts/                                   # Scripts PowerShell nativos para Windows
    ├── optimizar_ollama_produccion.ps1        # Calibración de variables (4 slots, FlashAttn, KV Q8_0)
    └── desplegar_anythingllm_produccion.ps1   # Despliegue automatizado de AnythingLLM Multi-User
```

---

## 🚀 Despliegue Rápido en Producción

1. **Calibrar Ollama:**
   ```powershell
   .\produccion\scripts\optimizar_ollama_produccion.ps1
   ```
2. **Descargar Modelos Principales:**
   ```powershell
   ollama pull qwen2.5:14b
   ollama pull qwen2.5-coder:32b
   ollama pull deepseek-r1:14b
   ollama pull bge-m3
   ```
3. **Levantar AnythingLLM Multi-User:**
   ```powershell
   .\produccion\scripts\desplegar_anythingllm_produccion.ps1
   ```
4. **Acceder a la Plataforma:**
   Navegar a `http://localhost:3001` o `http://<IP-WORKSTATION>:3001` desde los equipos clientes.
