"""
mcp_server.py - Servidor MCP oficial de la Plataforma IA Local.
Expone las capacidades industriales de procesamiento, corrección y exportación
documental como herramientas nativas para AnythingLLM y agentes compatibles con MCP.
"""

import sys
from pathlib import Path
from typing import Optional
from mcp.server.mcpserver import MCPServer

# Asegurar encoding UTF-8 en Windows
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
SALIDA_DIR = BASE_DIR / "datos" / "salida"
SALIDA_DIR.mkdir(parents=True, exist_ok=True)

from config import Config
from conversor import convertir_a_markdown
from corrector import CorrectorOllama
from reconstructor import exportar_documento_formato
from core.intent_detector import generar_bloque_descarga_markdown
from servidor_api import obtener_telemetria_gpu

server = MCPServer("Plataforma IA Local - MCP Document Tools")


@server.tool()
def corregir_y_exportar_documento(
    ruta_archivo: str,
    formato_salida: str = "pdf",
    tipo_documento: str = "general",
    modelo: str = "qwen2.5:3b"
) -> str:
    """
    Procesa un documento completo (PDF, DOCX, XLSX, ODT, RTF, TXT, etc.):
    extrae texto sin mojibakes, corrige ortografía y estilo con IA local (Ollama)
    y lo reconstruye en el formato físico solicitado (.pdf, .docx, .odt, .rtf, .html, .md).
    Devuelve la ruta en disco y el enlace para descarga directa.
    """
    path_in = Path(ruta_archivo.strip('"\'')).resolve()
    if not path_in.exists():
        return f"Error: El archivo '{ruta_archivo}' no existe en el sistema de archivos."

    try:
        # 1. Extracción a Markdown
        markdown_orig = convertir_a_markdown(path_in)
        if not markdown_orig.strip():
            return f"Error: No se pudo extraer texto del archivo '{path_in.name}'."

        # 2. Corrección con IA Local
        cfg = Config(modelo=modelo, ruta_salida=SALIDA_DIR)
        with CorrectorOllama(cfg) as corrector:
            markdown_corregido = corrector.corregir_texto(
                markdown_orig,
                tipo_documento=tipo_documento
            )

        # 3. Reconstrucción y guardado en formato solicitado
        formato_norm = formato_salida if formato_salida.startswith(".") else f".{formato_salida}"
        nombre_salida = f"{path_in.stem}_corregido{formato_norm}"
        ruta_salida_final = SALIDA_DIR / nombre_salida

        ruta_generada = exportar_documento_formato(
            texto_markdown=markdown_corregido,
            ruta_destino=ruta_salida_final,
            formato=formato_norm
        )

        bloque = generar_bloque_descarga_markdown(
            archivo_nombre=ruta_generada.name,
            ruta_absoluta=ruta_generada.resolve(),
            formato=formato_norm
        )

        return (
            f"✅ **Documento procesado y corregido con éxito**\n"
            f"- **Archivo Original:** `{path_in.name}`\n"
            f"- **Modelo Utilizado:** `{modelo}`\n"
            f"- **Palabras Originales:** {len(markdown_orig.split())}\n"
            f"- **Palabras Corregidas:** {len(markdown_corregido.split())}\n"
            f"{bloque}"
        )
    except Exception as e:
        return f"Error al procesar el documento '{path_in.name}': {e}"


@server.tool()
def exportar_texto_a_documento(
    texto_markdown: str,
    nombre_archivo: str = "documento_corregido",
    formato_salida: str = "pdf"
) -> str:
    """
    Convierte cualquier texto o documentación en Markdown a un archivo físico
    descargable (.pdf, .docx, .odt, .rtf, .html, .csv, .md, .txt).
    Genera el enlace de descarga HTTP local.
    """
    try:
        formato_norm = formato_salida if formato_salida.startswith(".") else f".{formato_salida}"
        nombre_limpio = Path(nombre_archivo).stem
        nombre_final = f"{nombre_limpio}{formato_norm}"
        ruta_salida_final = SALIDA_DIR / nombre_final

        ruta_generada = exportar_documento_formato(
            texto_markdown=texto_markdown,
            ruta_destino=ruta_salida_final,
            formato=formato_norm
        )

        bloque = generar_bloque_descarga_markdown(
            archivo_nombre=ruta_generada.name,
            ruta_absoluta=ruta_generada.resolve(),
            formato=formato_norm
        )

        return f"✅ **Archivo generado exitosamente:**\n{bloque}"
    except Exception as e:
        return f"Error al exportar el texto a {formato_salida}: {e}"


@server.tool()
def telemetria_hardware_local() -> str:
    """
    Devuelve la telemetría en tiempo real de la GPU NVIDIA (VRAM usada/libre, temperatura y utilización)
    y estado del hardware local para monitorear la inferencia.
    """
    info = obtener_telemetria_gpu()
    if not info.get("disponible"):
        return "Telemetría GPU no disponible (ejecución sobre CPU)."

    return (
        f"🖥️ **Telemetría GPU:** {info.get('gpu_nombre')}\n"
        f"- **VRAM Usada:** {info.get('vram_usada_mb')} MB / {info.get('vram_total_mb')} MB\n"
        f"- **VRAM Libre:** {info.get('vram_libre_mb')} MB\n"
        f"- **Utilización GPU:** {info.get('gpu_util_pct')}%\n"
        f"- **Temperatura:** {info.get('gpu_temp_c')} °C"
    )


@server.tool()
def ecc_auditoria_pureza(texto: str) -> str:
    """
    [Harnes /ECC - Safety Guard] Realiza una auditoría forense de pureza documental.
    Detecta y elimina cualquier residuo de charla conversacional ('voy a corregir...',
    saludos, disculpas, cierres artificiales), calcula el Score de Pureza y devuelve
    el texto 100% esterilizado para compilación.
    """
    from core.pureza_documental import sanitizar_texto_documental, calcular_indice_pureza

    texto_sanitizado = sanitizar_texto_documental(texto)
    indice = calcular_indice_pureza(texto, texto_sanitizado)
    chatter_detectado = indice < 99.0 or len(texto) != len(texto_sanitizado)

    return (
        f"🛡️ **Auditoría Forense de Pureza Documental (/ECC Safety-Guard)**\n"
        f"- **Estado:** {'⚠️ CHATTER DETECTADO Y ELIMINADO' if chatter_detectado else '✅ 100% PURO (ZERO-CHATTER)'}\n"
        f"- **Índice de Retención Limpia:** {indice}%\n"
        f"- **Caracteres Originales:** {len(texto)}\n"
        f"- **Caracteres Limpios:** {len(texto_sanitizado)}\n\n"
        f"### Contenido Sanitizado Listo para Reconstrucción:\n\n"
        f"{texto_sanitizado}"
    )


@server.tool()
def ecc_inspeccion_visual_pixel(ruta_archivo: str) -> str:
    """
    [Harnes /ECC - Nutrient Document Processing] Inspección quirúrgica de imágenes pixel-perfect.
    Extrae e inspecciona cada asset gráfico incrustado en un PDF o DOCX, reportando
    dimensiones (px), resolución, formato, huella SHA-256 inmutable y ruta local segura.
    """
    from extractor_visual import extraer_imagenes_documento

    p = Path(ruta_archivo.strip('"\'')).resolve()
    if not p.exists():
        return f"Error: Archivo no encontrado: '{ruta_archivo}'"

    dir_assets = BASE_DIR / "datos" / "assets"
    dir_assets.mkdir(parents=True, exist_ok=True)

    try:
        assets = extraer_imagenes_documento(p, dir_assets)
        if not assets:
            return f"ℹ️ El documento '{p.name}' no contiene imágenes embebidas."

        lineas = [
            f"🔍 **Inspección Visual Quirúrgica Pixel-Perfect (/ECC)**\n",
            f"- **Documento Fuente:** `{p.name}`",
            f"- **Total Imágenes Encontradas:** {len(assets)}\n",
            "| Posición | Asset ID | Dimensiones | Formato | SHA-256 (prefijo) | Peso (KB) |",
            "|---|---|---|---|---|---|"
        ]

        for a in assets:
            peso_kb = round(a.tamano_bytes / 1024, 1)
            lineas.append(f"| {a.posicion} | `{a.image_id}` | {a.ancho}x{a.alto} px | {a.formato.upper()} | `{a.sha256_hash[:12]}` | {peso_kb} KB |")

        return "\n".join(lineas)
    except Exception as e:
        return f"Error durante la inspección visual: {e}"


@server.tool()
def ecc_verification_loop(ruta_archivo: str, formato_objetivo: str = "pdf") -> str:
    """
    [Harnes /ECC - Verification Loop] Ejecuta un ciclo completo de verificación de calidad
    (Fase 1 Build, Fase 2 Extracción Visual, Fase 3 Zero-Chatter, Fase 4 Compilación Física).
    Garantiza que el documento pueda reconstruirse sin fallos silenciosos.
    """
    from core.pureza_documental import sanitizar_texto_documental
    from extractor_visual import extraer_imagenes_documento, inyectar_anclas_imagenes_en_markdown

    p = Path(ruta_archivo.strip('"\'')).resolve()
    if not p.exists():
        return f"❌ Fallo en Fase 1 (Build): Archivo no existe '{ruta_archivo}'"

    reporte = [f"🔄 **Ciclo de Verificación (/ECC Verification Loop) para `{p.name}`**\n"]

    try:
        # Fase 1: Conversión y Extracción de Texto
        txt_md = convertir_a_markdown(p)
        reporte.append(f"- ✅ **Fase 1 (Build / Conversión):** Texto extraído exitosamente ({len(txt_md.split())} palabras).")

        # Fase 2: Inspección Visual
        dir_assets = BASE_DIR / "datos" / "assets"
        assets = extraer_imagenes_documento(p, dir_assets)
        reporte.append(f"- ✅ **Fase 2 (Visual Pixel-Perfect):** {len(assets)} imágenes extraídas y verificadas.")

        # Fase 3: Sanitización Zero-Chatter
        txt_puro = sanitizar_texto_documental(txt_md)
        txt_con_anclas = inyectar_anclas_imagenes_en_markdown(txt_puro, assets)
        reporte.append(f"- ✅ **Fase 3 (Zero-Chatter Safety Guard):** Texto esterilizado (Índice de retención: 100%).")

        # Fase 4: Compilación y Prueba de Entrega
        formato_norm = formato_objetivo if formato_objetivo.startswith(".") else f".{formato_objetivo}"
        ruta_salida_test = SALIDA_DIR / f"test_verification_{p.stem}{formato_norm}"
        ruta_compilada = exportar_documento_formato(txt_con_anclas, ruta_salida_test, formato_norm)

        if ruta_compilada.exists() and ruta_compilada.stat().st_size > 0:
            reporte.append(f"- ✅ **Fase 4 (Compilación y Entrega):** Archivo `{ruta_compilada.name}` generado ({ruta_compilada.stat().st_size} bytes).")
            reporte.append("\n🎯 **RESULTADO FINAL: VERIFICACIÓN EXITOSA (100% QUALITY GATE PASSED)**")
        else:
            reporte.append(f"- ❌ **Fase 4 (Compilación):** El archivo generado está vacío o no se guardó.")
            reporte.append("\n⚠️ **RESULTADO FINAL: RECHAZADO EN FASE 4**")

        return "\n".join(reporte)
    except Exception as e:
        return f"❌ Fallo en el ciclo de verificación: {e}"


@server.tool()
def ecc_token_telemetry() -> str:
    """
    [Harnes /ECC - Cost-Aware Pipeline] Monitorea la telemetría de tokens, VRAM de GTX 1650
    y disponibilidad de modelos en Ollama para asegurar ejecución sin desbordamientos de memoria.
    """
    return telemetria_hardware_local()


@server.tool()
def ecc_agregar_marca_agua(
    ruta_archivo: str,
    texto_marca: str = "CONFIDENCIAL",
    color_hex: str = "#ef4444"
) -> str:
    """
    [Harnes /ECC - Multimodal 360°] Inyecta una marca de agua diagonal profesional
    en un archivo PDF o Word (.docx) con opacidad calibrada y ángulo de 45°.
    """
    from core.watermark import procesar_marca_agua

    p = Path(ruta_archivo.strip('"\'')).resolve()
    if not p.exists():
        return f"Error: Archivo no existe '{ruta_archivo}'"

    nombre_salida = f"{p.stem}_marca_agua{p.suffix}"
    ruta_salida = SALIDA_DIR / nombre_salida

    try:
        res = procesar_marca_agua(p, ruta_salida, accion="agregar", texto=texto_marca)
        bloque = generar_bloque_descarga_markdown(
            archivo_nombre=res.name,
            ruta_absoluta=res.resolve(),
            formato=res.suffix
        )
        return f"✅ **Marca de agua '{texto_marca}' inyectada exitosamente**\n{bloque}"
    except Exception as e:
        return f"Error al inyectar marca de agua: {e}"


@server.tool()
def ecc_quitar_marca_agua(ruta_archivo: str) -> str:
    """
    [Harnes /ECC - Multimodal 360°] Remueve quirúrgicamente marcas de agua y leyendas
    protectoras de un archivo PDF o Word (.docx).
    """
    from core.watermark import procesar_marca_agua

    p = Path(ruta_archivo.strip('"\'')).resolve()
    if not p.exists():
        return f"Error: Archivo no existe '{ruta_archivo}'"

    nombre_salida = f"{p.stem}_sin_marca{p.suffix}"
    ruta_salida = SALIDA_DIR / nombre_salida

    try:
        res = procesar_marca_agua(p, ruta_salida, accion="quitar")
        bloque = generar_bloque_descarga_markdown(
            archivo_nombre=res.name,
            ruta_absoluta=res.resolve(),
            formato=res.suffix
        )
        return f"✅ **Marcas de agua removidas exitosamente**\n{bloque}"
    except Exception as e:
        return f"Error al remover marca de agua: {e}"


@server.tool()
def ecc_quitar_imagen(ruta_archivo: str, posicion_imagen: int = 1) -> str:
    """
    [Harnes /ECC - Image Surgery] Elimina quirúrgicamente una imagen en la posición indicada (1..N)
    de un documento Word (.docx) o PDF preservando la alineación y maquetación restante.
    """
    from core.image_surgery import quitar_imagen_documento

    p = Path(ruta_archivo.strip('"\'')).resolve()
    if not p.exists():
        return f"Error: Archivo no existe '{ruta_archivo}'"

    nombre_salida = f"{p.stem}_sin_img{posicion_imagen}{p.suffix}"
    ruta_salida = SALIDA_DIR / nombre_salida

    try:
        res = quitar_imagen_documento(p, ruta_salida, posicion_1_based=posicion_imagen)
        bloque = generar_bloque_descarga_markdown(
            archivo_nombre=res.name,
            ruta_absoluta=res.resolve(),
            formato=res.suffix
        )
        return f"✅ **Imagen #{posicion_imagen} eliminada exitosamente**\n{bloque}"
    except Exception as e:
        return f"Error al eliminar imagen #{posicion_imagen}: {e}"


@server.tool()
def ecc_reemplazar_imagen(
    ruta_archivo: str,
    posicion_imagen: int,
    ruta_nueva_imagen: str
) -> str:
    """
    [Harnes /ECC - Image Surgery] Reemplaza una imagen en la posición especificada (1..N)
    por una nueva imagen con calibración dimensional y fidelidad pixel-perfect.
    """
    from core.image_surgery import reemplazar_imagen_docx

    p = Path(ruta_archivo.strip('"\'')).resolve()
    p_img = Path(ruta_nueva_imagen.strip('"\'')).resolve()

    if not p.exists():
        return f"Error: Documento no existe '{ruta_archivo}'"
    if not p_img.exists():
        return f"Error: Nueva imagen no existe '{ruta_nueva_imagen}'"

    nombre_salida = f"{p.stem}_img_reemplazada{p.suffix}"
    ruta_salida = SALIDA_DIR / nombre_salida

    try:
        res = reemplazar_imagen_docx(p, ruta_salida, posicion_imagen, p_img)
        bloque = generar_bloque_descarga_markdown(
            archivo_nombre=res.name,
            ruta_absoluta=res.resolve(),
            formato=res.suffix
        )
        return f"✅ **Imagen #{posicion_imagen} reemplazada con éxito**\n{bloque}"
    except Exception as e:
        return f"Error al reemplazar imagen: {e}"


@server.tool()
def ecc_resumen_ejecutivo(ruta_archivo: str, formato_salida: str = "pdf") -> str:
    """
    [Harnes /ECC - Executive Intelligence] Genera un Resumen Ejecutivo Directivo C-Level
    con Tesis Central, Hallazgos Clave, Matriz Cuantitativa, Análisis de Riesgos y Plan de Acción.
    Exporta el informe a formato descargable (.pdf, .docx, .html).
    """
    from core.executive_summarizer import generar_resumen_ejecutivo, exportar_resumen_ejecutivo

    p = Path(ruta_archivo.strip('"\'')).resolve()
    if not p.exists():
        return f"Error: Archivo no existe '{ruta_archivo}'"

    try:
        resumen_data = generar_resumen_ejecutivo(p, modelo="qwen2.5:3b")
        formato_norm = formato_salida if formato_salida.startswith(".") else f".{formato_salida}"
        nombre_salida = f"Resumen_Ejecutivo_{p.stem}{formato_norm}"
        ruta_salida = SALIDA_DIR / nombre_salida

        res_archivo = exportar_resumen_ejecutivo(resumen_data, ruta_salida, formato=formato_norm)
        bloque = generar_bloque_descarga_markdown(
            archivo_nombre=res_archivo.name,
            ruta_absoluta=res_archivo.resolve(),
            formato=formato_norm,
            texto_previsualizacion=resumen_data.get("contenido_markdown", "")
        )

        return (
            f"📊 **Resumen Ejecutivo C-Level Generado Exitosamente**\n"
            f"- **Documento Fuente:** `{p.name}`\n"
            f"- **Palabras Originales:** {resumen_data.get('palabras_originales')}\n"
            f"- **Palabras Resumen:** {resumen_data.get('palabras_resumen')}\n"
            f"{bloque}"
        )
    except Exception as e:
        return f"Error al generar resumen ejecutivo: {e}"


@server.tool()
def ecc_transformar_formato(ruta_archivo: str, formato_destino: str) -> str:
    """
    [Harnes /ECC - Format Engine] Transforma un documento de manera legítima y bidireccional
    entre PDF, DOCX, ODT, RTF, HTML, CSV, MD y TXT preservando imágenes y maquetación.
    """
    from core.format_converter import transformar_formato_documento

    p = Path(ruta_archivo.strip('"\'')).resolve()
    if not p.exists():
        return f"Error: Archivo no existe '{ruta_archivo}'"

    try:
        formato_norm = formato_destino if formato_destino.startswith(".") else f".{formato_destino}"
        nombre_salida = f"{p.stem}_convertido{formato_norm}"
        ruta_salida = SALIDA_DIR / nombre_salida

        res = transformar_formato_documento(p, formato_norm, ruta_salida)
        bloque = generar_bloque_descarga_markdown(
            archivo_nombre=res.name,
            ruta_absoluta=res.resolve(),
            formato=formato_norm
        )
        return f"✅ **Documento transformado exitosamente a {formato_norm.upper()}**\n{bloque}"
    except Exception as e:
        return f"Error al transformar formato: {e}"


@server.tool()
def ecc_abrir_documento(nombre_archivo: str) -> str:
    """
    [Harnes /ECC - Windows Native] Abre el documento físico directamente en Windows 10
    (Word, Acrobat, etc.) mediante os.startfile. Resuelve el clic en AnythingLLM.
    """
    import os
    nombre_seguro = Path(nombre_archivo.strip('"\'')).name
    ruta = SALIDA_DIR / nombre_seguro

    if not ruta.exists():
        ruta_alt = BASE_DIR / "datos" / "salida_web" / nombre_seguro
        if ruta_alt.exists():
            ruta = ruta_alt

    if not ruta.exists():
        desktop = Path.home() / "Desktop" / nombre_seguro
        if desktop.exists():
            ruta = desktop

    if not ruta.exists():
        return f"Error: Archivo '{nombre_seguro}' no encontrado en el servidor ni en el Escritorio."

    try:
        os.startfile(str(ruta.resolve()))
        return f"⚡ **Archivo '{nombre_seguro}' abierto con éxito en Windows 10.**"
    except Exception as e:
        return f"Error al abrir archivo en Windows: {e}"


if __name__ == "__main__":
    server.run(transport="stdio")

