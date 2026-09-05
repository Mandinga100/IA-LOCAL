"""
deploy_anythingllm_fcg_skill.py
Despliega el plugin nativo 'fcg-ppt' para AnythingLLM (Servidor y Desktop).
Crea la estructura requerida por ImportedPlugin:
- plugin.json (schema: skill-1.0.0, hubId: fcg-ppt)
- handler.js (runtime con aibitat y requestToolApproval)
- fcg_generator.py (CLI puente para python-pptx)
- assets/template_fcg.pptx
- scripts/fcg_helpers.py
"""

import os
import shutil
import json
from pathlib import Path

# Definir rutas destino
server_storage = Path(r"c:\Users\mandi\Documents\Proyectos\Plataforma IA local\AnythingLLM\server\storage\plugins\agent-skills\fcg-ppt")
appdata = os.environ.get("APPDATA", r"C:\Users\mandi\AppData\Roaming")
desktop_storage = Path(appdata) / "anythingllm-desktop" / "storage" / "plugins" / "agent-skills" / "fcg-ppt"

targets = [server_storage, desktop_storage]

# 1. Manifest plugin.json
PLUGIN_JSON = {
    "$schema": "https://raw.githubusercontent.com/Mintplex-Labs/anything-llm/refs/heads/master/server/utils/agents/imported-manifest.schema.json",
    "active": True,
    "hubId": "fcg-ppt",
    "name": "Generador PPT Faro Consulting",
    "schema": "skill-1.0.0",
    "version": "1.0.0",
    "description": "Genera presentaciones PowerPoint (.pptx) ejecutivas 16:9 con branding oficial, paleta de colores y componentes visuales de Faro Consulting Group.",
    "author": "Faro Consulting Group",
    "author_url": "https://faroconsulting.com",
    "license": "MIT",
    "setup_args": {
        "OUTPUT_DIR": {
            "type": "string",
            "required": False,
            "default": r"c:\Users\mandi\Documents\Proyectos\Plataforma IA local\AnythingLLM\Base\datos\salida_web",
            "value": r"c:\Users\mandi\Documents\Proyectos\Plataforma IA local\AnythingLLM\Base\datos\salida_web",
            "input": {
                "type": "text",
                "default": r"c:\Users\mandi\Documents\Proyectos\Plataforma IA local\AnythingLLM\Base\datos\salida_web",
                "placeholder": "Ruta de salida de presentaciones",
                "hint": "Carpeta destino donde se guardan las presentaciones .pptx generadas"
            }
        }
    },
    "examples": [
        {
            "prompt": "Genera una presentación ejecutiva con formato Faro sobre la auditoría de contratos",
            "call": "{\"title\": \"Auditoría Comparativa de Contratos v1 y v2\", \"subtitle\": \"Análisis Forense de Cláusulas y Riesgo Operativo\", \"category\": \"AUDITORÍA\", \"client\": \"Dirección General\", \"action\": \"generate_deck\"}"
        },
        {
            "prompt": "Crea una presentación PPTX Faro para la estrategia de IA local",
            "call": "{\"title\": \"Estrategia de Transformación Digital & IA 2026\", \"subtitle\": \"Implementación de Arquitectura Soberana\", \"category\": \"ESTRATEGIA\", \"client\": \"Comité Directivo\", \"action\": \"generate_deck\"}"
        }
    ],
    "entrypoint": {
        "file": "handler.js",
        "params": {
            "title": {
                "description": "Título principal de la portada de la presentación",
                "type": "string"
            },
            "subtitle": {
                "description": "Subtítulo explicativo o enfoque estratégico de la presentación",
                "type": "string"
            },
            "category": {
                "description": "Categoría superior o tag de navegación institucional (ej: ESTRATEGIA, AUDITORÍA, FINANZAS)",
                "type": "string"
            },
            "client": {
                "description": "Nombre del cliente, comité o área destinataria",
                "type": "string"
            },
            "summary": {
                "description": "Puntos clave o resumen ejecutivo para distribuir en las tarjetas de contenido",
                "type": "string"
            },
            "action": {
                "description": "Acción a ejecutar: 'generate_deck' para mazo directivo completo de 6 diapositivas",
                "type": "string"
            }
        }
    },
    "imported": True
}

# 2. Handler Node.js
HANDLER_JS = r'''const { execFile } = require("child_process");
const path = require("path");
const fs = require("fs");

module.exports.runtime = {
  handler: async function ({
    title = "Presentación Ejecutiva Faro Consulting Group",
    subtitle = "Consultoría Estratégica & Análisis Integral",
    category = "ESTRATEGIA & DIRECCIÓN",
    client = "Dirección General",
    summary = "",
    action = "generate_deck"
  }) {
    const callerId = `${this.config?.name || "Generador PPT Faro"} v${this.config?.version || "1.0.0"}`;
    try {
      this.introspect(`[${callerId}] Iniciando generación de presentación ejecutiva: '${title}'`);
      
      const defaultOutputDir = path.resolve(process.env.STORAGE_DIR || path.resolve(__dirname, "../../../storage"), "documents");
      const outputDir = this.runtimeArgs?.["OUTPUT_DIR"] || defaultOutputDir;
      
      if (!fs.existsSync(outputDir)) {
        try {
          fs.mkdirSync(outputDir, { recursive: true });
        } catch (_) {}
      }

      this.logger(`[FCG-LOG] Directorio destino para archivos .pptx: ${outputDir}`);

      // Comprobar si requiere confirmación interactiva
      if (typeof this.requestToolApproval === "function") {
        this.introspect(`[${callerId}] Solicitando aprobación del usuario para generar presentación...`);
        const approval = await this.requestToolApproval({
          payload: { title, client, category, action },
          description: `[FARO CONSULTING GROUP] ¿Autoriza la generación del mazo de diapositivas 16:9 con título: "${title}" para el cliente "${client}"?`
        });

        if (!approval.approved) {
          this.introspect(`[${callerId}] Generación cancelada por directiva del usuario.`);
          return JSON.stringify({
            status: "rejected",
            authorized: false,
            message: approval.message || "Operación cancelada por el usuario.",
            title
          });
        }
      }

      // Resolver intérprete Python y script generador
      const pythonCandidates = [
        "c:\\Users\\mandi\\Documents\\Proyectos\\Plataforma IA local\\AnythingLLM\\Base\\.venv\\Scripts\\python.exe",
        "python",
        "python3"
      ];
      
      let pythonExe = "python";
      for (const p of pythonCandidates) {
        if (p.includes("\\") && fs.existsSync(p)) {
          pythonExe = p;
          break;
        }
      }

      const generatorScript = path.resolve(__dirname, "fcg_generator.py");

      const payload = {
        title,
        subtitle,
        category,
        client,
        summary,
        action,
        output_dir: outputDir
      };

      const payloadJson = JSON.stringify(payload);
      this.introspect(`[${callerId}] Generando mazo 16:9 con formato corporativo FaroCG...`);

      const result = await new Promise((resolve, reject) => {
        execFile(
          pythonExe, 
          [generatorScript, "--json", payloadJson], 
          { encoding: "utf8", windowsHide: true }, 
          (error, stdout, stderr) => {
            if (error) {
              return reject(new Error(stderr || error.message));
            }
            try {
              const lines = stdout.trim().split("\n");
              const jsonLine = lines.reverse().find(l => l.trim().startsWith("{"));
              if (!jsonLine) {
                return resolve({ status: "success", raw_output: stdout });
              }
              resolve(JSON.parse(jsonLine.trim()));
            } catch (e) {
              resolve({ status: "success", raw_output: stdout });
            }
          }
        );
      });

      this.introspect(`[${callerId}] Presentación guardada exitosamente en: ${result.filepath || result.filename}`);
      return JSON.stringify(result);
    } catch (e) {
      this.logger(`[FCG-ERROR] Error en ${callerId}:`, e.message);
      this.introspect(`[${callerId}] Falló la generación: ${e.message}`);
      return JSON.stringify({
        status: "error",
        error: e.message
      });
    }
  }
};
'''

# Archivos origen para copiar
source_root = Path(r"c:\Users\mandi\Documents\Proyectos\Plataforma IA local")
src_template = source_root / ".agents" / "skills" / "fcg-ppt" / "assets" / "template_fcg.pptx"
src_helpers = source_root / ".agents" / "skills" / "fcg-ppt" / "scripts" / "fcg_helpers.py"
src_generator = source_root / "tools" / "fcg_generator.py"

for target_dir in targets:
    print(f"\n--- Desplegando en AnythingLLM: {target_dir} ---")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Subcarpetas
    assets_dir = target_dir / "assets"
    scripts_dir = target_dir / "scripts"
    assets_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. plugin.json
    with open(target_dir / "plugin.json", "w", encoding="utf-8") as f:
        json.dump(PLUGIN_JSON, f, indent=2, ensure_ascii=False)
    print(" -> plugin.json escrito.")
    
    # 2. handler.js
    with open(target_dir / "handler.js", "w", encoding="utf-8") as f:
        f.write(HANDLER_JS)
    print(" -> handler.js escrito.")
    
    # 3. fcg_generator.py
    if src_generator.exists():
        shutil.copy2(src_generator, target_dir / "fcg_generator.py")
        print(" -> fcg_generator.py copiado.")
        
    # 4. assets/template_fcg.pptx
    if src_template.exists():
        shutil.copy2(src_template, assets_dir / "template_fcg.pptx")
        print(" -> template_fcg.pptx copiado.")
        
    # 5. scripts/fcg_helpers.py
    if src_helpers.exists():
        shutil.copy2(src_helpers, scripts_dir / "fcg_helpers.py")
        shutil.copy2(src_helpers, target_dir / "fcg_helpers.py") # También en raíz para acceso directo
        print(" -> fcg_helpers.py copiado en scripts/ y raíz.")

print("\n[OK] Despliegue de 'fcg-ppt' en AnythingLLM finalizado con éxito.")
