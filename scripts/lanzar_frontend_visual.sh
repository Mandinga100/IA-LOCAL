#!/usr/bin/env bash
# lanzar_frontend_visual.sh
# Script nativo Bash para Linux
# Lanza el Frontend Visual e Interfaz Web de la Plataforma IA Local con Servidor API

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
GRAY='\033[0;90m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${CYAN}==========================================================${NC}"
echo -e "${CYAN} LANZANDO FRONTEND VISUAL Y SERVIDOR API (Linux)          ${NC}"
echo -e "${CYAN}==========================================================${NC}"

PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
if [ ! -f "${PYTHON_BIN}" ]; then
    PYTHON_BIN="python3"
fi

echo -e "\n${GREEN}🌐 Interfaz Web Visual disponible en: http://localhost:8000${NC}"
echo -e "${CYAN}📊 Telemetría GPU y API REST activa en: http://localhost:8000/docs${NC}"
echo -e "${GRAY}Presiona Ctrl+C para detener el servidor.\n${NC}"

export PYTHONUTF8=1
cd "${ROOT_DIR}"
exec "${PYTHON_BIN}" "${ROOT_DIR}/servidor_api.py"
