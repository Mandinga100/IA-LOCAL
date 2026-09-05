# Guía Operativa de Producción: Workstation 24 GB VRAM

**Documento:** `produccion/03_guia_operativa_produccion.md`  
**Destino:** Administradores y Operadores de la Workstation de Producción  
**Gobernanza:** SDP-U / Arquitectura /ECC  

---

## 1. Puesta en Marcha Inicial

### Paso 1: Configurar Variables de Rendimiento en Windows
Ejecutar en PowerShell nativo como Administrador:
```powershell
.\produccion\scripts\optimizar_ollama_produccion.ps1
```
Este script activa:
- `OLLAMA_NUM_PARALLEL=4`: Cuatro canales de inferencia paralela simultánea.
- `OLLAMA_FLASH_ATTENTION=1`: FlashAttention nativo activado en la arquitectura Blackwell.
- `OLLAMA_KV_CACHE_TYPE=q8_0`: Compresión de KV-Cache de alta fidelidad sin pérdida semántica.
- `OLLAMA_MAX_LOADED_MODELS=2`: Permite mantener dos modelos en memoria (ej. `qwen2.5:14b` + `qwen2.5vl:7b`).
- `OLLAMA_KEEP_ALIVE=24h`: Residencia caliente continua.

### Paso 2: Descarga de Modelos Homologados
Ejecutar en PowerShell:
```powershell
ollama pull qwen2.5:14b
ollama pull qwen2.5-coder:32b
ollama pull deepseek-r1:14b
ollama pull qwen2.5vl:7b
ollama pull bge-m3
```

### Paso 3: Desplegar AnythingLLM Multi-User en Docker
Ejecutar:
```powershell
.\produccion\scripts\desplegar_anythingllm_produccion.ps1
```
El contenedor se iniciará en `http://localhost:3001` (y accesible para toda la red local en `http://<IP-WORKSTATION>:3001`).

---

## 2. Monitoreo y Telemetría en Tiempo Real

Para verificar el estado de la GPU NVIDIA RTX PRO 4000 y el uso de memoria ECC:
```powershell
nvidia-smi -l 2
```
Métricas normales en producción:
- **VRAM Usada:** 12.000 – 18.500 MB / 24.576 MB.
- **Temperatura GPU:** 45 – 65 °C.
- **Utilización GPU:** 60 – 95% durante picos de generación paralela.
- **Memoria ECC:** Cero errores no corregibles (`Volatile Uncorr. ECC = 0`).

---

## 3. Gobernanza de Usuarios en Producción

1. **Alta de Usuarios (10+ usuarios):**
   - El Administrador genera enlaces de invitación o credenciales directas desde el panel de AnythingLLM.
2. **Asignación de Workspaces:**
   - Cada usuario se vincula a su departamento correspondiente utilizando los esquemas de [produccion/workspaces/](file:///c:/Users/mandi/Documents/Proyectos/Plataforma%20IA%20local/produccion/workspaces).
3. **Privacidad Offline Estricta:**
   - La variable `DISABLE_TELEMETRY=true` garantiza que ninguna información ni fragmento documental salga de la máquina local.
