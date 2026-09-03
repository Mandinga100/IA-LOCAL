"""
servidor_api.py - API Gateway y servidor web local para la Plataforma IA Local.
Expone endpoints REST, telemetría GPU real, métricas de calidad y sirve frontend/index.html.
"""

import os
import shutil
import subprocess
import time
from contextlib import asynccontextmanager
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, HTMLResponse
from pydantic import BaseModel

from config import Config
from conversor import convertir_a_markdown, ConversionError
from corrector import CorrectorOllama, InferenciaError
from reconstructor import guardar_documento_corregido, ReconstruccionError
from explorador import validar_firma_segura, calcular_hash_sha256
from logs import logger

from core.connector import OllamaConnector
from core.registry import ModelRegistry
from core.profiles import PROFILES, ProfileType, resolver_perfil
from core.router import TaskRouter
from core.guardrails import separar_razonamiento_y_respuesta
from core.intent_detector import detectar_intencion_exportacion, ejecutar_exportacion_automatica

# Directorios base
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATOS_DIR = BASE_DIR / "datos"
UPLOAD_DIR = DATOS_DIR / "entrada_web"
SALIDA_DIR = DATOS_DIR / "salida_web"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SALIDA_DIR.mkdir(parents=True, exist_ok=True)

# Inicialización de componentes desacoplados del núcleo de 5 capas
connector = OllamaConnector()
registry = ModelRegistry(connector=connector, cache_path=DATOS_DIR / "registry_cache.json")
registry.load_cache()
router = TaskRouter(connector=connector, registry=registry)

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Refresca las capacidades del registro en segundo plano al arrancar."""
    try:
        await registry.refresh_models()
        logger.info(f"Registro de modelos inicializado: {len(registry.list_specs())} modelos en caché.")
    except Exception as e:
        logger.debug(f"Arranque sin conexión a Ollama (usando caché previa): {e}")
    yield

app = FastAPI(
    title="Plataforma IA Local API",
    description="Servidor API local con arquitectura de 5 capas, compatibilidad OpenAI y telemetría GPU.",
    version="0.4.0",
    lifespan=lifespan
)

# Habilitar CORS para localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_private_network_access_header(request, call_next):
    if request.method == "OPTIONS":
        from fastapi.responses import Response
        response = Response(status_code=200)
    else:
        response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    return response


# Buffer en memoria para eventos de seguridad, alertas térmicas y auditoría (FIFO 250 eventos)
from collections import deque
import psutil  # type: ignore[import-untyped]

_BUFFER_LOGS_SEGURIDAD: deque = deque(maxlen=250)
_LAST_NET_IO: Optional[Any] = None
_LAST_NET_TIME: Optional[float] = None
_MAX_TEMP_REGISTRADA: int = 0

def registrar_evento_seguridad(
    nivel: str,
    categoria: str,
    mensaje: str,
    detalles: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Registra un evento de seguridad o alerta en el buffer circular de auditoría."""
    evento = {
        "id": len(_BUFFER_LOGS_SEGURIDAD) + 1,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "nivel": nivel.upper(),
        "categoria": categoria.upper(),
        "mensaje": mensaje,
        "detalles": detalles or {}
    }
    _BUFFER_LOGS_SEGURIDAD.appendleft(evento)
    if nivel in ("WARN", "WARNING", "ERROR", "CRITICAL"):
        logger.warning(f"[AUDITORIA-SEGURIDAD] [{categoria}] {mensaje} - {detalles}")
    else:
        logger.info(f"[AUDITORIA-SEGURIDAD] [{categoria}] {mensaje}")
    return evento

# Inicializar eventos de arranque en el buffer de auditoría
registrar_evento_seguridad(
    "INFO", "SISTEMA", "Servidor API y Gateway inicializados correctamente",
    {"host": "0.0.0.0", "port": 8000, "modo": "offline_industrial"}
)
registrar_evento_seguridad(
    "INFO", "GOBERNANZA", "Reglas ECC de inmutabilidad criptográfica activas (SHA-256)",
    {"rutas_blindadas": ["/ECC", "ai-harness/ecc"], "permiso": "CEO_ONLY"}
)


def obtener_telemetria_gpu() -> Dict[str, Any]:
    """Consulta la telemetría real de la GPU mediante nvidia-smi de forma segura."""
    global _MAX_TEMP_REGISTRADA
    try:
        res = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw,clocks.gr,clocks.mem",
                "--format=csv,noheader,nounits"
            ],
            capture_output=True,
            text=True,
            timeout=1.0
        )
        if res.returncode == 0:
            partes = [p.strip() for p in res.stdout.strip().split(",")]
            if len(partes) >= 5:
                vram_usada = int(partes[1])
                vram_total = int(partes[2])
                vram_libre = vram_total - vram_usada
                gpu_util = int(partes[3])
                gpu_temp = int(partes[4])

                power_watts = float(partes[5]) if len(partes) > 5 and partes[5] != "[N/A]" else 0.0
                clock_gpu_mhz = int(partes[6]) if len(partes) > 6 and partes[6] != "[N/A]" else 0
                clock_mem_mhz = int(partes[7]) if len(partes) > 7 and partes[7] != "[N/A]" else 0

                if gpu_temp > _MAX_TEMP_REGISTRADA:
                    _MAX_TEMP_REGISTRADA = gpu_temp

                # Alertas proactivas de seguridad térmica y VRAM
                if gpu_temp >= 82:
                    registrar_evento_seguridad(
                        "CRITICAL", "GPU_TEMP",
                        f"¡ALERTA CRÍTICA TÉRMICA EN GPU! Temperatura alcanzó {gpu_temp}°C (Límite 82°C)",
                        {"temp_c": gpu_temp, "gpu_util": gpu_util, "vram_usada_mb": vram_usada}
                    )
                elif gpu_temp >= 75:
                    registrar_evento_seguridad(
                        "WARN", "GPU_TEMP",
                        f"Temperatura elevada en GPU: {gpu_temp}°C. Monitoreo preventivo activo.",
                        {"temp_c": gpu_temp, "gpu_util": gpu_util}
                    )

                if vram_libre < 250:
                    registrar_evento_seguridad(
                        "WARN", "VRAM",
                        f"Memoria VRAM crítica: solo {vram_libre} MB libres de {vram_total} MB",
                        {"vram_libre_mb": vram_libre, "vram_usada_mb": vram_usada}
                    )

                return {
                    "disponible": True,
                    "gpu_nombre": partes[0],
                    "vram_usada_mb": vram_usada,
                    "vram_total_mb": vram_total,
                    "vram_libre_mb": vram_libre,
                    "gpu_util_pct": gpu_util,
                    "gpu_temp_c": gpu_temp,
                    "power_watts": power_watts,
                    "clock_gpu_mhz": clock_gpu_mhz,
                    "clock_mem_mhz": clock_mem_mhz,
                    "max_temp_registrada_c": _MAX_TEMP_REGISTRADA
                }
    except Exception as e:
        logger.debug(f"Telemetría GPU no disponible: {e}")

    return {
        "disponible": False,
        "gpu_nombre": "CPU / GPU no detectada",
        "vram_usada_mb": 0,
        "vram_total_mb": 4096,
        "vram_libre_mb": 4096,
        "gpu_util_pct": 0,
        "gpu_temp_c": 0,
        "power_watts": 0.0,
        "clock_gpu_mhz": 0,
        "clock_mem_mhz": 0,
        "max_temp_registrada_c": _MAX_TEMP_REGISTRADA
    }


def obtener_telemetria_360() -> Dict[str, Any]:
    """Genera un snapshot completo 360° de GPU, CPU, RAM, Red I/O y Procesos de Máquina."""
    global _LAST_NET_IO, _LAST_NET_TIME

    # 1. GPU y Hardware
    gpu_data = obtener_telemetria_gpu()

    # 2. CPU y Memoria RAM (psutil)
    cpu_pct = psutil.cpu_percent(interval=None)
    cpu_cores_logical = psutil.cpu_count(logical=True) or 1
    cpu_cores_physical = psutil.cpu_count(logical=False) or 1
    ram = psutil.virtual_memory()

    # 3. Tráfico de Red & I/O
    ahora = time.time()
    net_io = psutil.net_io_counters()
    kbps_in = 0.0
    kbps_out = 0.0

    if _LAST_NET_IO and _LAST_NET_TIME and (ahora > _LAST_NET_TIME):
        delta_t = ahora - _LAST_NET_TIME
        bytes_recv_delta = max(0, net_io.bytes_recv - _LAST_NET_IO.bytes_recv)
        bytes_sent_delta = max(0, net_io.bytes_sent - _LAST_NET_IO.bytes_sent)
        kbps_in = round((bytes_recv_delta / 1024) / delta_t, 2)
        kbps_out = round((bytes_sent_delta / 1024) / delta_t, 2)

    _LAST_NET_IO = net_io
    _LAST_NET_TIME = ahora

    # 4. Procesos Activos Relevantes en la Máquina
    procesos_relevantes: List[Dict[str, Any]] = []
    PATRONES_PROCESOS = ("ollama", "python", "uvicorn", "docker", "containerd", "wsl", "anythingllm")

    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
            try:
                p_name = (proc.info['name'] or "").lower()
                if any(pat in p_name for pat in PATRONES_PROCESOS):
                    mem_mb = round(proc.info['memory_info'].rss / (1024 * 1024), 1)
                    procesos_relevantes.append({
                        "pid": proc.info['pid'],
                        "nombre": proc.info['name'],
                        "cpu_pct": proc.info['cpu_percent'] or 0.0,
                        "memoria_mb": mem_mb,
                        "estado": proc.info['status']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.debug(f"Error listando procesos: {e}")

    # Ordenar procesos por consumo de RAM descendente (top 15)
    procesos_relevantes.sort(key=lambda x: x["memoria_mb"], reverse=True)
    procesos_relevantes = procesos_relevantes[:15]

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gpu": gpu_data,
        "cpu": {
            "util_pct": cpu_pct,
            "nucleos_logicos": cpu_cores_logical,
            "nucleos_fisicos": cpu_cores_physical
        },
        "ram": {
            "total_mb": round(ram.total / (1024 * 1024), 1),
            "usada_mb": round(ram.used / (1024 * 1024), 1),
            "libre_mb": round(ram.available / (1024 * 1024), 1),
            "util_pct": ram.percent
        },
        "red": {
            "bytes_enviados_mb": round(net_io.bytes_sent / (1024 * 1024), 2),
            "bytes_recibidos_mb": round(net_io.bytes_recv / (1024 * 1024), 2),
            "throughput_in_kbps": kbps_in,
            "throughput_out_kbps": kbps_out,
            "paquetes_enviados": net_io.packets_sent,
            "paquetes_recibidos": net_io.packets_recv
        },
        "procesos": procesos_relevantes
    }


@app.get("/")
async def root() -> FileResponse:
    """Sirve la landing page / interfaz web principal."""
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Interfaz frontend no encontrada.")
    return FileResponse(str(index_path))

@app.get("/api/telemetria/360")
async def telemetria_360() -> JSONResponse:
    """Snapshot integral 360° de GPU, CPU, RAM, Red I/O y procesos activos del sistema."""
    return JSONResponse(content=obtener_telemetria_360())

@app.get("/api/seguridad/logs")
async def seguridad_logs() -> JSONResponse:
    """Retorna los eventos de auditoría y seguridad registrados en el buffer en memoria."""
    logs_lista = list(_BUFFER_LOGS_SEGURIDAD)
    alertas_criticas = sum(1 for l in logs_lista if l.get("nivel") == "CRITICAL")
    alertas_warnings = sum(1 for l in logs_lista if l.get("nivel") in ("WARN", "WARNING"))

    return JSONResponse(
        content={
            "total_eventos": len(logs_lista),
            "alertas_criticas": alertas_criticas,
            "alertas_advertencias": alertas_warnings,
            "max_temp_registrada_c": _MAX_TEMP_REGISTRADA,
            "eventos": logs_lista
        }
    )

@app.post("/api/seguridad/test-alerta")
async def emitir_alerta_prueba(
    categoria: str = Form("GPU_TEMP"),
    mensaje: str = Form("Prueba manual de disparo de alerta térmica"),
    nivel: str = Form("WARN")
) -> JSONResponse:
    """Endpoint administrativo para emitir eventos de prueba hacia el feed de seguridad."""
    evento = registrar_evento_seguridad(nivel, categoria, mensaje, {"simulado": True})
    return JSONResponse(content={"status": "ok", "evento": evento})

@app.get("/api/salud")
async def salud() -> JSONResponse:

    """Verifica la conectividad con Ollama, lista modelos, perfiles y telemetría de hardware."""
    url_ollama = "http://localhost:11434/api/tags"
    modelos: List[str] = []
    ollama_online = False

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url_ollama)
            if resp.status_code == 200:
                ollama_online = True
                data = resp.json()
                modelos = [m.get("name") for m in data.get("models", []) if m.get("name")]
    except Exception as e:
        logger.debug(f"Ollama no disponible en salud: {e}")

    gpu_info = obtener_telemetria_gpu()

    return JSONResponse(
        content={
            "estado": "online",
            "ollama": ollama_online,
            "modelos_disponibles": modelos,
            "perfiles_activos": [p.value for p in PROFILES.keys()],
            "modelo_ancla_residente": router.get_currently_resident_model(),
            "telemetria_gpu": gpu_info
        }
    )

@app.get("/api/telemetria")
async def telemetria() -> JSONResponse:
    """Retorna la telemetría en tiempo real de GPU y memoria."""
    return JSONResponse(content=obtener_telemetria_gpu())

@app.post("/api/procesar")
async def procesar_documento(
    archivo: UploadFile = File(...),
    tipo_documento: str = Form("general"),
    modelo: str = Form("qwen2.5:3b"),
    chunk_size: int = Form(1800),
    perfil: Optional[str] = Form(None)
) -> JSONResponse:
    """
    Recibe un archivo, extrae su contenido a Markdown, ejecuta la corrección
    con el modelo o perfil seleccionado, mide telemetría en alta resolución
    y reconstruye el formato de salida.
    """
    if not archivo.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")

    nombre_sanitizado = Path(archivo.filename).name
    ruta_guardado_upload = UPLOAD_DIR / nombre_sanitizado

    tiempo_inicio_total = time.perf_counter()

    try:
        # 1. Guardar archivo subido en disco
        with open(ruta_guardado_upload, "wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)

        # 2. Validación de seguridad (Magic Bytes / Firmas no ejecutables)
        if not validar_firma_segura(ruta_guardado_upload):
            ruta_guardado_upload.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail="El archivo fue rechazado por contener firmas ejecutables binarias no permitidas."
            )

        hash_original = calcular_hash_sha256(ruta_guardado_upload)

        # 3. Conversión a Markdown (Medición de tiempo)
        t_conv_start = time.perf_counter()
        markdown_original = convertir_a_markdown(ruta_guardado_upload)
        t_conv_ms = round((time.perf_counter() - t_conv_start) * 1000, 1)

        if not markdown_original.strip():
            raise HTTPException(
                status_code=422,
                detail="El archivo no contiene texto extraíble o es ilegible."
            )

        # 4. Inferencia con IA local (Medición de tiempo)
        t_inf_start = time.perf_counter()
        razonamiento_traza: Optional[str] = None
        modelo_ejecutado = modelo

        if perfil:
            decision = await router.execute_task(
                perfil_nombre=perfil,
                prompt=f"Corrige y optimiza el siguiente texto en Markdown preservando su formato y mejorando su calidad:\n\n{markdown_original}",
                longitud_original=len(markdown_original)
            )
            markdown_corregido = decision.texto_final
            razonamiento_traza = decision.razonamiento_traza
            modelo_ejecutado = decision.modelo_ejecutado
        else:
            config = Config(
                ruta_entrada=UPLOAD_DIR,
                ruta_salida=SALIDA_DIR,
                modelo=modelo,
                chunk_size=chunk_size
            )
            with CorrectorOllama(config) as corrector:
                markdown_corregido = corrector.corregir_texto(
                    markdown_original,
                    tipo_documento=tipo_documento
                )
        t_inf_ms = round((time.perf_counter() - t_inf_start) * 1000, 1)

        # 5. Reconstrucción y guardado del archivo corregido (Medición de tiempo)
        t_rec_start = time.perf_counter()
        ruta_destino_final = SALIDA_DIR / nombre_sanitizado
        archivo_generado = guardar_documento_corregido(
            texto_corregido=markdown_corregido,
            ruta_original=ruta_guardado_upload,
            ruta_destino=ruta_destino_final
        )
        t_rec_ms = round((time.perf_counter() - t_rec_start) * 1000, 1)

        tiempo_total_s = round(time.perf_counter() - tiempo_inicio_total, 2)
        hash_corregido = calcular_hash_sha256(archivo_generado)

        # Cálculo de métricas de calidad y esfuerzo local
        palabras_orig = len(markdown_original.split())
        palabras_corr = len(markdown_corregido.split())
        chars_orig = len(markdown_original)
        chars_corr = len(markdown_corregido)

        tokens_estimados = max(1, int(chars_corr / 3.8))
        tokens_por_segundo = round(tokens_estimados / (t_inf_ms / 1000), 1) if t_inf_ms > 0 else 0

        # Score estimado de calidad / preservación estructural (0 a 100)
        ratio_longitud = min(chars_corr, chars_orig) / max(chars_corr, chars_orig) if max(chars_corr, chars_orig) > 0 else 1.0
        score_calidad = round(min(100.0, ratio_longitud * 100.0), 1)

        gpu_telemetria = obtener_telemetria_gpu()

        return JSONResponse(
            content={
                "exito": True,
                "nombre_archivo": nombre_sanitizado,
                "archivo_descarga": archivo_generado.name,
                "extension": archivo_generado.suffix,
                "texto_original": markdown_original,
                "texto_corregido": markdown_corregido,
                "tamano_bytes": archivo_generado.stat().st_size,
                "telemetria": {
                    "tiempo_total_segundos": tiempo_total_s,
                    "tiempo_conversion_ms": t_conv_ms,
                    "tiempo_inferencia_ms": t_inf_ms,
                    "tiempo_reconstruccion_ms": t_rec_ms,
                    "tokens_estimados": tokens_estimados,
                    "tokens_por_segundo": tokens_por_segundo,
                    "modelo": modelo_ejecutado,
                    "perfil": perfil,
                    "razonamiento": razonamiento_traza,
                    "tipo_documento": tipo_documento,
                    "gpu": gpu_telemetria
                },
                "calidad": {
                    "palabras_original": palabras_orig,
                    "palabras_corregido": palabras_corr,
                    "caracteres_original": chars_orig,
                    "caracteres_corregido": chars_corr,
                    "delta_caracteres": chars_corr - chars_orig,
                    "score_calidad": score_calidad,
                    "hash_sha256_original": hash_original,
                    "hash_sha256_corregido": hash_corregido
                }
            }
        )

    except HTTPException:
        raise
    except (ConversionError, InferenciaError, ReconstruccionError) as err:
        logger.error(f"Fallo en pipeline web para {nombre_sanitizado}: {err}")
        raise HTTPException(status_code=500, detail=str(err))
    except Exception as e:
        logger.error(f"Error inesperado en procesar_documento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@app.get("/api/descargar/{nombre_archivo}")
async def descargar_documento(nombre_archivo: str) -> FileResponse:
    """Permite la descarga segura del documento reconstruido."""
    nombre_seguro = Path(urllib.parse.unquote(nombre_archivo)).name
    ruta_archivo = (SALIDA_DIR / nombre_seguro).resolve()

    # Si no existe en SALIDA_DIR (salida_web), buscar en datos/salida
    if not ruta_archivo.exists():
        ruta_alt = (DATOS_DIR / "salida" / nombre_seguro).resolve()
        if ruta_alt.exists() and ruta_alt.is_relative_to((DATOS_DIR / "salida").resolve()):
            ruta_archivo = ruta_alt

    if not ruta_archivo.exists():
        raise HTTPException(status_code=404, detail="El archivo solicitado no existe.")

    # Mapeo de MIME Types para visualización y descarga directa
    ext = ruta_archivo.suffix.lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".odt": "application/vnd.oasis.opendocument.text",
        ".rtf": "application/rtf",
        ".csv": "text/csv; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
        ".md": "text/markdown; charset=utf-8"
    }
    media_type = mime_map.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(ruta_archivo),
        filename=nombre_seguro,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{nombre_seguro}"'}
    )


@app.get("/api/ver/{nombre_archivo}", response_class=HTMLResponse)
async def previsualizar_documento(nombre_archivo: str) -> HTMLResponse:
    """
    Entrega una interfaz interactiva de previsualización para cualquier documento reconstruido,
    con visor incrustado para PDF, renderizado de Markdown, telemetría y botones de descarga directa.
    """
    nombre_seguro = Path(urllib.parse.unquote(nombre_archivo)).name
    ruta_archivo = (SALIDA_DIR / nombre_seguro).resolve()

    if not ruta_archivo.exists():
        ruta_alt = (DATOS_DIR / "salida" / nombre_seguro).resolve()
        if ruta_alt.exists() and ruta_alt.is_relative_to((DATOS_DIR / "salida").resolve()):
            ruta_archivo = ruta_alt

    if not ruta_archivo.exists():
        raise HTTPException(status_code=404, detail="El documento no existe para previsualización.")

    ext = ruta_archivo.suffix.lower()
    tamano_kb = round(ruta_archivo.stat().st_size / 1024, 1)
    url_descarga = f"/api/descargar/{urllib.parse.quote(nombre_seguro)}"

    # Contenido del visor según formato
    if ext == ".pdf":
        visor_html = f'''
        <div class="visor-container">
            <iframe src="{url_descarga}#toolbar=1" width="100%" height="800px" style="border: none; border-radius: 12px;"></iframe>
        </div>
        '''
    elif ext in [".md", ".txt", ".csv"]:
        try:
            with open(ruta_archivo, "r", encoding="utf-8", errors="replace") as f:
                contenido_raw = f.read()
            import html
            contenido_escapado = html.escape(contenido_raw)
            visor_html = f'''
            <div class="visor-container text-box">
                <pre style="white-space: pre-wrap; font-family: monospace; line-height: 1.5; color: #e2e8f0;">{contenido_escapado}</pre>
            </div>
            '''
        except Exception as e:
            visor_html = f'<p class="error">Error al leer contenido: {e}</p>'
    elif ext == ".html":
        visor_html = f'''
        <div class="visor-container">
            <iframe src="{url_descarga}" width="100%" height="800px" style="border: none; border-radius: 12px; background: white;"></iframe>
        </div>
        '''
    else:
        # Formatos ofimáticos binarios (DOCX, ODT, RTF): si existe .corregido.md o similar, mostrar texto
        ruta_md_aux = ruta_archivo.with_suffix(".corregido.md")
        preview_extra = ""
        if ruta_md_aux.exists():
            try:
                import html
                with open(ruta_md_aux, "r", encoding="utf-8", errors="replace") as f:
                    txt = html.escape(f.read())
                preview_extra = f'''
                <div class="visor-container text-box" style="margin-top: 20px;">
                    <h3 style="margin-bottom: 12px; color: #a5b4fc;">Transcripción Estructurada</h3>
                    <pre style="white-space: pre-wrap; font-family: monospace; color: #e2e8f0;">{txt}</pre>
                </div>
                '''
            except Exception:
                pass

        visor_html = f'''
        <div class="visor-container info-box" style="text-align: center; padding: 40px;">
            <div style="font-size: 48px; margin-bottom: 16px;">📄</div>
            <h2 style="font-family: Outfit, sans-serif; margin-bottom: 12px;">Documento Ofimático Reconstruido ({ext.upper()})</h2>
            <p style="color: #94a3b8; max-width: 500px; margin: 0 auto 24px;">
                Este archivo ha sido compilado en formato binario estructurado ({ext.upper()}).
                Puedes descargarlo para abrirlo directamente en Microsoft Word, LibreOffice o tu suite preferida.
            </p>
            <a href="{url_descarga}" class="btn-download" style="display: inline-flex; margin: 0 auto;">📥 Descargar {nombre_seguro}</a>
            {preview_extra}
        </div>
        '''

    pagina_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Previsualizador | {nombre_seguro}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: #070a13;
            color: #f8fafc;
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .header {{
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 16px 28px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .header-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .badge {{
            background: rgba(99, 102, 241, 0.2);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
            font-size: 12px;
            padding: 3px 8px;
            border-radius: 6px;
            font-family: monospace;
        }}
        .actions {{
            display: flex;
            gap: 12px;
        }}
        .btn-download {{
            background: #6366f1;
            color: white;
            text-decoration: none;
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
        }}
        .btn-download:hover {{
            background: #4f46e5;
            transform: translateY(-1px);
        }}
        .btn-secondary {{
            background: rgba(255, 255, 255, 0.06);
            color: #cbd5e1;
            text-decoration: none;
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.2s;
        }}
        .btn-secondary:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}
        .main-content {{
            flex: 1;
            max-width: 1280px;
            width: 100%;
            margin: 24px auto;
            padding: 0 20px;
        }}
        .visor-container {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }}
        .text-box {{
            padding: 24px;
            max-height: 800px;
            overflow-y: auto;
        }}
        .footer-bar {{
            padding: 16px;
            text-align: center;
            font-size: 13px;
            color: #64748b;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-title">
            <span>Plataforma IA Local</span>
            <span class="badge">{nombre_seguro}</span>
            <span style="font-size: 13px; color: #94a3b8;">({tamano_kb} KB)</span>
        </div>
        <div class="actions">
            <a href="/" class="btn-secondary">Volver al Panel</a>
            <a href="/api/abrir/{nombre_seguro}" class="btn-secondary" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border-color: rgba(16, 185, 129, 0.4);">⚡ Abrir en PC</a>
            <a href="{url_descarga}" class="btn-download">📥 Descargar {ext.upper()}</a>
        </div>
    </header>

    <main class="main-content">
        {visor_html}
    </main>

    <footer class="footer-bar">
        Plataforma IA Local &bull; Inferencia 100% Offline con Ollama &bull; Windows 10 64-bit
    </footer>
</body>
</html>'''
    return HTMLResponse(content=pagina_html)


@app.get("/api/asset/{doc_prefix}/{nombre_archivo}")
async def servir_asset_imagen(doc_prefix: str, nombre_archivo: str) -> FileResponse:
    """
    Sirve imágenes y activos gráficos extraídos con cabeceras CORS para AnythingLLM/Electron.
    """
    prefijo_limpio = re.sub(r'[^a-zA-Z0-9_\-]', '', doc_prefix)
    archivo_limpio = Path(urllib.parse.unquote(nombre_archivo)).name

    dir_assets = (DATOS_DIR / "assets").resolve()
    ruta_asset = (dir_assets / prefijo_limpio / archivo_limpio).resolve()

    if not ruta_asset.exists() or not ruta_asset.is_relative_to(dir_assets):
        ruta_alt = (SALIDA_DIR / "assets_surgery" / archivo_limpio).resolve()
        if ruta_alt.exists():
            ruta_asset = ruta_alt
        else:
            raise HTTPException(status_code=404, detail="El asset visual solicitado no existe.")

    ext = ruta_asset.suffix.lower()
    media_type = "image/png" if ext == ".png" else ("image/jpeg" if ext in (".jpg", ".jpeg") else "application/octet-stream")

    return FileResponse(
        path=str(ruta_asset),
        media_type=media_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=86400"
        }
    )


@app.get("/api/abrir/{nombre_archivo}")
async def abrir_documento_en_windows(nombre_archivo: str) -> JSONResponse:
    """
    Abre el archivo físico instantáneamente en la aplicación nativa de Windows 10
    (Word, Acrobat Reader, etc.) mediante os.startfile.
    Resuelve el problema de los metalinks en AnythingLLM Desktop.
    """
    nombre_seguro = Path(urllib.parse.unquote(nombre_archivo)).name
    ruta_archivo = (SALIDA_DIR / nombre_seguro).resolve()

    if not ruta_archivo.exists():
        ruta_alt = (DATOS_DIR / "salida" / nombre_seguro).resolve()
        if ruta_alt.exists() and ruta_alt.is_relative_to((DATOS_DIR / "salida").resolve()):
            ruta_archivo = ruta_alt

    if not ruta_archivo.exists():
        desktop = Path.home() / "Desktop" / nombre_seguro
        if desktop.exists():
            ruta_archivo = desktop

    if not ruta_archivo.exists():
        raise HTTPException(status_code=404, detail=f"No se encontró el archivo '{nombre_seguro}' para abrir.")

    try:
        import os
        os.startfile(str(ruta_archivo))
        logger.info(f"Archivo abierto en Windows 10 con os.startfile: {ruta_archivo}")
        return JSONResponse({
            "exito": True,
            "mensaje": f"Archivo '{nombre_seguro}' abierto con éxito en Windows.",
            "ruta": str(ruta_archivo)
        })
    except Exception as e:
        logger.error(f"Error al abrir archivo con os.startfile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"No se pudo abrir el archivo en Windows: {e}")


# ============================================================================
# ENDPOINTS DE ORQUESTACIÓN Y COMPATIBILIDAD OPENAI (/v1) PARA OPEN WEBUI
# ============================================================================

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "chat_ui"
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stream: bool = False
    max_tokens: Optional[int] = None

class OrquestarRequest(BaseModel):
    perfil: str = "doc_main"
    prompt: str
    system_override: Optional[str] = None


@app.get("/api/perfiles")
async def listar_perfiles() -> JSONResponse:
    """Retorna la matriz de perfiles operativos configurados y su estado."""
    datos_perfiles = {}
    for p_type, prof in PROFILES.items():
        datos_perfiles[p_type.value] = {
            "label": prof.label,
            "description": prof.description,
            "primary_model": prof.primary_model,
            "secondary_model": prof.secondary_model,
            "safe_fallback": prof.safe_fallback_model,
            "contexto_num_ctx": prof.num_ctx,
            "temperatura": prof.temperature,
            "cadena_completa": prof.get_effective_models()
        }
    return JSONResponse(content={"perfiles": datos_perfiles})


@app.post("/api/orquestar")
async def orquestar_tarea(req: OrquestarRequest) -> JSONResponse:
    """Ejecuta una tarea de texto directa gobernada por el TaskRouter y los guardrails."""
    try:
        decision = await router.execute_task(
            perfil_nombre=req.perfil,
            prompt=req.prompt,
            system_override=req.system_override
        )
        return JSONResponse(
            content={
                "exito": True,
                "perfil": decision.perfil_utilizado.value,
                "modelo_ejecutado": decision.modelo_ejecutado,
                "es_fallback": decision.es_fallback,
                "texto_final": decision.texto_final,
                "razonamiento": decision.razonamiento_traza,
                "tiempo_ms": decision.tiempo_total_ms,
                "reintentos": decision.reintentos_realizados,
                "auditoria": {
                    "es_valido": decision.auditoria.es_valido,
                    "score_calidad": decision.auditoria.score_calidad,
                    "errores": decision.auditoria.errores,
                    "advertencias": decision.auditoria.advertencias
                }
            }
        )
    except Exception as e:
        logger.error(f"Error en orquestar_tarea: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/models")
async def v1_models() -> JSONResponse:
    """
    Expone los perfiles lógicos y modelos locales como modelos compatibles con OpenAI.
    Permite a Open WebUI conectarse directamente y listar perfiles como modelos nativos.
    """
    now_ts = int(time.time())
    model_list = []

    # 1. Perfiles lógicos principales
    for p_type, prof in PROFILES.items():
        model_list.append({
            "id": p_type.value,
            "object": "model",
            "created": now_ts,
            "owned_by": "plataforma-ia-local",
            "permission": [],
            "root": p_type.value,
            "parent": None
        })

    # 2. Modelos físicos detectados en Ollama
    for spec in registry.list_specs():
        if spec.name not in [p.value for p in PROFILES.keys()]:
            model_list.append({
                "id": spec.name,
                "object": "model",
                "created": now_ts,
                "owned_by": "ollama-local",
                "permission": [],
                "root": spec.name,
                "parent": None
            })

    return JSONResponse(content={"object": "list", "data": model_list})


@app.post("/v1/chat/completions")
async def v1_chat_completions(req: ChatCompletionRequest):
    """
    Endpoint OpenAI-Compatible para Open WebUI y AnythingLLM.
    Mapea el modelo solicitado a un modelo instalado o perfil lógico, aplica enrutamiento y guardrails.
    """
    specs = registry.list_specs()
    installed_names = [s.name for s in specs]

    if req.model in installed_names:
        chosen_model = req.model
        profile = resolver_perfil(req.model)
    else:
        profile = resolver_perfil(req.model)
        chosen_model = router._select_best_available_model(profile, installed_names)

    messages_payload = [{"role": m.role, "content": m.content} for m in req.messages]
    chat_id = f"chatcmpl-{int(time.time() * 1000)}"
    created_ts = int(time.time())

    # Detección inteligente de intención de exportación física (.pdf, .docx, etc.)
    export_intent = detectar_intencion_exportacion(messages_payload)

    # Modo Streaming (SSE) para Open WebUI y AnythingLLM
    if req.stream:
        async def event_generator() -> AsyncGenerator[str, None]:
            accumulated_tokens = []
            try:
                async for chunk in connector.chat_stream(
                    model=chosen_model,
                    messages=messages_payload,
                    num_ctx=profile.num_ctx,
                    temperature=req.temperature if req.temperature is not None else profile.temperature,
                    top_p=req.top_p if req.top_p is not None else profile.top_p,
                    num_predict=req.max_tokens or profile.num_predict
                ):
                    delta_content = chunk.get("message", {}).get("content", "")
                    if delta_content:
                        accumulated_tokens.append(delta_content)
                        chunk_payload = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created_ts,
                            "model": req.model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": delta_content},
                                    "finish_reason": None
                                }
                            ]
                        }
                        yield f"data: {json.dumps(chunk_payload, ensure_ascii=False)}\n\n"

                # Si el usuario solicitó exportar o descargar el documento
                if export_intent and export_intent.es_exportacion:
                    texto_generado = "".join(accumulated_tokens).strip()
                    texto_exportar = texto_generado

                    # Si el LLM generó poco texto y tenemos la ruta fuente en disco, usamos el contenido original
                    if len(texto_generado.split()) < 35 and export_intent.ruta_fuente and export_intent.ruta_fuente.exists():
                        try:
                            texto_exportar = convertir_a_markdown(export_intent.ruta_fuente)
                        except Exception as e_conv:
                            logger.debug(f"Conversión fallback de archivo fuente falló: {e_conv}")

                    if texto_exportar:
                        try:
                            res_exp = ejecutar_exportacion_automatica(
                                intent=export_intent,
                                texto_markdown=texto_exportar,
                                salida_dir=SALIDA_DIR
                            )
                            bloque_extra = res_exp.get("bloque_markdown", "")
                            if bloque_extra:
                                chunk_bloque = {
                                    "id": chat_id,
                                    "object": "chat.completion.chunk",
                                    "created": created_ts,
                                    "model": req.model,
                                    "choices": [
                                        {
                                            "index": 0,
                                            "delta": {"content": bloque_extra},
                                            "finish_reason": None
                                        }
                                    ]
                                }
                                yield f"data: {json.dumps(chunk_bloque, ensure_ascii=False)}\n\n"
                        except Exception as err_exp:
                            logger.error(f"Fallo en exportación automática stream: {err_exp}")

                # Chunk final de finalización
                final_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": req.model,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                }
                yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as err:
                logger.error(f"Error en stream v1_chat_completions: {err}")
                err_chunk = {
                    "error": {"message": f"Fallo en generación: {err}", "type": "server_error"}
                }
                yield f"data: {json.dumps(err_chunk)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # Modo Batch / No-Streaming
    try:
        resp = await connector.chat(
            model=chosen_model,
            messages=messages_payload,
            num_ctx=profile.num_ctx,
            temperature=req.temperature if req.temperature is not None else profile.temperature,
            top_p=req.top_p if req.top_p is not None else profile.top_p,
            num_predict=req.max_tokens or profile.num_predict
        )
        content_raw = resp.get("message", {}).get("content", "")
        razonamiento, content_limpio = separar_razonamiento_y_respuesta(content_raw)

        # Si el usuario o UI quiere ver el razonamiento (ej: DeepSeek-R1), lo preservamos
        final_content = content_limpio
        if razonamiento and "r1" in chosen_model.lower():
            final_content = f"<think>\n{razonamiento}\n</think>\n{content_limpio}"

        # Exportación automática en modo batch si se detectó intención
        if export_intent and export_intent.es_exportacion:
            texto_exportar = content_limpio.strip()
            if len(texto_exportar.split()) < 35 and export_intent.ruta_fuente and export_intent.ruta_fuente.exists():
                try:
                    texto_exportar = convertir_a_markdown(export_intent.ruta_fuente)
                except Exception as e_conv:
                    logger.debug(f"Conversión fallback batch falló: {e_conv}")

            if texto_exportar:
                try:
                    res_exp = ejecutar_exportacion_automatica(
                        intent=export_intent,
                        texto_markdown=texto_exportar,
                        salida_dir=SALIDA_DIR
                    )
                    final_content += res_exp.get("bloque_markdown", "")
                except Exception as err_exp:
                    logger.error(f"Fallo en exportación automática batch: {err_exp}")

        prompt_eval_count = resp.get("prompt_eval_count", 0)
        eval_count = resp.get("eval_count", 0)

        return JSONResponse(
            content={
                "id": chat_id,
                "object": "chat.completion",
                "created": created_ts,
                "model": req.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": final_content
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_eval_count,
                    "completion_tokens": eval_count,
                    "total_tokens": prompt_eval_count + eval_count
                }
            }
        )
    except Exception as e:
        logger.error(f"Error en v1_chat_completions no-stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def iniciar_servidor(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Inicia el servidor Uvicorn en todas las interfaces de red (0.0.0.0)."""
    logger.info(f"Iniciando servidor web en http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    iniciar_servidor()

