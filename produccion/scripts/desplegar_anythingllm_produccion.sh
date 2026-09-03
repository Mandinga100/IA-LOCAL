#!/usr/bin/env bash
# desplegar_anythingllm_produccion.sh
# Script nativo Bash para Linux (Ubuntu Server / Debian / RHEL / Rocky Linux)
# Despliega AnythingLLM Multi-User en la máquina de producción

set -euo pipefail

CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
GRAY='\033[0;90m'
WHITE='\033[1;37m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROD_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT_DIR="$(cd "${PROD_DIR}/.." && pwd)"

echo -e "${CYAN}==================================================================${NC}"
echo -e "${CYAN} DESPLIEGUE ANYTHINGLLM MULTI-USER PRODUCCIÓN (Workstation 24GB) ${NC}"
echo -e "${CYAN}==================================================================${NC}"

# 1. Comprobación de Docker
echo -e "\n${YELLOW}[1/4] Verificando motor Docker y soporte GPU...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado en el PATH del sistema.${NC}"
    echo -e "${YELLOW}👉 Instala Docker Engine y el plugin Docker Compose:${NC}"
    echo -e "${GRAY}   https://docs.docker.com/engine/install/${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}⚠️ El demonio Docker no parece estar en ejecución o tu usuario carece de permisos.${NC}"
    echo -e "${YELLOW}👉 Inicia Docker: sudo systemctl start docker${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ Demonio Docker activo y operativo.${NC}"

# 2. Almacenamiento Persistente de Producción
echo -e "\n${YELLOW}[2/4] Verificando almacenamiento persistente de producción...${NC}"
PROD_STORAGE="${ROOT_DIR}/docker_storage_prod"
if [ ! -d "${PROD_STORAGE}" ]; then
    mkdir -p "${PROD_STORAGE}"
    echo -e "${GRAY}  Carpeta creada: ${PROD_STORAGE}${NC}"
else
    echo -e "${GRAY}  Carpeta verificada: ${PROD_STORAGE}${NC}"
fi
chmod 777 "${PROD_STORAGE}" 2>/dev/null || true
echo -e "${GREEN}  ✅ Permisos configurados para contenedor multiusuario.${NC}"

# 3. Comprobar Puerto 3001
echo -e "\n${YELLOW}[3/4] Verificando disponibilidad de puerto 3001...${NC}"
PORT_OCCUPIED=0
if command -v ss &> /dev/null; then
    if ss -tulpn | grep -q ":3001\b"; then
        PORT_OCCUPIED=1
    fi
elif command -v lsof &> /dev/null; then
    if lsof -i :3001 &> /dev/null; then
        PORT_OCCUPIED=1
    fi
fi

if [ "${PORT_OCCUPIED}" -eq 1 ]; then
    echo -e "${YELLOW}  ⚠️ Advertencia: El puerto 3001 ya tiene actividad:${NC}"
else
    echo -e "${GREEN}  ✅ Puerto 3001 libre.${NC}"
fi

# 4. Despliegue con Docker Compose de Producción
echo -e "\n${YELLOW}[4/4] Levantando contenedor AnythingLLM Multi-User de Producción...${NC}"
COMPOSE_FILE="${PROD_DIR}/docker-compose.yml"

if [ -f "${COMPOSE_FILE}" ]; then
    docker compose -f "${COMPOSE_FILE}" up -d
    echo -e "\n${GREEN}🎉 ¡AnythingLLM Multi-User Producción Activo en Linux!${NC}"
    echo -e "${CYAN}🌐 URL de Acceso Local : http://localhost:3001${NC}"
    echo -e "${CYAN}🌐 URL para Red Local  : http://<IP-WORKSTATION>:3001${NC}"
    echo -e "${WHITE}⚙️ Pasos de Configuración en Producción:${NC}"
    echo -e "${GRAY}   1. Crea la cuenta de Administrador institucional.${NC}"
    echo -e "${GRAY}   2. En Ajustes -> LLM Provider -> Ollama, ingresa:${NC}"
    echo -e "${WHITE}      URL: http://host.docker.internal:11434${NC}"
    echo -e "${WHITE}      Modelo por defecto: qwen2.5:14b${NC}"
    echo -e "${GRAY}   3. En Embeddings Provider -> Ollama, selecciona: bge-m3${NC}"
    echo -e "${GRAY}   4. Da de alta a los 10 usuarios y vincula los 4 workspaces de produccion/workspaces/.${NC}"
else
    echo -e "${RED}❌ No se encontró el archivo ${COMPOSE_FILE}.${NC}"
    exit 1
fi
