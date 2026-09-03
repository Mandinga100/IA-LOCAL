"""
extractor_visual.py - Extracción segura, normalización y hash de imágenes embebidas.
Soporta inicialmente documentos DOCX con salvaguardas contra Decompression Bombs
(Pixel Flood DoS), Path Traversal en assets y downscaling adaptativo para VLMs locales.
Bajo gobernanza /ECC y principios de ciberseguridad por diseño.
"""

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Any
from PIL import Image
from logs import logger

# Límite estricto contra ataques de descompresión (Pixel Flood DoS) - Gap V-13
MAX_PIXELS_SEGURO: int = 50_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS_SEGURO

# Dimensión máxima sugerida para proteger la VRAM de modelos visuales (Gap V-14)
MAX_DIMENSION_VLM: int = 1280


class ExtraccionVisualError(Exception):
    """Excepción de dominio cuando ocurre un error durante la extracción de imágenes."""
    pass


class DecompressionBombError(ExtraccionVisualError):
    """Excepción cuando una imagen excede los límites seguros de descompresión."""
    pass


@dataclass(frozen=True)
class AssetVisual:
    """Representación inmutable de un asset visual extraído y normalizado."""
    image_id: str
    ruta_disco: Path
    rel_path: str
    sha256_hash: str
    formato: str
    ancho: int
    alto: int
    posicion: int
    tamano_bytes: int


def calcular_hash_imagen(datos_binarios: bytes) -> str:
    """Calcula el hash SHA-256 de los bytes de una imagen."""
    return hashlib.sha256(datos_binarios).hexdigest()


def normalizar_y_redimensionar(
    datos_binarios: bytes,
    max_dimension: int = MAX_DIMENSION_VLM
) -> bytes:
    """
    Verifica la imagen contra límites de tamaño y la redimensiona manteniendo
    la relación de aspecto si su lado mayor excede max_dimension.
    Devuelve los bytes en formato PNG normalizado.
    """
    try:
        with Image.open(io.BytesIO(datos_binarios)) as img:
            ancho, alto = img.size
            if ancho * alto > MAX_PIXELS_SEGURO:
                raise DecompressionBombError(
                    f"Imagen excede el límite seguro de descompresión: {ancho}x{alto} píxeles"
                )

            # Redimensionar si excede el lado mayor
            lado_mayor = max(ancho, alto)
            if lado_mayor > max_dimension:
                factor = max_dimension / lado_mayor
                nuevo_ancho = max(1, int(ancho * factor))
                nuevo_alto = max(1, int(alto * factor))
                img_res = img.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
            else:
                img_res = img

            # Normalizar a RGB/RGBA y exportar a PNG
            buffer = io.BytesIO()
            if img_res.mode in ("RGBA", "LA") or (img_res.mode == "P" and "transparency" in img_res.info):
                img_res.convert("RGBA").save(buffer, format="PNG", optimize=True)
            else:
                img_res.convert("RGB").save(buffer, format="PNG", optimize=True)
            return buffer.getvalue()
    except Image.DecompressionBombError as e:
        raise DecompressionBombError(f"Pixel Flood detectado por Pillow: {e}") from e
    except Exception as e:
        if isinstance(e, DecompressionBombError):
            raise
        raise ExtraccionVisualError(f"Fallo al procesar imagen binaria: {e}") from e


def extraer_imagenes_docx(
    ruta_docx: Path,
    dir_salida_assets: Path,
    doc_hash: Optional[str] = None,
    max_dimension: int = MAX_DIMENSION_VLM
) -> List[AssetVisual]:
    """
    Extrae todas las imágenes embebidas en un archivo .docx de manera segura.
    - Sanitiza rutas para prevenir Path Traversal (Gap V-15).
    - Aplica guardia contra bombas de descompresión (Gap V-13).
    - Aplica downscaling para proteger la VRAM de Ollama (Gap V-14).
    - Genera hashes SHA-256 únicos por imagen (Gap V-02).
    """
    if not ruta_docx.exists():
        raise ExtraccionVisualError(f"El archivo no existe: {ruta_docx}")

    # Blindaje contra Path Traversal en el directorio de salida
    dir_salida_base = dir_salida_assets.resolve()
    dir_salida_base.mkdir(parents=True, exist_ok=True)

    hash_doc_prefix = doc_hash[:8] if doc_hash else "doc"
    carpeta_doc_assets = dir_salida_base / hash_doc_prefix
    carpeta_doc_assets.mkdir(parents=True, exist_ok=True)

    if not carpeta_doc_assets.resolve().is_relative_to(dir_salida_base):
        raise ExtraccionVisualError("Intento de Path Traversal detectado en directorio de assets")

    import docx

    try:
        doc = docx.Document(str(ruta_docx))
    except Exception as e:
        raise ExtraccionVisualError(f"Error al abrir documento DOCX {ruta_docx.name}: {e}") from e

    assets_extraidos: List[AssetVisual] = []
    posicion = 1

    # Extraer de todas las partes relacionadas con imágenes
    for part in doc.part.related_parts.values():
        if "image" in part.content_type:
            raw_bytes = part.blob
            if not raw_bytes:
                continue

            try:
                # Normalizar y proteger contra bombas de píxeles
                bytes_procesados = normalizar_y_redimensionar(raw_bytes, max_dimension=max_dimension)
                img_hash = calcular_hash_imagen(bytes_procesados)

                # Obtener dimensiones finales
                with Image.open(io.BytesIO(bytes_procesados)) as img_final:
                    ancho_f, alto_f = img_final.size

                image_id = f"{hash_doc_prefix}-img-{posicion:03d}-{img_hash[:8]}"
                nombre_archivo = f"{image_id}.png"
                ruta_archivo = carpeta_doc_assets / nombre_archivo

                # Verificar ruta final estricta
                if not ruta_archivo.resolve().is_relative_to(dir_salida_base):
                    raise ExtraccionVisualError(f"Ruta de asset insegura: {ruta_archivo}")

                ruta_archivo.write_bytes(bytes_procesados)
                rel_path = f"assets/{hash_doc_prefix}/{nombre_archivo}"

                asset = AssetVisual(
                    image_id=image_id,
                    ruta_disco=ruta_archivo,
                    rel_path=rel_path,
                    sha256_hash=img_hash,
                    formato="png",
                    ancho=ancho_f,
                    alto=alto_f,
                    posicion=posicion,
                    tamano_bytes=len(bytes_procesados)
                )
                assets_extraidos.append(asset)
                posicion += 1

            except DecompressionBombError as dbe:
                logger.warning(f"Imagen en {ruta_docx.name} omitida por riesgo DoS: {dbe}")
                continue
            except Exception as e:
                logger.error(f"Error al procesar imagen en posición {posicion}: {e}")
                continue

    return assets_extraidos


def extraer_imagenes_pdf(
    ruta_pdf: Path,
    dir_salida_assets: Path,
    doc_hash: Optional[str] = None,
    max_dimension: int = MAX_DIMENSION_VLM
) -> List[AssetVisual]:
    """
    Extrae quirúrgicamente todas las imágenes incrustadas en un archivo PDF utilizando pypdfium2.
    Preserva resolución pixel-perfect, modo de color, calcula SHA-256 e impide DoS por descompresión.
    """
    if not ruta_pdf.exists():
        raise ExtraccionVisualError(f"Archivo PDF no existe: {ruta_pdf}")

    try:
        import pypdfium2 as pdfium
    except ImportError as ie:
        raise ExtraccionVisualError(f"pypdfium2 no está instalado: {ie}") from ie

    # Hash del documento para aislamiento de directorio
    if not doc_hash:
        doc_hash = hashlib.sha256(ruta_pdf.read_bytes()).hexdigest()
    hash_doc_prefix = doc_hash[:16]

    dir_salida_base = dir_salida_assets.resolve()
    carpeta_doc_assets = dir_salida_base / hash_doc_prefix
    carpeta_doc_assets.mkdir(parents=True, exist_ok=True)

    assets_extraidos: List[AssetVisual] = []
    posicion = 1

    try:
        doc = pdfium.PdfDocument(str(ruta_pdf.resolve()))
        for page_num in range(len(doc)):
            page = doc[page_num]
            for obj in page.get_objects():
                obj_any: Any = obj
                obj_type = getattr(obj_any, "type", None)
                if obj_type == pdfium.raw.FPDF_PAGEOBJ_IMAGE or isinstance(obj, pdfium.PdfImage):
                    try:
                        bitmap = obj_any.get_bitmap()
                        pil_img = bitmap.to_pil()

                        # Convertir a bytes PNG preservando fidelidad
                        buf = io.BytesIO()
                        if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
                            pil_img.convert("RGBA").save(buf, format="PNG", optimize=True)
                        else:
                            pil_img.convert("RGB").save(buf, format="PNG", optimize=True)
                        raw_bytes = buf.getvalue()

                        # Normalización y chequeo de seguridad
                        bytes_procesados = normalizar_y_redimensionar(raw_bytes, max_dimension=max_dimension)
                        img_hash = calcular_hash_imagen(bytes_procesados)

                        with Image.open(io.BytesIO(bytes_procesados)) as img_final:
                            ancho_f, alto_f = img_final.size

                        image_id = f"{hash_doc_prefix}-p{page_num+1:02d}-img-{posicion:03d}-{img_hash[:8]}"
                        nombre_archivo = f"{image_id}.png"
                        ruta_archivo = carpeta_doc_assets / nombre_archivo

                        if not ruta_archivo.resolve().is_relative_to(dir_salida_base):
                            raise ExtraccionVisualError(f"Ruta de asset insegura: {ruta_archivo}")

                        ruta_archivo.write_bytes(bytes_procesados)
                        rel_path = f"assets/{hash_doc_prefix}/{nombre_archivo}"

                        asset = AssetVisual(
                            image_id=image_id,
                            ruta_disco=ruta_archivo,
                            rel_path=rel_path,
                            sha256_hash=img_hash,
                            formato="png",
                            ancho=ancho_f,
                            alto=alto_f,
                            posicion=posicion,
                            tamano_bytes=len(bytes_procesados)
                        )
                        assets_extraidos.append(asset)
                        posicion += 1

                    except DecompressionBombError as dbe:
                        logger.warning(f"Imagen en página {page_num+1} de {ruta_pdf.name} omitida por DoS: {dbe}")
                        continue
                    except Exception as e:
                        logger.error(f"Fallo al procesar imagen en página {page_num+1}: {e}")
                        continue

    except Exception as e:
        logger.error(f"Fallo al abrir o procesar PDF {ruta_pdf}: {e}", exc_info=True)
        raise ExtraccionVisualError(f"Error extrayendo imágenes de {ruta_pdf.name}: {e}") from e

    return assets_extraidos


def extraer_imagenes_documento(
    ruta_archivo: Path,
    dir_salida_assets: Path,
    doc_hash: Optional[str] = None
) -> List[AssetVisual]:
    """Despacha la extracción de imágenes según el formato (.docx o .pdf)."""
    ext = ruta_archivo.suffix.lower()
    if ext == ".docx":
        return extraer_imagenes_docx(ruta_archivo, dir_salida_assets, doc_hash=doc_hash)
    elif ext == ".pdf":
        return extraer_imagenes_pdf(ruta_archivo, dir_salida_assets, doc_hash=doc_hash)
    return []


def inyectar_anclas_imagenes_en_markdown(texto_md: str, assets: List[AssetVisual]) -> str:
    """
    Inserta o preserva las etiquetas de anclaje de imagen ![alt](ruta) en el texto Markdown.
    Si las imágenes ya están referenciadas, las valida; si no, las ancla quirúrgicamente.
    """
    if not assets:
        return texto_md

    texto_final = texto_md
    anclas_faltantes = []

    for asset in assets:
        ruta_str = str(asset.ruta_disco).replace("\\", "/")
        tag = f"![{asset.image_id}]({ruta_str})"
        if asset.image_id not in texto_final and asset.sha256_hash[:8] not in texto_final:
            anclas_faltantes.append(tag)

    if anclas_faltantes:
        texto_final = texto_final.rstrip() + "\n\n" + "\n\n".join(anclas_faltantes) + "\n"

    return texto_final

