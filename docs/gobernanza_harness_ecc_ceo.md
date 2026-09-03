# Directiva de Gobernanza: Inmutabilidad del Arnés /ECC y Autorización Exclusiva del CEO

**Documento:** `docs/gobernanza_harness_ecc_ceo.md`  
**Estado:** POLÍTICA MANDATORIA E INMUTABLE  
**Gobernanza:** SDP-U / Arnés /ECC / Seguridad C-Level  
**Plataforma:** Windows 10 Pro 64-bit | Python 3.13  

---

## 1. Propósito y Separación de los Arneses /ECC

En la arquitectura de la **Plataforma IA Local** coexisten dos instancias del arnés `/ECC`, cada una con una delimitación estricta de alcance y propósito:

| Instancia | Ubicación | Propósito y Alcance | Política de Edición |
|---|---|---|---|
| **Arnés de Proyecto** | `ECC/` (en la raíz) | Marco metodológico interno del proyecto y referencia estandarizada. | **ESTRICTAMENTE INMUTABLE.** Prohibida cualquier modificación por usuarios o desarrolladores. |
| **Arnés de Producción** | `ai-harness/ecc/` | Instancia operativa para la máquina real de producción y gestión con IA Local. | **MÁXIMA PRIVACIDAD Y SEGURIDAD.** Reservado para ejecución productiva. |

---

## 2. Política de Autorización Exclusiva del CEO

> [!IMPORTANT]
> **REGLA DE ORO DE SEGURIDAD:**  
> **Únicamente el CEO está facultado y autorizado para modificar, editar o añadir código en cualquiera de las dos carpetas (`ECC/` y `ai-harness/ecc/`).**

1. **Denegación por Defecto:** Cualquier usuario, proceso o subagente que intente modificar archivos dentro de estas carpetas será bloqueado de manera automática.
2. **Desafío de Identidad:** Ante un intento de modificación, el sistema exige ingresar el nombre de CEO.
3. **No-Divulgación y Cero Hardcodeo:**
   - **El nombre en texto plano del CEO NO está hardcodeado** en ningún archivo del código fuente ni en los repositorios públicos.
   - La verificación se realiza de manera determinista mediante una función hash criptográfica SHA-256 unidireccional.
   - Si la cadena ingresada (tras normalización canónica de minúsculas y espacios) no genera el hash SHA-256 autorizado, el acceso es revocado de inmediato con una excepción `PermissionError`.

---

## 3. Implementación Técnica de la Guardia Criptográfica

### 3.1. Módulo Núcleo: `core/ecc_guard.py`
El módulo intercepta las operaciones de escritura y valida la pertenencia a las zonas protegidas:
```python
from core.ecc_guard import validar_acceso_escritura_ecc

# Valida si una ruta puede ser modificada
try:
    validar_acceso_escritura_ecc("ai-harness/ecc/config.json", nombre_ceo_candidato="nombre_ingresado")
    # Si es el CEO verificado, la ejecución continúa
except PermissionError as e:
    # Si no coincide el hash criptográfico, se aborta la operación
    print(f"Bloqueo de seguridad: {e}")
```

### 3.2. Script de Validación en Consola: `scripts/verificar_permisos_ecc.ps1`
Permite a la consola PowerShell o a los hooks de control verificar interactivamente la identidad antes de aplicar cambios:
```powershell
.\scripts\verificar_permisos_ecc.ps1
```

### 3.3. Configuración de Entorno Seguro
Para pipelines automatizados o sesiones autorizadas, el hash puede ser sobreescrito o provisto mediante variables de entorno:
- `CEO_AUTH_HASH`: Hash SHA-256 esperado (por defecto utiliza el hash sellado criptográfico).
- `CEO_AUTH_SESSION_TOKEN`: Token de sesión para ejecuciones autorizadas en segundo plano.

---

## 4. Matriz de Auditoría y Control de Intentos no Autorizados

| Intento / Escenario | Acción del Sistema | Resultado |
|---|---|---|
| Usuario estándar intenta editar `ECC/agents/` | Interceptado por `core/ecc_guard.py` | `PermissionError: Acceso Denegado` |
| Usuario estándar intenta modificar `ai-harness/ecc/` | Interceptado por `core/ecc_guard.py` | `PermissionError: Acceso Denegado` |
| Candidato ingresa un nombre erróneo o nulo | Fallo de hash criptográfico SHA-256 | Bloqueo total y registro de alerta |
| CEO verificado con hash válido | Verificación positiva SHA-256 | Autorización temporal de escritura |
