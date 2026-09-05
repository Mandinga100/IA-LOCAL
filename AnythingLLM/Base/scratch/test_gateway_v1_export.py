import json
import httpx
import sys

sys.stdout.reconfigure(encoding="utf-8")

url = "http://127.0.0.1:8000/v1/chat/completions"

# Test request simulating AnythingLLM attached document
payload = {
    "model": "qwen2.5:3b", # Intentionally requesting 3b to test automatic enterprise escalation to 7b
    "messages": [
        {
            "role": "user",
            "content": (
                "Context: [CONTEXT 0] (source: localfile://c:/docs/prueba_calidad.pdf)\n"
                "# DOcumEntaciÃ³n TÃ©cNica\n"
                "guÃ¬a tÃ©cniCa para SaaS multi-tenant.\n"
                "### CaracTERÃ¬sticas prinCIPALES:\n"
                "- Soporte multi-tenant (pero a veces no funciona)\n"
                "- AutenticaciÃ³n vÃ¬a JWT (a veces caduca)\n"
                "### InstAlaciÃ³n:\n"
                "1. Ejecuta `npm instal` (sÃ¬, con una 'l')\n"
                "2. Corre `npm run dev` (y reza para que funcione)\n"
                "### Anexo CÃ³digo:\n"
                "```javascript\n"
                "function saludar() {\n"
                "  console.log(\"Hola, mundo!\" // falta parentesis\n"
                "  return true;\n"
                "}\n"
                "```\n\n"
                "corrige el documento que te adjunte y devuelvemelo en formato .pdf descargable"
            )
        }
    ],
    "stream": False
}

print("Enviando petición a http://127.0.0.1:8000/v1/chat/completions...")
with httpx.Client(timeout=180.0) as client:
    resp = client.post(url, json=payload)
    print(f"Status Code: {resp.status_code}")
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    print("\n=== RESPUESTA RECIBIDA (PRIMEROS 600 CARACTERES) ===")
    print(content[:600])
    print("\n=== FINAL DE RESPUESTA (ENLACES DE DESCARGA / PREVIEW) ===")
    print(content[-600:])
