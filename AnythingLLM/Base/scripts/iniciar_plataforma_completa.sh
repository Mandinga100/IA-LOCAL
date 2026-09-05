#!/usr/bin/env bash
# iniciar_plataforma_completa.sh
# Script maestro Bash simétrico para Linux (Ubuntu/Debian)
# Orquesta la plataforma completa: Ollama, Collector (:8888), AnythingLLM (:3001) y Gateway Base (:8000)

set -euo pipefail

MODO="${1:-Local}"

echo -e "\033[0;36m======================================================================\033[0m"
echo -e "\033[0;36m  PLATAFORMA IA LOCAL & ANYTHINGLLM - ORQUESTADOR MAESTRO UNIFICADO  \033[0m"
echo -e "\033[0;36m======================================================================\033[0m"
echo -e "\033[0;33mModo de ejecución: ${MODO}\033[0m\n"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ANYTHING_DIR="$(cd "${BASE_DIR}/.." && pwd)"
SERVER_DIR="${ANYTHING_DIR}/server"
COLLECTOR_DIR="${ANYTHING_DIR}/collector"
FRONTEND_DIR="${ANYTHING_DIR}/frontend"
PUBLIC_DIR="${SERVER_DIR}/public"

PYTHON_BIN="${BASE_DIR}/.venv/bin/python"
if [ ! -f "${PYTHON_BIN}" ]; then
    PYTHON_BIN="python3"
fi

export PYTHONUTF8=1
export PYTHONIOENCODING="utf-8"

# 1. Comprobación y Optimización de Ollama
echo -e "\033[0;33m[1/5] Verificando servicio Ollama...\033[0m"
if curl -s "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
    echo -e "  \033[0;32m✅ Ollama detectado y activo en http://127.0.0.1:11434\033[0m"
else
    echo -e "  \033[0;33m⚠️ Ollama no responde. Intentando iniciar en segundo plano...\033[0m"
    if command -v ollama >/dev/null 2>&1; then
        export OLLAMA_NUM_PARALLEL=4
        export OLLAMA_MAX_LOADED_MODELS=2
        export OLLAMA_KEEP_ALIVE="24h"
        ollama serve >/dev/null 2>&1 &
        sleep 3
        echo -e "  \033[0;32m✅ Ollama iniciado en background.\033[0m"
    else
        echo -e "  \033[0;31m⚠️ Comando 'ollama' no encontrado en el PATH.\033[0m"
    fi
fi

# 2. Sincronizar Workspaces y Documentos
echo -e "\n\033[0;33m[2/5] Sincronizando workspaces y flujos documentales...\033[0m"
"${PYTHON_BIN}" "${SCRIPT_DIR}/sincronizar_workspaces.py"

# 3. Verificación de Frontend Compilado
echo -e "\n\033[0;33m[3/5] Verificando compilación de frontend AnythingLLM...\033[0m"
if [ ! -f "${PUBLIC_DIR}/_index.html" ]; then
    echo -e "  \033[0;36mFrontend no compilado en server/public. Compilando...\033[0m"
    (cd "${FRONTEND_DIR}" && npm run build)
    mkdir -p "${PUBLIC_DIR}"
    cp -r "${FRONTEND_DIR}/dist/"* "${PUBLIC_DIR}/"
    echo -e "  \033[0;32m✅ Frontend compilado y desplegado en server/public.\033[0m"
else
    echo -e "  \033[0;32m✅ Frontend listo en server/public.\033[0m"
fi

# 4. Lanzamiento de Servicios según Modo
COLLECTOR_PID=""
ANYTHING_PID=""

cleanup() {
    echo -e "\n\033[0;33m======================================================================\033[0m"
    echo -e "\033[0;33m  Cerrando servicios de la plataforma...\033[0m"
    echo -e "\033[0;33m======================================================================\033[0m"
    if [ -n "${COLLECTOR_PID}" ] && kill -0 "${COLLECTOR_PID}" 2>/dev/null; then
        echo -e "  Deteniendo Collector API (PID: ${COLLECTOR_PID})..."
        kill "${COLLECTOR_PID}" 2>/dev/null || true
    fi
    if [ -n "${ANYTHING_PID}" ] && kill -0 "${ANYTHING_PID}" 2>/dev/null; then
        echo -e "  Deteniendo AnythingLLM Server (PID: ${ANYTHING_PID})..."
        kill "${ANYTHING_PID}" 2>/dev/null || true
    fi
    echo -e "  \033[0;32m✅ Servicios detenidos correctamente.\033[0m"
}
trap cleanup EXIT INT TERM

# Liberación preventiva de puertos
liberar_puerto() {
    local port=$1
    if command -v fuser >/dev/null 2>&1; then
        fuser -k "${port}/tcp" >/dev/null 2>&1 || true
    fi
}
liberar_puerto 8000
if [ "${MODO}" != "SoloBase" ]; then
    liberar_puerto 8888
    liberar_puerto 3001
fi

echo -e "\n\033[0;33m[4/5] Inicializando servidores de la plataforma...\033[0m"
if [ "${MODO}" = "Docker" ]; then
    echo -e "  \033[0;36m🐳 Modo Docker seleccionado. Ejecutando compose...\033[0m"
    bash "${SCRIPT_DIR}/desplegar_anythingllm_docker.sh"
elif [ "${MODO}" != "SoloBase" ]; then
    echo -e "  \033[0;36mIniciando Collector (API de Procesamiento de Documentos en puerto 8888)...\033[0m"
    (cd "${COLLECTOR_DIR}" && node index.js) >/dev/null 2>&1 &
    COLLECTOR_PID=$!
    for i in {1..15}; do
        if curl -s "http://127.0.0.1:8888/accepts" >/dev/null 2>&1; then
            echo -e "  \033[0;32m✅ Collector API activo en http://localhost:8888 (PID: ${COLLECTOR_PID})\033[0m"
            break
        fi
        sleep 1
    done

    echo -e "  \033[0;36mIniciando AnythingLLM Server en segundo plano (puerto 3001)...\033[0m"
    (cd "${SERVER_DIR}" && node index.js) >/dev/null 2>&1 &
    ANYTHING_PID=$!
    for i in {1..20}; do
        if curl -s "http://127.0.0.1:3001/api/ping" | grep -q "online" 2>/dev/null; then
            echo -e "  \033[0;32m✅ AnythingLLM Server activo en http://localhost:3001 (PID: ${ANYTHING_PID})\033[0m"
            break
        fi
        sleep 1
    done
fi

# 5. Lanzar Gateway Base
echo -e "\n\033[0;32m[5/5] Levantando Servidor Gateway Base y Dashboard 360° en http://localhost:8000...\033[0m"
echo -e "\033[0;36m======================================================================\033[0m"
echo -e "  \033[0;33mACCESO A LA PLATAFORMA:\033[0m"
echo -e "  -> AnythingLLM (Interfaz Web & Chat) : \033[0;36mhttp://localhost:3001\033[0m"
echo -e "  -> Dashboard 360° & Telemetría        : \033[0;32mhttp://localhost:8000\033[0m"
echo -e "  -> Collector (Ingesta Documental)    : \033[0;37mhttp://localhost:8888\033[0m"
echo -e "  -> Gateway OpenAI Compatible (/v1)   : \033[0;37mhttp://localhost:8000/v1\033[0m"
echo -e "  -> Documentación Swagger API         : \033[0;90mhttp://localhost:8000/docs\033[0m"
echo -e "\033[0;36m======================================================================\033[0m"
echo -e "Presiona Ctrl+C para finalizar.\n"

cd "${BASE_DIR}"
"${PYTHON_BIN}" "servidor_api.py"
