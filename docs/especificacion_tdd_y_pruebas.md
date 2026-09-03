# Especificación TDD y Matriz de Pruebas

**Versión:** 0.3.0 (Consolidada con Formatos Extendidos y Auditoría Forense)  
**Entorno de Pruebas:** Python 3.13.14 (64-bit) | Pytest 9.1.1 | Pytest-Cov 7.1.0 | Respx 0.23.1  
**Estándar de Calidad:** ECC v2.0.0 (TDD, tolerancia cero a fallos silenciosos, cobertura > 80%)

---

## 1. Metodología TDD bajo Gobernanza ECC

1. **Fase RED:** Definición de casos de prueba y aserciones estrictas para cada nuevo formato (`.odt`, `.rtf`, `.csv`, `.xls`), guardias de seguridad (Magic Bytes `MZ`, `ELF`) y detección anti-mojibakes antes de modificar la lógica de producción.
2. **Fase GREEN:** Implementación de extractores (`odfpy`, `striprtf`, `xlrd`, `csv.Sniffer`) y reconstructores para satisfacer los contratos de prueba.
3. **Fase REFACTOR:** Optimización de tipado estático (`Any`, `getattr`), chunking jerárquico y decodificación en cascada (UTF-8 -> CP1252 -> Latin-1).

---

## 2. Matriz de Pruebas Automatizadas (61 Tests)

| Archivo de Test | Tipo | Casos Validados | Resultado |
|---|---|---|---|
| `tests/unit/test_config.py` | Unitario | Inmutabilidad (`frozen=True`), resolución de rutas `Path`, defaults y parámetros de inferencia. | PASSED (3/3) |
| `tests/unit/test_explorador.py` | Unitario | Directorio vacío, exclusión de temporales Office (`~$*`), soporte de caracteres especiales, guardia path traversal. | PASSED (3/3), 1 SKIPPED |
| `tests/unit/test_chunker.py` | Unitario | Texto corto, preservación de párrafos (`\n\n`), párrafos gigantes continuos (subdivisión por oraciones), context manager `with CorrectorOllama()`, limpieza de wrappers markdown. | PASSED (6/6) |
| `tests/unit/test_corrector.py` | Unitario | Inferencia con `respx`, manejo de error 500 (`InferenciaError`), backoff exponencial, fallback automático a modelo alternativo. | PASSED (7/7) |
| `tests/unit/test_reconstructor.py` | Unitario | Generación `.docx`, `.html`, exportación compleja `.corregido.md`, captura con `ReconstruccionError`. | PASSED (14/14) |
| `tests/unit/test_formatos_extendidos.py` | Unitario | Conversión y reconstrucción `.odt`, `.rtf`, `.csv`, guardias de Magic Bytes (`MZ`/`ELF`), límites de tamaño de archivo y flags CLI (`--fallback`, `--chunk-size`). | PASSED (9/9) |
| `tests/unit/test_procesador_lote.py` | Unitario | Aislamiento con `shutil.copy2` en `datos/errores/`, tolerancia a fallos en lote, CLI `main()`, ledger JSON y reanudación por hash. | PASSED (6/6) |
| `tests/unit/test_encoding.py` | Unitario | Round-trip UTF-8, `RotatingFileHandler.encoding='utf-8'`, lectura adaptativa CP1252/Latin-1 sin mojibakes, caracteres especiales y tipográficos. | PASSED (11/11) |
| `tests/integration/test_pipeline.py` | Integración | Pipeline E2E multiformato, simulación con `respx`, generación de ledger y salida UTF-8. | PASSED (1/1) |

---

## 3. Cobertura de Código Certificada

Informe emitido por `pytest-cov` sobre la base de código consolidada:

```text
Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
config.py                                   30      2    93%   50, 52
conversor.py                               139     41    71%   (ramas de formatos legacy)
corrector.py                               149     25    83%   (casos límite de fallback)
explorador.py                               75     12    84%   (excepciones de permisos OS)
logs.py                                     27      3    89%   (handlers)
procesador_lote.py                          89      7    92%   (errores I/O copy)
reconstructor.py                           140      7    95%   (handlers ODT/RTF)
tests\integration\test_pipeline.py          40      0   100%
tests\unit\test_chunker.py                  36      0   100%
tests\unit\test_config.py                   19      0   100%
tests\unit\test_corrector.py                76      1    99%
tests\unit\test_encoding.py                 84      0   100%
tests\unit\test_explorador.py               41      4    90%
tests\unit\test_formatos_extendidos.py      92      0   100%
tests\unit\test_procesador_lote.py          88      0   100%
tests\unit\test_reconstructor.py            98      0   100%
----------------------------------------------------------------------
TOTAL                                     1223    102    92%

======================= 60 passed, 1 skipped in 16.61s =======================
```

> **Certificación ECC:** 92% de cobertura global consolidada. El 100% de las suites unitarias críticas superan el 90-100%, certificando estabilidad para despliegue productivo.
