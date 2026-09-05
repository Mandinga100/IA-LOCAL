"""
sincronizar_workspaces.py - Sincronizador de Workspaces y Flujos Documentales
Conecta las especificaciones departamentales de Base y ai-harness con AnythingLLM.
"""

import sys
import json
import sqlite3
import io
from pathlib import Path
from typing import Dict, List, Any, Optional

# Forzar codificación UTF-8 en Windows
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
ANYTHINGLLM_DIR = BASE_DIR.parent
STORAGE_DB = ANYTHINGLLM_DIR / "server" / "storage" / "anythingllm.db"
COLLECTOR_HOTDIR = ANYTHINGLLM_DIR / "collector" / "hotdir"
SALIDA_DOCUMENTOS = BASE_DIR / "datos" / "salida"
OUTPUT_DIR = BASE_DIR / "output"

def obtener_definiciones_workspaces() -> List[Dict[str, Any]]:
    """Carga los workspaces definidos en ai-harness o Base/produccion."""
    rutas_candidatas = [
        ANYTHINGLLM_DIR / "ai-harness" / "ecc" / "workspaces",
        BASE_DIR / "produccion" / "workspaces"
    ]
    
    dir_workspaces = None
    for r in rutas_candidatas:
        if r.exists() and list(r.glob("*.json")):
            dir_workspaces = r
            break
            
    if not dir_workspaces:
        print("⚠️ No se encontró la carpeta de definiciones de workspaces.")
        return []
        
    workspaces = []
    for f in sorted(dir_workspaces.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                workspaces.append(data)
        except Exception as e:
            print(f"❌ Error leyendo {f.name}: {e}")
            
    return workspaces


def sincronizar_sqlite(workspaces: List[Dict[str, Any]]) -> int:
    """Inyecta o actualiza los workspaces directamente en SQLite de AnythingLLM."""
    if not STORAGE_DB.exists():
        print(f"ℹ️ Base de datos SQLite aún no inicializada en: {STORAGE_DB}")
        print("   Se sincronizará automáticamente cuando AnythingLLM arranque por primera vez.")
        return 0
        
    sincronizados = 0
    try:
        conn = sqlite3.connect(STORAGE_DB)
        cursor = conn.cursor()
        
        # Verificar que la tabla workspaces exista
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workspaces'")
        if not cursor.fetchone():
            print("ℹ️ Tabla 'workspaces' no encontrada aún en SQLite (pendiente migración de Prisma).")
            conn.close()
            return 0
            
        for ws in workspaces:
            name = ws.get("name")
            slug = ws.get("slug")
            temp = float(ws.get("temperature", 0.2))
            prompt = ws.get("system_prompt", "")
            model = ws.get("model", "qwen2.5:3b")
            
            cursor.execute("SELECT id FROM workspaces WHERE slug = ?", (slug,))
            row = cursor.fetchone()
            
            if row:
                cursor.execute("""
                    UPDATE workspaces 
                    SET name = ?, openAiTemp = ?, openAiPrompt = ?, chatProvider = 'generic-openai', chatModel = ?
                    WHERE slug = ?
                """, (name, temp, prompt, model, slug))
                print(f"  🔄 Workspace actualizado: {name} ({slug}) -> {model}")
            else:
                cursor.execute("""
                    INSERT INTO workspaces (name, slug, openAiTemp, openAiHistory, openAiPrompt, chatProvider, chatModel, chatMode, topN)
                    VALUES (?, ?, ?, 20, ?, 'generic-openai', ?, 'chat', 4)
                """, (name, slug, temp, prompt, model))
                print(f"  ✅ Workspace insertado: {name} ({slug}) -> {model}")
                
            sincronizados += 1
            
        conn.commit()
        conn.close()
        print(f"🎉 Sincronizados {sincronizados} workspaces en AnythingLLM SQLite.")
    except Exception as e:
        print(f"❌ Error al conectar con SQLite: {e}")
        
    return sincronizados


def vincular_flujo_documentos():
    """Asegura que los directorios de salida de Base estén conectados para ingesta RAG."""
    SALIDA_DOCUMENTOS.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    COLLECTOR_HOTDIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Directorios documentales vinculados:")
    print(f"   - Salida Base: {SALIDA_DOCUMENTOS}")
    print(f"   - Entregas Output: {OUTPUT_DIR}")
    print(f"   - Ingesta Collector: {COLLECTOR_HOTDIR}")


def main():
    print("=" * 60)
    print(" SINCRONIZADOR DE WORKSPACES Y DOCUMENTOS (BASE <-> ANYTHINGLLM)")
    print("=" * 60)
    
    vincular_flujo_documentos()
    
    workspaces = obtener_definiciones_workspaces()
    print(f"\n📋 Workspaces detectados ({len(workspaces)}):")
    for ws in workspaces:
        print(f"   • {ws.get('name')} [{ws.get('slug')}] -> Modelo: {ws.get('model')}")
        
    sincronizar_sqlite(workspaces)
    print("\n✅ Interconexión de workspaces completada.")

if __name__ == "__main__":
    main()
