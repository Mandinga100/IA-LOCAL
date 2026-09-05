#!/usr/bin/env bash
# scripts/verificar_permisos_ecc.sh
# Validación criptográfica de inmutabilidad para el arnés /ecc (raíz y ai-harness/ecc)
# Linux Bash (Ubuntu, Debian, Fedora, RHEL, Arch)

set -euo pipefail

CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

NOMBRE_CANDIDATO="${1:-}"
HASH_SELLADO_DEFAULT="b42c3725f996d2937b402298812f10ac4207c47992d73f0bd81d5eea07d1e8dd"
HASH_ESPERADO="${CEO_AUTH_HASH:-$HASH_SELLADO_DEFAULT}"

# 1. Solicitar nombre si no fue suministrado por argumento o entorno
if [ -z "${NOMBRE_CANDIDATO}" ]; then
    if [ -n "${CEO_AUTH_SESSION_NAME:-}" ]; then
        NOMBRE_CANDIDATO="${CEO_AUTH_SESSION_NAME}"
    else
        echo -e "${YELLOW}🛡️ GOBERNANZA /ECC: Acceso a Zonas Inmutables (raíz o ai-harness)${NC}"
        read -r -p "Ingrese el nombre de CEO autorizado para continuar: " NOMBRE_CANDIDATO
    fi
fi

# 2. Normalización canónica (NFD sin tildes, minúsculas, espacios colapsados)
# Utiliza Python 3 para garantizar 100% de paridad con core/ecc_guard.py
if command -v python3 &> /dev/null; then
    NORM=$(python3 -c "import sys, unicodedata; t = sys.argv[1].strip().lower(); nfkd = unicodedata.normalize('NFKD', t); sin_tildes = ''.join(c for c in nfkd if not unicodedata.combining(c)); print(' '.join(sin_tildes.split()))" "${NOMBRE_CANDIDATO}")
    HASH_CALC=$(python3 -c "import sys, hashlib; print(hashlib.sha256(sys.argv[1].encode('utf-8')).hexdigest())" "${NORM}")
else
    # Fallback portable POSIX (tr + sha256sum)
    NORM=$(echo "${NOMBRE_CANDIDATO}" | tr '[:upper:]' '[:lower:]' | xargs)
    HASH_CALC=$(echo -n "${NORM}" | sha256sum | awk '{print $1}')
fi

# 3. Comparación de hashes
HASH_ESPERADO_LOWER=$(echo "${HASH_ESPERADO}" | tr '[:upper:]' '[:lower:]')
HASH_CALC_LOWER=$(echo "${HASH_CALC}" | tr '[:upper:]' '[:lower:]')

if [ "${HASH_CALC_LOWER}" = "${HASH_ESPERADO_LOWER}" ]; then
    echo -e "${GREEN}✅ Identidad de CEO verificada criptográficamente. Permiso de modificación concedido.${NC}"
    export CEO_AUTH_SESSION_TOKEN="${NORM}"
    exit 0
else
    echo -e "${RED}⛔ ACCESO DENEGADO: El nombre ingresado no coincide con el CEO autorizado.${NC}"
    echo -e "${RED}Las carpetas 'ECC/' y 'ai-harness/ecc/' permanecen inmutables y protegidas contra escritura.${NC}"
    exit 1
fi
