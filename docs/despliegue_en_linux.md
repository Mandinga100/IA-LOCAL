# Guía de Despliegue y Operación en Linux

Esta guía detalla el aprovisionamiento, optimización de hardware y despliegue de la **Plataforma IA Local** en distribuciones GNU/Linux (Ubuntu 22.04 / 24.04 LTS, Debian 12, Fedora, RHEL / Rocky Linux y Arch Linux), operando en **paralelo simétrico** con la versión de Windows 10 / 11 64-bit.

---

## 📋 Requisitos del Sistema en Linux

### Paquetes Base y Herramientas del Sistema
```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y curl git python3 python3-venv python3-pip build-essential

# Fedora / RHEL / Rocky Linux
sudo dnf install -y curl git python3 python3-pip gcc make
```

### Gestor de Entornos Python (`uv` recomendado)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### Docker Engine y Plugin Docker Compose
Instala Docker oficial siguiendo la documentación oficial de Linux:
```bash
# Agregar usuario actual al grupo docker (para ejecutar sin sudo)
sudo usermod -aG docker $USER
newgrp docker
```

---

## 🎮 Aceleración por GPU NVIDIA (CUDA y Docker)

Para aprovechar la aceleración por hardware en inferencia local (GTX 1650 en MVP o RTX PRO 4000 / GPUs 24GB en Producción):

1. **Drivers NVIDIA y CUDA Toolkit:**
   Verifica la detección con:
   ```bash
   nvidia-smi
   ```

2. **NVIDIA Container Toolkit (para Docker con GPU):**
   ```bash
   # Ubuntu / Debian
   curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
   curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
     sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
     sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
   sudo apt update && sudo apt install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

---

## 🦙 Instalación y Optimización del Motor Ollama

### 1. Instalación Oficial de Ollama en Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
En Linux, Ollama se registra automáticamente como un servicio de `systemd` (`ollama.service`).

### 2. Optimización según el Hardware

#### En Entorno de Desarrollo / MVP (GTX 1650 / 4 GB VRAM):
```bash
chmod +x scripts/*.sh
./scripts/optimizar_ollama_concurrencia.sh

# Descarga de pesos ligeros recomendados
ollama pull qwen2.5:3b
ollama pull qwen2.5-coder:3b
ollama pull nomic-embed-text
```

#### En Entorno de Producción (24 GB VRAM / RTX PRO 4000 / Servidores):
```bash
chmod +x produccion/scripts/*.sh
./produccion/scripts/optimizar_ollama_produccion.sh

# Descarga de modelos de alta gama
ollama pull qwen2.5:14b
ollama pull qwen2.5-coder:32b
ollama pull deepseek-r1:14b
ollama pull qwen2.5vl:7b
ollama pull bge-m3
```

Ambos scripts configuran automáticamente el drop-in de systemd en `/etc/systemd/system/ollama.service.d/override.conf` y aplican `systemctl daemon-reload && systemctl restart ollama`.

---

## 🐳 Despliegue de AnythingLLM Multi-User en Docker

### 1. En Desarrollo / MVP
```bash
./scripts/desplegar_anythingllm_docker.sh
```
- Acceso local: `http://localhost:3001`
- Acceso en red local: `http://<IP-DEL-SERVIDOR>:3001`

### 2. En Producción
```bash
./produccion/scripts/desplegar_anythingllm_produccion.sh
```

El script ajusta automáticamente los permisos de las carpetas de persistencia (`docker_storage/` o `docker_storage_prod/`) con permisos adecuados para el usuario interno del contenedor MintplexLabs, garantizando cero errores de permisos (`EACCES`).

---

## 🚀 Gateway FastAPI y Servidor MCP en Linux

### 1. Preparación del Entorno Virtual
```bash
export PYTHONUTF8=1
uv venv .venv --python 3.13
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. Ejecutar Gateway Local
```bash
python servidor_api.py
```
Disponible en `http://localhost:8000` con documentación interactiva Swagger en `/docs`.

### 3. Ejecución de la Suite TDD
```bash
pytest -q
```
Certifica el 100% de pruebas pasando sin regresiones.

---

## 🛡️ Gobernanza Criptográfica /ECC en Linux

Para verificar permisos de modificación del arnés inmutable:
```bash
./scripts/verificar_permisos_ecc.sh "Nombre Candidato"
```
Valida la huella SHA-256 (`b42c3725f996d2937b402298812f10ac4207c47992d73f0bd81d5eea07d1e8dd`) y exporta el token `CEO_AUTH_SESSION_TOKEN`.

---

## 📊 Matriz de Simetría Multiplataforma

| Operación | Windows 10 / 11 (PowerShell) | Linux (Bash) |
|---|---|---|
| **Optimizar Ollama (MVP 4GB)** | `.\scripts\optimizar_ollama_concurrencia.ps1` | `./scripts/optimizar_ollama_concurrencia.sh` |
| **Optimizar Ollama (Prod 24GB)** | `.\produccion\scripts\optimizar_ollama_produccion.ps1` | `./produccion/scripts/optimizar_ollama_produccion.sh` |
| **Desplegar AnythingLLM (MVP)** | `.\scripts\desplegar_anythingllm_docker.ps1` | `./scripts/desplegar_anythingllm_docker.sh` |
| **Desplegar AnythingLLM (Prod)** | `.\produccion\scripts\desplegar_anythingllm_produccion.ps1` | `./produccion/scripts/desplegar_anythingllm_produccion.sh` |
| **Validar Gobernanza /ECC** | `.\scripts\verificar_permisos_ecc.ps1` | `./scripts/verificar_permisos_ecc.sh` |
| **Ejecutar Pruebas TDD** | `.\.venv\Scripts\pytest.exe` | `pytest` / `.venv/bin/pytest` |
| **Generar Backup** | `.\.venv\Scripts\python.exe scripts/generar_backup.py` | `python3 scripts/generar_backup.py` |
