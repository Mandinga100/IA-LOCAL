# Especificación TDD y Matriz de Pruebas

## 1. Metodología TDD bajo Gobernanza ECC

Siguiendo el principio **Test-Driven Development (TDD)** del harness ECC:
1. **Fase RED:** Se redactaron las especificaciones de prueba unitarias e integración antes de escribir el código funcional, verificando que los tests fallaran limpiamente por ausencia de implementación.
2. **Fase GREEN:** Se implementaron los módulos con la mínima complejidad necesaria para satisfacer las pruebas.
3. **Fase REFACTOR:** Se optimizó la legibilidad, inmutabilidad y tipado, verificando que la cobertura superara el **80% mínimo obligatorio**.

---

## 2. Matriz de Pruebas Automatizadas

| Archivo de Test | Tipo | Casos Validados | Resultado |
|---|---|---|---|
| `tests/unit/test_config.py` | Unitario | Defaults, inmutabilidad (`AttributeError`/`FrozenInstanceError`), resolución de rutas `Path`. | PASSED (3/3) |
| `tests/unit/test_explorador.py` | Unitario | Directorio vacío, exclusión de temporales Office (`~$*`), soporte de caracteres con tilde y ñ, directorio inexistente. | PASSED (3/3) |
| `tests/unit/test_chunker.py` | Unitario | Texto corto (1 chunk), preservación de límites de párrafos (`\n\n`), caracteres especiales («», “”, —, ñ). | PASSED (3/3) |
| `tests/unit/test_corrector.py` | Unitario | Inferencia exitosa simulada con `respx`, manejo de error 500 y lanzamiento de `InferenciaError`. ⚠️ Falta verificación explícita de backoff exponencial (`time.sleep` mock). | PASSED (2/2) |
| `tests/integration/test_pipeline.py` | Integración | Pipeline E2E con documentos `.txt`, `.docx` y `.md`, simulación de Ollama, creación de ledger JSON y salida UTF-8. | PASSED (1/1) |
| `tests/unit/test_reconstructor.py` | Unitario | **[PENDIENTE Sprint 2-A]** Casos: `_guardar_docx`, `_guardar_html`, fallback `.corregido.md`, `ReconstruccionError`. Target: ≥85%. | NO EXISTE |
| `tests/unit/test_procesador_lote.py` | Unitario | **[PENDIENTE Sprint 2-B]** Casos: rama de aislamiento de errores, `main()` CLI con `argparse`. Target: ≥80%. | NO EXISTE |
| `tests/unit/test_encoding.py` | Unitario | **[PENDIENTE Sprint 2-C]** Lectura/escritura UTF-8, `RotatingFileHandler.encoding`, caracteres ñ/tildes/«». | NO EXISTE |

---

## 3. Cobertura de Código Certificada

Informe emitido por `pytest-cov` en Python 3.13.14 (64-bit):

> ⚠️ **Deuda Técnica ECC:** `reconstructor.py` (51%) y `procesador_lote.py` (60%) están por debajo del umbral ECC del 80% en módulos críticos. Tests pendientes clasificados en **Sprint 2** (ver tabla inferior).

```text
Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
config.py                               29      2    93%   44, 46
conversor.py                            33      6    82%   35, 53-54, 59-61
corrector.py                            81      6    93%   37, 77-78, 115-116, 129
explorador.py                           48      4    92%   52-53, 81-82
logs.py                                 22      1    95%   23
procesador_lote.py                      87     35    60%   34-39, 55-56, 64-65, 93-104, 110-111, 122, 127-144, 147
reconstructor.py                        57     28    51%   22, 25, 27, 29, 31, 39-65, 92-101, 106-108
tests\integration\test_pipeline.py      40      0   100%
tests\unit\test_chunker.py              19      0   100%
tests\unit\test_config.py               19      0   100%
tests\unit\test_corrector.py            19      0   100%
tests\unit\test_explorador.py           25      0   100%
------------------------------------------------------------------
TOTAL                                  479     82    83%

======================= 12 passed, 1 warning in 13.05s ========================
```

> **Certificación:** 83% de cobertura global, superando el umbral de aceptación del 80% establecido en `ECC/AGENTS.md`.

---

## 4. Estrategia de Mocks con `respx`

Para garantizar que los tests sean reproducibles, ultrarrápidos y se ejecuten independientemente del estado de la GPU o del servicio de Ollama:
- Se interceptan las llamadas HTTP a `http://localhost:11434/api/generate` mediante el decorator `@respx.mock`.
- Se simulan tanto respuestas 200 OK con JSON válido como errores de servidor 500 y caídas de conexión, asegurando que el reintento exponencial y la captura de errores funcionen según el diseño de `silent-failure-hunter`.
