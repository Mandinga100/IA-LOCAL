import pytest
from pathlib import Path
from explorador import explorar_directorio, DocumentoTarea

def test_explorar_directorio_vacio(tmp_path: Path):
    tareas = explorar_directorio(tmp_path)
    assert tareas == []

def test_explorar_directorio_archivos_validos(tmp_path: Path):
    # Crear estructura de prueba
    sub_dir = tmp_path / "subcarpeta con tilde áñ"
    sub_dir.mkdir(parents=True)
    
    (tmp_path / "archivo1.docx").write_text("dummy", encoding="utf-8")
    (tmp_path / "archivo2.txt").write_text("dummy", encoding="utf-8")
    (tmp_path / "ignorar.xyz").write_text("dummy", encoding="utf-8")
    (tmp_path / "~$temp_office.docx").write_text("dummy", encoding="utf-8")  # Archivo bloqueo Office
    (sub_dir / "documento_anidado.md").write_text("dummy", encoding="utf-8")

    tareas = explorar_directorio(tmp_path)
    nombres = [t.ruta_origen.name for t in tareas]

    assert "archivo1.docx" in nombres
    assert "archivo2.txt" in nombres
    assert "documento_anidado.md" in nombres
    assert "ignorar.xyz" not in nombres
    assert "~$temp_office.docx" not in nombres  # Debe excluir temporales de Office

def test_explorar_directorio_inexistente():
    ruta_falsa = Path("C:/RutaQueNoExisteSeguro_12345")
    tareas = explorar_directorio(ruta_falsa)
    assert tareas == []


# ---------------------------------------------------------------------------
# Sprint 2-A: Path Traversal Guard
# ---------------------------------------------------------------------------
def test_path_traversal_symlink_bloqueado(tmp_path: Path) -> None:
    """
    Un symlink con extension valida (.txt) que apunte fuera del directorio base
    debe ser bloqueado por la guardia is_relative_to() y no incluirse en las tareas.
    """
    dir_base = tmp_path / "base"
    dir_externo = tmp_path / "externo"
    dir_base.mkdir()
    dir_externo.mkdir()

    # Archivo real fuera del directorio base
    archivo_externo = dir_externo / "secreto.txt"
    archivo_externo.write_text("Datos sensibles", encoding="utf-8")

    # Symlink dentro del directorio base apuntando al archivo externo
    symlink = dir_base / "enlace.txt"
    try:
        symlink.symlink_to(archivo_externo)
    except (OSError, NotImplementedError):
        pytest.skip("El sistema de archivos no soporta symlinks en este entorno.")

    tareas = explorar_directorio(dir_base)
    nombres = [t.ruta_origen.name for t in tareas]

    # El symlink que escapa del directorio base debe estar bloqueado
    assert "secreto.txt" not in nombres
    assert "enlace.txt" not in nombres

