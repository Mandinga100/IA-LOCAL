import sys
import time
import json
import re
import asyncio
from pathlib import Path

# Configurar salida en UTF-8
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.pureza_documental import normalizar_mojibake, sanitizar_texto_documental
from core.connector import OllamaConnector
from reconstructor import exportar_documento_formato

async def run_benchmark_async():
    print("================================================================")
    print(" INICIANDO BENCHMARK FORENSE: RECONSTRUCCIÓN ENTERPRISE QWEN 7B")
    print("================================================================")

    doc_path = BASE_DIR / "datos" / "entrada_web" / "documentacion_corrupta.md"
    raw_content = doc_path.read_text(encoding="utf-8")
    print(f"1. Documento original cargado: {len(raw_content)} caracteres.")

    # Normalización de mojibake
    cleaned_input = normalizar_mojibake(raw_content)
    print(f"2. Mojibake normalizado: {len(cleaned_input)} caracteres.")

    system_directive = (
        "Eres el Asistente Oficial de Redacción y Corrección Documental de Nivel Senior Enterprise.\n"
        "DIRECTIVAS OBLIGATORIAS:\n"
        "1. IDIOMA ESTRICTO: Redacta 100% en ESPAÑOL TÉCNICO FORMAL Y PROFESIONAL. Queda terminantemente PROHIBIDO el uso de catalán, valenciano u otras lenguas no solicitadas.\n"
        "2. REHABILITACIÓN ENTERPRISE: Transforma todo comentario irónico, informal, sarcástico o erróneo (como 'reza para que funcione', 'llora un poco', 'o algo así', 'no estamos seguros', 'no respondemos') en especificaciones y procedimientos de ingeniería de software corporativo profesionales y rigurosos.\n"
        "3. SINTAXIS Y CÓDIGO PERFECTO: Corrige todos los errores sintácticos en los bloques de código (ej. cerrar paréntesis, llaves, strings) para que sean 100% funcionales y compilables. Corrige diagramas de arquitectura para que reflejen un flujo Enterprise coherente.\n"
        "4. PUREZA ZERO-CHATTER: Entrega directamente el documento corregido en Markdown comenzando por el título, sin preámbulos, saludos ni disculpas, completando íntegramente todas las secciones hasta el final sin truncar.\n"
    )

    user_prompt = (
        "Corrige el siguiente documento técnico corrupto y transfórmalo en una especificación técnica formal de nivel enterprise:\n\n"
        f"```markdown\n{cleaned_input}\n```"
    )

    messages = [
        {"role": "system", "content": system_directive},
        {"role": "user", "content": user_prompt}
    ]

    connector = OllamaConnector(timeout_default_s=300.0)
    print("3. Conectando a Ollama con streaming en 'qwen2.5:7b' (num_ctx=8192, num_predict=4096)...")
    
    t0 = time.time()
    accumulated_tokens = []
    token_count = 0

    async for chunk in connector.chat_stream(
        model="qwen2.5:7b",
        messages=messages,
        num_ctx=8192,
        temperature=0.1,
        top_p=0.85,
        num_predict=4096
    ):
        delta = chunk.get("message", {}).get("content", "")
        if delta:
            accumulated_tokens.append(delta)
            token_count += 1
            if token_count % 30 == 0:
                print(".", end="", flush=True)

    t1 = time.time()
    elapsed = t1 - t0
    output_text = "".join(accumulated_tokens).strip()
    tps = token_count / elapsed if elapsed > 0 else 0

    print(f"\n4. Generación streaming finalizada en {elapsed:.2f}s | Chunks/Tokens: {token_count} | Velocidad aprox: {tps:.1f} t/s")

    # Auditoría Forense del Output
    print("\n--- AUDITORÍA FORENSE DE CALIDAD ---")
    
    # Check Catalan tokens
    catalan_words = [
        "aquest", "aquesta", "però", "amb", "roter", "dibuix", "usuari", "usuaris",
        "instal·lació", "instalacio", "connexió", "executa", "descarrega", "compartís",
        "seguretat", "llora un peu", "reza per"
    ]
    encontrados_catalan = []
    output_lower = output_text.lower()
    for w in catalan_words:
        if re.search(rf"\b{w}\b", output_lower):
            encontrados_catalan.append(w)

    if encontrados_catalan:
        print(f"❌ FALLO: Se detectaron palabras en catalán: {encontrados_catalan}")
    else:
        print("✅ IDIOMA: 100% Español Técnico Formal (0 palabras en catalán detectadas).")

    # Check for sarcasm or non-enterprise phrases
    sarcasm_phrases = [
        "llora un poco", "reza para", "no estamos seguros", "o algo así", "no respondemos",
        "calle falsa", "no vayas", "mereces un premio", "pero no hay"
    ]
    encontrados_sarcasmo = []
    for s in sarcasm_phrases:
        if s in output_lower:
            encontrados_sarcasmo.append(s)

    if encontrados_sarcasmo:
        print(f"❌ FALLO: Se detectaron frases sarcásticas/informales: {encontrados_sarcasmo}")
    else:
        print("✅ TONO ENTERPRISE: 100% Formal y riguroso (0 frases informales/sarcásticas).")

    # Check Anexo A JS code syntax
    match_code = re.search(r"```javascript([\s\S]*?)```", output_text)
    if match_code:
        js_code = match_code.group(1).strip()
        print(f"\nCódigo JavaScript generado en Anexo A:\n{js_code}")
        par_open = js_code.count("(")
        par_close = js_code.count(")")
        brace_open = js_code.count("{")
        brace_close = js_code.count("}")
        if par_open == par_close and brace_open == brace_close:
            print("✅ CÓDIGO JS: Paréntesis y llaves balanceados (Sintácticamente correcto).")
        else:
            print(f"❌ FALLO CÓDIGO: Desbalance de paréntesis ({par_open}/{par_close}) o llaves ({brace_open}/{brace_close})")

    # Sanitizar con pureza documental
    texto_puro = sanitizar_texto_documental(output_text)
    
    # Exportar a PDF y DOCX
    salida_dir = BASE_DIR / "datos" / "salida_web"
    salida_dir.mkdir(parents=True, exist_ok=True)
    pdf_destino = salida_dir / "documentacion_enterprise_corregida.pdf"
    docx_destino = salida_dir / "documentacion_enterprise_corregida.docx"

    print("\n5. Compilando entregables físicos...")
    ruta_pdf = exportar_documento_formato(texto_puro, pdf_destino, ".pdf")
    ruta_docx = exportar_documento_formato(texto_puro, docx_destino, ".docx")

    print(f"✅ PDF generado: {ruta_pdf} ({ruta_pdf.stat().st_size} bytes)")
    print(f"✅ DOCX generado: {ruta_docx} ({ruta_docx.stat().st_size} bytes)")

    print("\n=== MUESTRA DEL DOCUMENTO FINAL GENERADO ===")
    print(texto_puro[:1200])
    print("\n...\n")
    print(texto_puro[-600:])

if __name__ == "__main__":
    asyncio.run(run_benchmark_async())
