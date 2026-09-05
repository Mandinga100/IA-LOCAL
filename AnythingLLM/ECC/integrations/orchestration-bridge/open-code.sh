#!/usr/bin/env bash
# ECC Orchestration Bridge — invocador de OpenCode.
#
# Genera cambios con OpenCode y emite un envelope JSON que el hook
# post-opencode-verify.js consume por stdin.
#
# Uso:
#   open-code.sh generate --task-type bulk_codegen --prompt-file /tmp/p.md [--model X]
#   open-code.sh models --list
#
# Requiere: ECC_OPENCODE_URL, ECC_OPENCODE_TOKEN, jq, git.
# Antigravity NO se invoca desde aqui. Es un binario/endpoint distinto y su
# gate vive en pre-opencode-gate.js; mezclarlos aqui haria trivial saltarse
# el cerrojo experimental.

set -euo pipefail

BRIDGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$BRIDGE_DIR" rev-parse --show-toplevel)"
POLICY="${ECC_BRIDGE_POLICY:-$BRIDGE_DIR/model-route.yaml}"

# --- allowlist: nada de shell arbitrario -----------------------------------
ALLOWED_COMMANDS="generate refactor script scaffold models"

die() { printf '[open-code] %s\n' "$1" >&2; exit "${2:-1}"; }

require_env() {
  local name="$1"
  [ -n "${!name:-}" ] || die "falta \$$name (no lo pongas en un archivo del repo)"
}

# --- parseo -----------------------------------------------------------------
COMMAND="${1:-}"
[ -n "$COMMAND" ] || die "uso: open-code.sh <${ALLOWED_COMMANDS// /|}> [opciones]"
shift

case " $ALLOWED_COMMANDS " in
  *" $COMMAND "*) ;;
  *) die "comando '$COMMAND' fuera de la allowlist ($ALLOWED_COMMANDS)" ;;
esac

TASK_TYPE=""
PROMPT_FILE=""
MODEL=""
TIMEOUT_S="${ECC_BRIDGE_TIMEOUT:-300}"
EXPERIMENTAL="false"

while [ $# -gt 0 ]; do
  case "$1" in
    --task-type)    TASK_TYPE="${2:?}"; shift 2 ;;
    --prompt-file)  PROMPT_FILE="${2:?}"; shift 2 ;;
    --model)        MODEL="${2:?}"; shift 2 ;;
    --timeout)      TIMEOUT_S="${2:?}"; shift 2 ;;
    --experimental) EXPERIMENTAL="true"; shift ;;
    --list)         shift ;;
    *) die "opcion desconocida: $1" ;;
  esac
done

require_env ECC_OPENCODE_URL
require_env ECC_OPENCODE_TOKEN

# --- models --list: sirve para verificar los slugs sin verificar del YAML ---
if [ "$COMMAND" = "models" ]; then
  curl -sS --max-time 30 \
    -H "Authorization: Bearer ${ECC_OPENCODE_TOKEN}" \
    "${ECC_OPENCODE_URL}/v1/models" \
  | jq -r '.data[]? // .models[]? | "\(.id)\t\(.pricing.tier // "free")"'
  exit 0
fi

[ -n "$TASK_TYPE" ]   || die "--task-type es obligatorio"
[ -f "$PROMPT_FILE" ] || die "--prompt-file no existe: $PROMPT_FILE"

# --- resolucion de modelo ---------------------------------------------------
# Si no viene --model, lo resuelve route-task contra model-route.yaml.
if [ -z "$MODEL" ]; then
  MODEL="$(node "$BRIDGE_DIR/scripts/route-task.js" \
             --policy "$POLICY" --task-type "$TASK_TYPE" --field model_id)"
fi
[ -n "$MODEL" ] || die "no se pudo resolver un modelo para task_type=$TASK_TYPE"

RUN_ID="${ECC_RUN_ID:-$(date +%s)-$$}"
BASE_REF="$(git -C "$REPO_ROOT" rev-parse HEAD)"
START_MS=$(( $(date +%s%N) / 1000000 ))

# --- invocacion -------------------------------------------------------------
REQ_BODY="$(jq -n \
  --arg task_type "$TASK_TYPE" \
  --arg model "$MODEL" \
  --arg prompt "$(cat "$PROMPT_FILE")" \
  --arg repo "$REPO_ROOT" \
  --argjson timeout "$TIMEOUT_S" \
  --argjson experimental "$EXPERIMENTAL" \
  '{task_type:$task_type, model:$model, prompt:$prompt,
    repo_path:$repo, timeout_s:$timeout, experimental:$experimental}')"

set +e
RESPONSE="$(curl -sS --max-time "$TIMEOUT_S" \
  -X POST "${ECC_OPENCODE_URL}/v1/${COMMAND}" \
  -H "Authorization: Bearer ${ECC_OPENCODE_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-ECC-Run-Id: ${RUN_ID}" \
  --data "$REQ_BODY")"
CURL_EXIT=$?
set -e

END_MS=$(( $(date +%s%N) / 1000000 ))
DURATION_MS=$(( END_MS - START_MS ))

if [ $CURL_EXIT -ne 0 ]; then
  jq -n --arg run_id "$RUN_ID" --arg model "$MODEL" --arg tt "$TASK_TYPE" \
        --argjson dur "$DURATION_MS" --argjson code "$CURL_EXIT" \
    '{schema:"ecc.bridge.artifact/v1", run_id:$run_id, engine:"opencode",
      model:$model, task_type:$tt, exit_code:$code, duration_ms:$dur,
      error:"transport_failure", diff:"", files:[]}'
  exit 0    # exit 0 a proposito: el hook decide, el script no bloquea la sesion
fi

# --- envelope para el hook --------------------------------------------------
DIFF="$(git -C "$REPO_ROOT" diff "$BASE_REF" 2>/dev/null || printf '')"
DIFF_SHA="$(printf '%s' "$DIFF" | sha256sum | cut -d' ' -f1)"

jq -n \
  --arg run_id "$RUN_ID" \
  --arg model "$MODEL" \
  --arg tt "$TASK_TYPE" \
  --arg base "$BASE_REF" \
  --arg diff "$DIFF" \
  --arg sha "$DIFF_SHA" \
  --argjson dur "$DURATION_MS" \
  --argjson resp "$RESPONSE" \
  '{schema:"ecc.bridge.artifact/v1",
    run_id:$run_id, engine:"opencode", model:$model, task_type:$tt,
    base_ref:$base, exit_code:($resp.exit_code // 0),
    duration_ms:$dur, artifact_sha256:$sha,
    files:($resp.files // []), diff:$diff,
    usage:($resp.usage // {}),
    stdout:(($resp.stdout // "") | .[0:4000])}' \
| tee -a "${ECC_BRIDGE_ARTIFACTS:-$HOME/.claude/metrics}/artifacts.jsonl"
