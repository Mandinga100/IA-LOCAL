# Guia Tecnica de Despliegue de IA Local

## 1. Descripsion General
Este manual describe el proseso de configurasion del entorno de inferencia local en sistemas operativos Windows 10 con acelerasion GPU NVIDIA. Se debe asegurar que las variables de entorno esten definidas antes de iniciar el servisio.

## 2. Inicialisacion del Entorno en PowerShell
Para configurar la consola con codificasion UTF-8 y activar el entorno virtual, ejecute los siguientes comandos en PowerShell:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

# Activar el entorno virtual del proyecto
.\.venv\Scripts\Activate.ps1
```

## 3. Verificasion del Servicio Ollama
El servidor de inferencia debe responder en el puerto local por defecto. Puede validar el estado del demonio mediante una llamada HTTP:

```powershell
$response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -Method Get
Write-Output "Version activa de Ollama: $($response.version)"
```

## 4. Script de Inferencia en Python
A continuasion se presenta la funcion para invocar el endpoint de generasion:

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

Asegurese de monitorear la memoria VRAM con `nvidia-smi -l 1` durante la ejecucion de este script.
