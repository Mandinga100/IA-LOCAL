#!/usr/bin/env bash
# desplegar_anythingllm_docker.sh
# Script nativo Bash para Linux (Ubuntu, Debian, Fedora, RHEL, Arch)
# Despliega y valida AnythingLLM Multi-User en Docker

set -euo pipefail

CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
GRAY='\033[0;90m'
WHITE='\033[1;37m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${CYAN}==========================================================${NC}"
echo -e "${CYAN}   DESPLIEGUE ANYTHINGLLM MULTI-USER DOCKER (Linux)       ${NC}"
echo -e "${CYAN}==========================================================${NC}"

# 1. Comprobación de Docker
echo -e "\n${YELLOW}[1/4] Verificando motor Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado o no se encuentra en el PATH del sistema.${NC}"
    echo -e "${YELLOW}👉 Instala Docker Engine en tu distribución Linux:${NC}"
    echo -e "${GRAY}   https://docs.docker.com/engine/install/${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}⚠️ Docker está instalado pero el demonio (dockerd) no responde o tu usuario no pertenece al grupo 'docker'.${NC}"
    echo -e "${YELLOW}👉 Inicia el servicio con: sudo systemctl start docker${NC}"
    echo -e "${YELLOW}👉 Agrega tu usuario al grupo docker: sudo usermod -aG docker \$USER && newgrp docker${NC}\n"
    exit 1
fi
echo -e "${GREEN}  ✅ Demonio Docker activo y respondiendo.${NC}"

# 2. Preparar Almacenamiento Persistente
echo -e "\n${YELLOW}[2/4] Preparando almacenamiento local persistente...${NC}"
STORAGE_DIR="${ROOT_DIR}/docker_storage"
if [ ! -d "${STORAGE_DIR}" ]; then
    mkdir -p "${STORAGE_DIR}"
    echo -e "${GRAY}  Carpeta creada: ${STORAGE_DIR}${NC}"
else
    echo -e "${GRAY}  Carpeta existente verificada: ${STORAGE_DIR}${NC}"
fi

# Ajustar permisos para evitar problemas de escritura con contenedores Linux no-root
chmod 777 "${STORAGE_DIR}" 2>/dev/null || true
echo -e "${GREEN}  ✅ Permisos de almacenamiento configurados.${NC}"

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
elif command -v netstat &> /dev/null; then
    if netstat -tuln | grep -q ":3001\b"; then
        PORT_OCCUPIED=1
    fi
fi

if [ "${PORT_OCCUPIED}" -eq 1 ]; then
    echo -e "${YELLOW}  ⚠️ Advertencia: El puerto 3001 ya tiene actividad o está en uso.${NC}"
else
    echo -e "${GREEN}  ✅ Puerto 3001 libre.${NC}"
fi

# 4. Despliegue con Docker Compose
echo -e "\n${YELLOW}[4/4] Levantando contenedor AnythingLLM Multi-User...${NC}"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"

if [ -f "${COMPOSE_FILE}" ]; then
    docker compose -f "${COMPOSE_FILE}" up -d
    echo -e "\n${GREEN}🎉 ¡Contenedor desplegado con éxito en Linux!${NC}"
    echo -e "${CYAN}🌐 URL de Acceso Local : http://localhost:3001${NC}"
    echo -e "${CYAN}🌐 URL para Red Local  : http://<IP-DE-TU-SERVIDOR>:3001${NC}"
    echo -e "${WHITE}⚙️ Primeros Pasos:${NC}"
    echo -e "${GRAY}   1. Abre http://localhost:3001 en tu navegador.${NC}"
    echo -e "${GRAY}   2. Crea la cuenta de Administrador principal.${NC}"
    echo -e "${GRAY}   3. En Ajustes -> LLM Provider, selecciona 'Ollama' con URL:${NC}"
    echo -e "${WHITE}      http://host.docker.internal:11434${NC}"
    echo -e "${GRAY}   4. En Ajustes -> Multi-User, habilita el registro de los 10 usuarios y crea los 4 workspaces.${NC}"
else
    echo -e "${RED}❌ No se encontró docker-compose.yml en ${ROOT_DIR}.${NC}"
    exit 1
fi
