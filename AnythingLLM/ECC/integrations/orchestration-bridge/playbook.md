# ECC Orchestration Bridge — Playbook (artefacto C)

Claude Code orquesta y verifica. OpenCode genera. Antigravity está apagado.

> **Estado**: implementado y verificado — 43/43 tests, eslint limpio.
> El flujo completo se ejecuta con clientes stub, sin llamar a ningún modelo.
>
> Falta una sola cosa para operarlo de verdad: un **adaptador de verificación**
> (`ECC_BRIDGE_VERIFIER`) que conecte triage y validación final a modelos
> reales. Sin él el bridge funciona, pero manda todo a revisión humana — a
> propósito (§0.3).

---

## 0. El bridge es opcional

Es una **capacidad del harness, no una ruta obligatoria**. Por defecto está
apagado. Sin activarlo, el harness se comporta exactamente igual que si el
bridge no estuviera instalado: no se escribe ledger, no se emite salida, el
stdin de cada hook vuelve intacto.

### 0.1 Cómo se activa

Tres niveles, del más amplio al más estrecho:

| Nivel | Mecanismo | Efecto |
|---|---|---|
| Proyecto | `.claude/bridge.json` con `{"enabled": true}` | activa en ese repo |
| Sesión | `ECC_BRIDGE=on` / `ECC_BRIDGE=off` | override; `off` gana siempre |
| Tarea | `"scope": ["src/**"]` en `bridge.json` | sólo tareas que toquen esas rutas |

Precedencia: `ECC_BRIDGE=off` > `bridge.json` > apagado. El `scope` del
proyecto acota **incluso** con `ECC_BRIDGE=on` — un override de sesión sube el
interruptor general, no salta los límites que el proyecto declaró.

Plantilla lista para copiar: `bridge.json.example`.

### 0.2 Reversible y transparente

Desactivar es borrar `.claude/bridge.json` o poner `enabled: false`. No queda
estado que limpiar ni hooks a medio correr. Al activarse, el bridge escribe en
el ledger **por qué** está activo (`source`, `reason`), así que siempre se puede
saber bajo qué regla actuó sin leer el código.

Un `bridge.json` corrupto **no** activa nada: el default sigue siendo apagado.

### 0.3 Dos excepciones, ambas deliberadas

1. **El gate de PreToolUse no se apaga con `ECC_BRIDGE=off`.** Pero sólo
   reacciona a invocaciones de `open-code.sh`; todo lo demás pasa intacto. Si
   alguien ejecuta el script del bridge, está usando el bridge para ese comando,
   y desactivar una comprobación de seguridad justo ahí sería el peor momento
   posible. Apagar el bridge quita el flujo, no los cerrojos del flujo.

2. **Sin adaptador de verificación no se aprueba nada.** Si `ECC_BRIDGE_VERIFIER`
   no está configurado, el pipeline corre los gates deterministas y luego manda
   a revisión humana en vez de aprobar. Un verificador que aprueba sin haber
   verificado es peor que no tener verificador.

---

## 1. Razonamiento del diseño

### 1.1 Por qué partir triage (Sonnet 5) y validación final (Opus 4.8)

El coste de verificar un diff está dominado por los **tokens de entrada**, no por
los de salida. El diff completo, el contexto del repo y el checklist del PR se
pagan una vez por cada modelo que los lea. Si Opus verifica todo, se paga el
precio de Opus por leer un diff que en el 70–80 % de los casos es rutinario.

El reparto funciona porque **triage y validación no son la misma tarea**:

- **Triage** es reducción: leer mucho, emitir poco (una lista de checks, una
  clase de riesgo, un booleano `needs_deep_review`). Es tolerante a error porque
  su fallo se recupera — si sobre-escala, se paga Opus de más una vez; el error
  caro sería sub-escalar, y por eso los `touches_paths` de la regla `r5` fuerzan
  la escalada sin consultar al modelo.
- **Validación final** es juicio: leer poco (el diff más los hallazgos ya
  acotados por el triage) y decidir con alta fidelidad. Es intolerante a error.

Así Opus lee un contexto **ya recortado** y sólo en los casos que lo merecen. El
ahorro no viene de "usar un modelo más barato", viene de que el modelo caro lee
menos y con menos frecuencia.

El segundo efecto es de precisión, no de coste: un modelo al que se le pide
"revisa esto" sobre un diff grande diluye la atención. Darle a Opus una lista
concreta de sospechas del triage convierte una pregunta abierta en varias
cerradas, que es donde los modelos aciertan más.

Y hay un tercer nivel que **casi nunca debe dispararse**: los gates
deterministas. `eslint`, `node tests/run-all.js` y el audit de seguridad son
más baratos y más fiables que cualquier LLM para lo que saben responder. Corren
primero. Si los tests fallan, no se gasta ni un token en preguntarle a un modelo
si el código está bien.

### 1.2 Por qué OpenCode para la generación masiva

No es una cuestión de calidad de modelo, es de **forma de la tarea**:

- La generación masiva es *escribir mucho*: los tokens de salida dominan y es
  exactamente donde el precio por token pesa. Los modelos free de OpenCode
  hacen ese trabajo a coste marginal cero.
- El error de generación es **barato y detectable**. Un codemod mal hecho lo
  caza el linter o el test suite en segundos. No hace falta que el generador sea
  el modelo más fiable; hace falta que el verificador lo sea.
- OpenCode ya tiene el bucle de escritura montado en este repo
  (`.opencode/plugins/ecc-hooks.ts`, `tools/`): aplica diffs, corre formatters,
  gestiona `changed-files`. Reimplementar eso desde Claude Code sería trabajo
  duplicado.
- Separar generación de verificación evita el sesgo del auto-review: el modelo
  que escribió el código es el peor situado para juzgarlo.

El corolario: **la calidad del sistema la fija el verificador, no el generador**.
Por eso el presupuesto se gasta en Opus para revisar, no en Opus para escribir.

### 1.3 Cuándo invocar Antigravity

Sólo con **doble cerrojo** — `experimental: true` en el payload **y**
`ECC_ALLOW_ANTIGRAVITY=1` en el entorno. Un flag dentro del payload lo puede
poner cualquiera que construya la petición; la variable de entorno la controla
quien despliega. Los dos, o ninguno.

Casos concretos que lo justifican:

| Caso | Regla |
|---|---|
| Scaffolding de un prototipo desechable | escritura limitada a `scaffold/**`, `examples/**` |
| Explorar una forma de API antes de comprometerse | el output **nunca** se mergea sin humano |
| Comparar un enfoque alternativo al de OpenCode | corre en sandbox, se descarta por defecto |

Casos que **nunca** lo justifican: cualquier cosa en la ruta de merge, en
`.github/`, en `scripts/hooks/`, en instalación, o que toque credenciales.
`max_retries: 0` — si falla, cae a OpenCode y se acabó.

### 1.4 Plan de optimización iterativa (A/B)

Empezar conservador y aflojar **sólo** con evidencia. Ninguna fase avanza por
calendario; avanza por métrica.

- **Fase 0 — línea base (2 semanas).** Opus valida todo lo que el triage marque,
  y además un 100 % de sombra: Sonnet emite su veredicto y Opus lo emite también,
  pero decide Opus. Sirve para medir el **desacuerdo** Sonnet↔Opus sin arriesgar
  nada. Coste alto a propósito.
- **Fase 1 — recorte por acuerdo.** Si en la fase 0 Sonnet coincide con Opus
  en ≥95 % de los casos `risk_class != critical`, dejar de escalar esos casos.
  Mantener la sombra al 20 % como muestreo permanente.
- **Fase 2 — A/B de planificación.** Fable vs Opus en `r6`, 50/50, midiendo
  retrabajo posterior (¿cuántos planes acaban replanificándose?), no la opinión
  sobre el plan.
- **Fase 3 — modelos de OpenCode.** A/B entre los tres slugs por `task_type`,
  midiendo `pass_rate` del primer intento. El más barato que mantenga el
  pass_rate gana.
- **Regla de rollback**: si `human_review_rate` sube >5 puntos o aparece
  cualquier defecto de seguridad en producción, se vuelve a la fase anterior
  inmediatamente. La telemetría de la fase que falló se conserva.

Umbral que **no** se toca en ninguna fase: `score < 0.70 ⇒ human_review`.

---

## 2. Despliegue

### Paso 1 — Verificar los slugs de OpenCode

Los IDs de Claude están verificados (`claude-fable-5`, `claude-sonnet-5`,
`claude-opus-4-8`). Los de OpenCode **no**: "Deepseek v4 Flash", "Big Pícke" y
"hy3" del brief no corresponden a slugs confirmables desde aquí, y "Big Pícke"/
"hy3" parecen transcripciones. Antes de nada:

```bash
export ECC_OPENCODE_URL=https://…
export ECC_OPENCODE_TOKEN=…          # nunca en un archivo del repo
integrations/orchestration-bridge/open-code.sh models --list
```

Con la salida real, fijar en el entorno y poner `verified: true` en
`model-route.yaml`:

```bash
export ECC_OC_MODEL_BULK=…
export ECC_OC_MODEL_REFACTOR=…
export ECC_OC_MODEL_SCRIPT=…
```

Mientras `verified: false`, cada entrada del ledger lo arrastra: si algo sale
raro, se ve en el log que el modelo no estaba confirmado.

### Paso 2 — Implementar los scripts de hook

Todos los scripts que referencia `hookify-config.json` existen ya:

| Script | Responsabilidad | Contrato |
|---|---|---|
| `scripts/route-task.js` | resolver regla → `{engine, model, fallback, retries, timeout, cost_cap}` | puro, sin red |
| `scripts/decision.js` | gates + matriz de decisión | puro, sin eval |
| `scripts/verify-pipeline.js` | gates → triage → final → decisión | clientes inyectados |
| `scripts/pre-opencode-gate.js` | auth, allowlist, doble cerrojo Antigravity, cost cap | **blocking, <200 ms, sin red** |
| `scripts/post-opencode-verify.js` | entrada de PostToolUse; detecta fallo por su cuenta | async, timeout 30 s |
| `scripts/post-opencode-failure.js` | política de reintentos | async, timeout 20 s |
| `scripts/bridge-session-init.js` | cargar policy, abrir ledger, fijar `run_id` | async |
| `scripts/bridge-session-close.js` | cerrar ledger, resumen del run | async |
| `scripts/bridge-session.js` | lógica compartida de las tres entradas de sesión | no-op si el bridge está off |
| `scripts/lib/bridge-config.js` | activación: env → proyecto → scope → default off | puro |
| `scripts/lib/ledger.js` | escritura JSONL + redacción de credenciales | nunca lanza |
| `scripts/lib/verifier-clients.js` | gates reales; triage/final vía adaptador | ver §0.3 |

Lo único que falta para operar: escribir el adaptador de `ECC_BRIDGE_VERIFIER`.

Reglas de `.claude/rules/node.md` que aplican: CommonJS, `exit 0` ante error
propio, ≤200 líneas por hook (extraer a `scripts/lib/`), prefijo `[BridgeGate]`
en stderr.

`post-opencode-verify.js` **debe** detectar el fallo por su cuenta
(`tool_response.success === false` o `exit_code !== 0`). `PostToolUseFailure`
está en `schemas/hooks.schema.json` de este repo pero no es un evento que el
runtime de Claude Code emita hoy; la entrada queda por compatibilidad futura,
no como mecanismo del que depender.

### Paso 3 — Fusionar los hooks

Fusionar el bloque `hooks` de `hookify-config.json` en `.claude/settings.json`
(añadir a los arrays existentes, no reemplazarlos). Validar:

```bash
node -e "require('./scripts/lib/hook-flags')" && \
npx ajv validate -s schemas/hooks.schema.json -d .claude/settings.json
```

`ECC_ALLOW_ANTIGRAVITY` se queda a `"0"`. Los tokens **no** van en
`settings.json` — ese archivo se commitea.

### Paso 4 — Permisos del invocador

```bash
chmod +x integrations/orchestration-bridge/open-code.sh
```

En Windows corre vía Git Bash. `open-code.sh` necesita `jq`, `curl` y `git`.

---

## 3. Pruebas

```bash
# routing, gate y matriz de decisión (deterministas)      -> 23 tests
node tests/integrations/orchestration-bridge.test.js

# opt-in + flujo end-to-end con clientes stub              -> 20 tests
node tests/integrations/orchestration-bridge-flow.test.js

# suite completa antes de commitear
node tests/run-all.js
```

Ninguno de los 43 tests llama a un modelo. El pipeline recibe
`runGates`/`triage`/`final` inyectados, que es justamente lo que permite
verificar el flujo entero — incluidas la escalada a Opus y la rama de veto —
sin gastar una llamada.

Integración manual, en este orden:

0. **Sin `.claude/bridge.json`** → el bridge no debe hacer absolutamente nada.
   Es la prueba más importante: si aquí aparece cualquier salida o se crea el
   ledger, el opt-in está roto.
1. `ECC_HOOK_PROFILE=minimal` y un cambio trivial → el bridge no debe disparar.
2. `standard` y un codemod pequeño → debe verse `route → pre_gate → generate →
   gates → triage → decision` en el ledger.
3. Meter un secreto falso en un archivo de prueba → debe cortar en `gates` con
   `llm_invoked: false`. **Revertir inmediatamente.**
4. Pedir `scaffold_prototype` con `experimental: true` → debe denegar.

### Ejemplo de salida de Claude Code

```json
{
  "schema": "ecc.bridge.verdict/v1",
  "run_id": "1784592842-40118",
  "artifact_sha256": "7c1f0a9b3e2d…",
  "status": "approve",
  "aggregate_score": 0.88,
  "threshold": 0.70,
  "security_veto": false,
  "models_used": {
    "generation": "${ECC_OC_MODEL_BULK}",
    "triage": "claude-sonnet-5",
    "final": null
  },
  "checks": [
    { "name": "lint",                "status": "pass", "score": 1.00, "recommendation": null },
    { "name": "tests",               "status": "pass", "score": 1.00, "recommendation": null },
    { "name": "security",            "status": "pass", "score": 1.00, "recommendation": null },
    { "name": "style_conventions",   "status": "pass", "score": 0.94, "recommendation": null },
    { "name": "acceptance_criteria", "status": "pass", "score": 0.90, "recommendation": null },
    { "name": "test_coverage_delta", "status": "warn", "score": 0.72,
      "recommendation": "añadir test para la rama de error en parseConfig()" }
  ],
  "remedial_action": null,
  "human_review_required": false,
  "cost_usd_est": 0.078,
  "duration_ms": 149892
}
```

Con `status: "auto_fix"`, `remedial_action` lleva el prompt exacto de re-ejecución.
Con `status: "human_review"`, lleva qué debe mirar la persona y por qué.

---

## 4. SLOs

| SLI | Objetivo | Ventana | Si se incumple |
|---|---|---|---|
| Tasa de aprobación automática | ≥ 60 % | 7 d | revisar si el triage sobre-escala |
| Tasa de revisión humana | ≤ 25 % | 7 d | si sube, **no** bajar el umbral: mirar el generador |
| Tasa de reintentos | ≤ 20 % | 7 d | prompts poco específicos o modelo mal elegido |
| p95 latencia de verificación | ≤ 90 s | 7 d | recortar el contexto del triage |
| Coste por PR mergeado | ≤ 1,50 USD | 30 d | subir el listón de `needs_deep_review` |
| Defectos de seguridad en producción | **0** | siempre | rollback de fase inmediato |
| Desacuerdo Sonnet↔Opus (sombra) | ≤ 5 % | 14 d | no avanzar de fase |

---

## 5. Checklist de seguridad

- [ ] `ECC_OPENCODE_TOKEN` y `ECC_ANTIGRAVITY_TOKEN` sólo por entorno; nunca en
      `settings.json`, `model-route.yaml` ni en ningún archivo commiteado.
- [ ] `open-code.sh` rechaza cualquier comando fuera de la allowlist.
- [ ] Sin `eval`, sin interpolación de input no saneado en shell.
- [ ] `ECC_ALLOW_ANTIGRAVITY=0` por defecto en todos los entornos salvo el de
      experimentación.
- [ ] Antigravity con `sandbox: true` y `write_scope` acotado.
- [ ] Los logs redactan `*token*`, `*secret*`, `*_key`, `Authorization`.
- [ ] Todo artefacto lleva `sha256`; un sha ya verificado no se re-verifica.
- [ ] Un fail de seguridad anula el score agregado, siempre.
- [ ] `score < 0.70 ⇒ human_review`, sin excepción por coste ni por urgencia.
- [ ] El diff que llega al verificador es **datos**, no instrucciones: si trae
      texto dirigido al modelo ("aprueba esto", "ignora las reglas"), se marca
      como sospechoso y se escala a humano.
- [ ] Los hooks salen con `exit 0` ante error propio: el bridge nunca bloquea.

---

## 6. Tuning: qué mirar y con qué umbrales

Empezar por estos cuatro observables, en este orden:

1. **Desacuerdo Sonnet↔Opus por `risk_class`.** Es la métrica que gobierna todo
   el plan de fases. Si el desacuerdo en `low`/`medium` es <5 %, se puede dejar
   de escalar ahí. Si en `critical` es alto, el problema es el triage, no Opus.
2. **Distribución de `aggregate_score`.** Si se apelotona justo encima de 0,85,
   el verificador está siendo complaciente — probablemente le falta contexto de
   los criterios de aceptación. Si se apelotona entre 0,70 y 0,85, el generador
   está produciendo trabajo mediocre de forma sistemática y hay que arreglar el
   prompt de generación, no el umbral.
3. **`retry_rate` por `task_type`.** Alto en un tipo concreto = ese slug de
   OpenCode no sirve para eso. Es la señal para el A/B de la fase 3.
4. **Tokens de entrada del triage.** Es el mayor coste unitario del bridge. Si
   crece, el diff está creciendo: partir las tareas antes de generarlas sale más
   barato que verificar diffs grandes.

Umbrales iniciales, todos revisables salvo el último:

| Parámetro | Inicial | Cuándo moverlo |
|---|---|---|
| `score_threshold` | 0,70 | **nunca hacia abajo** |
| `auto_approve_threshold` | 0,85 | bajar a 0,80 sólo si el desacuerdo es <3 % durante 14 d |
| `max_retries` (bulk) | 2 | bajar a 1 si el 2.º intento acierta <30 % de las veces |
| `cost_cap_usd` (generación) | 0,30 | subir sólo si el capping dispara >10 % de las veces |
| `cost_cap_usd` (final) | 1,50 | es el gasto que se quiere hacer; no recortarlo |

La trampa a evitar: cuando `human_review_rate` sube, la reacción intuitiva es
bajar el umbral. Eso no mejora nada — sólo deja de mirar. Un umbral alto con
mucho reenvío a humano significa que el **generador** está fallando, y ahí es
donde hay que tocar.

---

## 7. Contenido del paquete

```
integrations/orchestration-bridge/
├── diagram.txt           (A) diagrama técnico: hooks, ruta de modelo, endpoints
├── model-route.yaml      (B) política: 8 reglas, gates, matriz de decisión, SLIs
├── hookify-config.json       hooks para fusionar en .claude/settings.json
├── open-code.sh              invocador de OpenCode + envelope para el hook
├── playbook.md           (C) este archivo
├── example-logs.json     (D) muestras de auditoría (valores ilustrativos)
├── test-cases.json           5 casos con entrada y salida esperada
├── bridge.json.example       plantilla de activación por proyecto
└── scripts/
    ├── route-task.js             resolución de ruta (puro)
    ├── decision.js               gates + matriz de decisión
    ├── verify-pipeline.js        orquestación de la verificación
    ├── pre-opencode-gate.js      gate de PreToolUse
    ├── post-opencode-verify.js   entrada de PostToolUse
    ├── post-opencode-failure.js  política de reintentos
    ├── bridge-session.js         ciclo de vida + 3 envoltorios finos
    └── lib/
        ├── bridge-config.js      activación opt-in
        ├── ledger.js             auditoría JSONL con redacción
        └── verifier-clients.js   gates reales + adaptador LLM

tests/integrations/orchestration-bridge.test.js        23/23
tests/integrations/orchestration-bridge-flow.test.js   20/20
```

Cambios fuera del directorio del bridge:

- `package.json` → `js-yaml` en `dependencies` (`route-task.js` lo necesita y
  sólo llegaba transitivo). El spec es `>=4.2.0` para coincidir exactamente con
  el `override` de seguridad ya existente; npm rechaza un override que no case
  con la dependencia directa.
- `manifests/install-modules.json` → módulo `orchestration-bridge` con
  `defaultInstall: false` y `stability: experimental`. El repo **deriva** el
  array `files` de este grafo y lo verifica en
  `tests/scripts/npm-publish-surface.test.js`: editar `files` a mano rompe el
  test. `defaultInstall: false` es lo que mantiene el principio opt-in también
  en la instalación.
- `package.json` → `files` incluye `integrations/orchestration-bridge/`,
  consecuencia del punto anterior.
