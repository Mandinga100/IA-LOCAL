import sys
from pathlib import Path

# Set UTF-8 encoding for standard output
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pureza_documental import normalizar_mojibake

file_path = Path(r"c:\Users\mandi\Documents\Proyectos\Plataforma IA local\AnythingLLM\Base\datos\entrada_web\documentacion_corrupta.md")
content = file_path.read_text(encoding="utf-8")
cleaned = normalizar_mojibake(content)

print("=== CLEANED TEXT PREVIEW ===")
print(cleaned[:800])
print("\n=== CHECKING SPECIFIC SECTIONS ===")
for line in cleaned.splitlines():
    if any(k in line.lower() for k in ["caracter", "autentica", "guia", "instal", "modulo", "anexo", "ultima"]):
        print("MATCH:", line)
