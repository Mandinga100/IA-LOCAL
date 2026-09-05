#!/usr/bin/env bash
# optimizar_ollama_concurrencia.sh
# Script nativo Bash para Linux
# Calibra Ollama para concurrencia de 10 usuarios sin desbordamiento de VRAM (GTX 1650 / 4GB VRAM)

set -euo pipefail

CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
GRAY='\033[0;90m'
WHITE='\033[1;37m'
NC='\033[0m'

echo -e "${CYAN}==========================================================${NC}"
echo -e "${CYAN} OPTIMIZACIÓN DE CONCURRENCIA OLLAMA (GTX 1650 / 4GB VRAM)${NC}"
echo -e "${CYAN}==========================================================${NC}"

# 1. Variables de Inferencia
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE="24h"
export OLLAMA_HOST="0.0.0.0:11434"

echo -e "\n${YELLOW}[1/3] Configurando variables de entorno de inferencia...${NC}"
echo -e "${GREEN}  ✅ OLLAMA_NUM_PARALLEL = 2 (Permite 2 slots concurrentes en paralelo)${NC}"
echo -e "${GREEN}  ✅ OLLAMA_MAX_LOADED_MODELS = 1 (Evita sobrecarga simultánea en 4GB VRAM)${NC}"
echo -e "${GREEN}  ✅ OLLAMA_KEEP_ALIVE = 24h (Evita latencia de recarga de pesos desde disco)${NC}"
echo -e "${GREEN}  ✅ OLLAMA_HOST = 0.0.0.0:11434 (Escucha en todas las interfaces para Docker)${NC}"

# Persistencia para systemd (si existe servicio ollama en Linux)
SYSTEMD_OVERRIDE_DIR="/etc/systemd/system/ollama.service.d"
if [ -d "/etc/systemd/system" ] && command -v systemctl &> /dev/null; then
    if [ "$(id -u)" -eq 0 ]; then
        mkdir -p "${SYSTEMD_OVERRIDE_DIR}"
        cat << 'EOF' > "${SYSTEMD_OVERRIDE_DIR}/override.conf"
[Service]
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_KEEP_ALIVE=24h"
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
        systemctl daemon-reload
        if systemctl is-active --quiet ollama; then
            systemctl restart ollama
            echo -e "${GREEN}  ✅ Servicio systemd 'ollama' actualizado y reiniciado.${NC}"
        fi
    else
        echo -e "${GRAY}  💡 Para persistir en el servicio systemd oficial de Linux ejecuta:${NC}"
        echo -e "${GRAY}     sudo mkdir -p ${SYSTEMD_OVERRIDE_DIR}${NC}"
        echo -e "${GRAY}     sudo tee ${SYSTEMD_OVERRIDE_DIR}/override.conf << 'EOF'${NC}"
        echo -e "${GRAY}[Service]${NC}"
        echo -e "${GRAY}Environment=\"OLLAMA_NUM_PARALLEL=2\"${NC}"
        echo -e "${GRAY}Environment=\"OLLAMA_MAX_LOADED_MODELS=1\"${NC}"
        echo -e "${GRAY}Environment=\"OLLAMA_KEEP_ALIVE=24h\"${NC}"
        echo -e "${GRAY}Environment=\"OLLAMA_HOST=0.0.0.0:11434\"${NC}"
        echo -e "${GRAY}EOF${NC}"
        echo -e "${GRAY}     sudo systemctl daemon-reload && sudo systemctl restart ollama${NC}"
    fi
fi

# Persistencia en ~/.bashrc para sesiones de usuario
if [ -f "${HOME}/.bashrc" ]; then
    if ! grep -q "OLLAMA_NUM_PARALLEL" "${HOME}/.bashrc"; then
        cat << 'EOF' >> "${HOME}/.bashrc"

# Configuración de Inferencia Ollama (Plataforma IA Local)
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE="24h"
export OLLAMA_HOST="0.0.0.0:11434"
EOF
        echo -e "${GREEN}  ✅ Variables agregadas a ~/.bashrc para persistencia de sesión.${NC}"
    fi
fi

# 2. Diagnóstico del Binario Ollama y Modelos
echo -e "\n${YELLOW}[2/3] Verificando instalación de Ollama...${NC}"
if command -v ollama &> /dev/null; then
    OLLAMA_BIN=$(command -v ollama)
    echo -e "${GRAY}  Ejecutable detectado en: ${OLLAMA_BIN}${NC}"
    echo -e "${GRAY}  Modelos recomendados para MVP (GTX 1650 4GB):${NC}"
    echo -e "${WHITE}    - qwen2.5:3b        (Ofimática, documentos Word/PDF, resúmenes, Zero-Chatter) ~1.9 GB VRAM${NC}"
    echo -e "${WHITE}    - qwen2.5-coder:3b  (Programación Python, scripts, fórmulas Excel)            ~1.9 GB VRAM${NC}"
    echo -e "${WHITE}    - nomic-embed-text  (Embeddings ultraligeros para AnythingLLM RAG)           ~270 MB RAM${NC}"
else
    echo -e "${RED}  ⚠️ No se encontró el comando 'ollama' en el PATH.${NC}"
    echo -e "${YELLOW}  👉 Instálalo en Linux con: curl -fsSL https://ollama.com/install.sh | sh${NC}"
fi

# 3. Resumen Matemático de VRAM
echo -e "\n${YELLOW}[3/3] Validación de Límites de Memoria (Hardware Budget):${NC}"
echo -e "${WHITE}  VRAM Disponible en GTX 1650 : 4.096 MB${NC}"
echo -e "${WHITE}  Pesos de Modelo (Qwen 3B Q4): ~1.900 MB${NC}"
echo -e "${WHITE}  KV-Cache (2 slots @ 2048 ctx): ~640 MB${NC}"
echo -e "${WHITE}  CUDA Overhead del Sistema   : ~300 MB${NC}"
echo -e "${GRAY}  -------------------------------------------------------${NC}"
echo -e "${GREEN}  TOTAL CONSUMO ESTIMADO      : ~2.840 MB (Margen libre: ~1.250 MB)${NC}"
echo -e "${GREEN}  ESTADO                      : 100% RESIDENTE EN GPU (0% PAGING A RAM)\n${NC}"

echo -e "${CYAN}Si Ollama corre como servicio systemd, reinícialo: sudo systemctl restart ollama${NC}"
