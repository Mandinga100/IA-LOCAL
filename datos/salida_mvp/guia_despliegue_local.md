# Guía Técnica de Despliegue de IA Local

## 1. Descripción General
Este manual describe el proceso de configuración del entorno de inferencia local en sistemas operativos Windows 10 con aceleración GPU NVIDIA. Se debe asegurar que las variables de entorno estén definidas antes de iniciar el servicio.

## 2. Inicialización del Entorno en PowerShell
Para configurar la consola con codificación UTF-8 y activar el entorno virtual, ejecute los siguientes comandos en PowerShell:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

# Activar el entorno virtual del proyecto
.\.venv\Scripts\Activate.ps1
```

## 3. Verificación del Servicio Ollama
El servidor de inferencia debe responder en el puerto local por defecto. Puede validar el estado del demonio mediante una llamada HTTP:

```powershell
$response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -Method Get
Write-Output "Versión activa de Ollama: $($response.version)"
```

## 4. Script de Inferencia en Python
A continuación se presenta la función para invocar el endpoint de generación:

```python
import httpx

def consultar_modelo(prompt: str, modelo: str = "qwen2.5:3b") -> str:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": modelo,
        "prompt": prompt,
        "stream": False
    }
    with httpx.Client(timeout=60.0) as client:
        res = client.post(url, json=payload)
        res.raise_for_status()
        return res.json().get("response", "")
```

Asegúrese de monitorear la memoria VRAM con `nvidia-smi -l 1` durante la ejecución de este script.