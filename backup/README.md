# Almacén de Backups Consolidados del Proyecto

Esta carpeta almacena el respaldo comprimido de la **Plataforma de IA Local**.

---

## 📦 Formato y Estrategia de Compresión

Los backups se generan en formato **`.tar.gz` con compresión GZIP nivel 9** (máxima tasa de compresión), aplicando exclusiones inteligentes y una **política de retención de versión única consolidada** (el script reemplaza automáticamente versiones anteriores para no acumular archivos obsoletos).

### Directorios y Archivos Excluidos:
- `.venv/` (Entorno virtual Python: se restaura con `uv pip install -r requirements.txt`).
- `node_modules/` (Dependencias npm: se restauran con `npm install`).
- `.git/` (Historial de control de versiones).
- `__pycache__/`, `*.pyc` (Bytecode compilado de Python).
- `.pytest_cache/`, `.coverage` (Caché de pruebas y cobertura).
- `backup/` (Se evita la auto-inclusión de backups anteriores).

---

## 🛠️ Cómo Actualizar el Backup

Para actualizar el backup consolidado al estado más reciente del proyecto:

```powershell
.\.venv\Scripts\python.exe scripts/generar_backup.py
```

---

## 🔄 Cómo Restaurar el Backup

Para descomprimir y restaurar el proyecto en cualquier máquina con Windows 10/11 o Linux:

```powershell
# En PowerShell (usando tar nativo de Windows 10):
tar -xzf "backup/backup_plataforma_ia_local_*.tar.gz"

# O mediante Python nativo:
python -c "import tarfile, glob; tarfile.open(glob.glob('backup/*.tar.gz')[0], 'r:gz').extractall('.')"
```
