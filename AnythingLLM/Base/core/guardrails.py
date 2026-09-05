"""
core/guardrails.py - Capa 5: Guardrails de Salida, Sanitización y Auditoría.
Implementa el aislamiento de trazas de pensamiento (<think>) para DeepSeek-R1,
validación y auto-reparación de JSON y verificación de integridad estructural en Markdown.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AuditResult:
    """Resultado de la auditoría de calidad y validación de salida."""
    es_valido: bool
    score_calidad: float
    errores: List[str] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)
    razonamiento_capturado: Optional[str] = None
    texto_limpio: str = ""


def separar_razonamiento_y_respuesta(texto: str) -> Tuple[Optional[str], str]:
    """
    Extrae los bloques de pensamiento <think>...</think> emitidos por modelos
    de razonamiento tipo DeepSeek-R1. Devuelve (razonamiento, texto_limpio).
    """
    if not texto:
        return None, ""

    patron_completo = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)
    match = patron_completo.search(texto)

    if match:
        razonamiento = match.group(1).strip()
        texto_limpio = patron_completo.sub("", texto).strip()
        return razonamiento, texto_limpio

    # Caso en que el modelo dejó abierto el tag por truncamiento: <think>...
    patron_incompleto = re.compile(r"<think>(.*)", re.DOTALL | re.IGNORECASE)
    match_inc = patron_incompleto.search(texto)
    if match_inc:
        razonamiento = match_inc.group(1).strip()
        texto_limpio = patron_incompleto.sub("", texto).strip()
        return razonamiento, texto_limpio

    return None, texto.strip()


def extraer_bloque_json(texto: str) -> str:
    """Extrae el contenido dentro de bloques ```json ... ``` o delimita llaves {}."""
    texto_strip = texto.strip()
    # Buscar bloque fenced markdown ```json ... ```
    match_fence = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", texto_strip, re.DOTALL)
    if match_fence:
        return match_fence.group(1).strip()

    # Buscar entre la primera llave '{' y la última '}'
    inicio = texto_strip.find("{")
    fin = texto_strip.rfind("}")
    if inicio != -1 and fin != -1 and fin > inicio:
        return texto_strip[inicio : fin + 1]

    # Buscar entre corchetes '[' y ']' para listas
    inicio_arr = texto_strip.find("[")
    fin_arr = texto_strip.rfind("]")
    if inicio_arr != -1 and fin_arr != -1 and fin_arr > inicio_arr:
        return texto_strip[inicio_arr : fin_arr + 1]

    return texto_strip


def validar_json_estricto(texto: str) -> Tuple[bool, Optional[Any], Optional[str]]:
    """Valida si el texto contiene un JSON válido (objeto o lista)."""
    cadena_candidata = extraer_bloque_json(texto)
    try:
        parsed = json.loads(cadena_candidata)
        return True, parsed, None
    except json.JSONDecodeError as e:
        return False, None, f"JSONDecodeError: {e}"


def reparar_json_incompleto(texto: str) -> Optional[Any]:
    """
    Intenta cerrar de forma heurística estructuras JSON truncadas
    (comillas abiertas, corchetes o llaves no cerradas).
    """
    cadena = extraer_bloque_json(texto).strip()
    if not cadena:
        return None

    # Intentar parseo directo
    try:
        return json.loads(cadena)
    except json.JSONDecodeError:
        pass

    # Heurística: balancear comillas, llaves y corchetes
    reparada = cadena
    # Si termina con comilla sin cerrar
    if reparada.count('"') % 2 != 0:
        reparada += '"'

    llaves_abiertas = reparada.count("{") - reparada.count("}")
    corchetes_abiertos = reparada.count("[") - reparada.count("]")

    if corchetes_abiertos > 0:
        reparada += "]" * corchetes_abiertos
    if llaves_abiertas > 0:
        reparada += "}" * llaves_abiertas

    try:
        return json.loads(reparada)
    except json.JSONDecodeError:
        return None


def validar_markdown_estructurado(
    texto: str,
    longitud_esperada_min: int = 20,
    longitud_original: Optional[int] = None
) -> AuditResult:
    """
    Audita la consistencia de una salida en Markdown:
    - Presencia de encabezados semánticos
    - Bloques de código debidamente cerrados
    - Preservación razonable de contenido
    """
    errores: List[str] = []
    advertencias: List[str] = []

    razonamiento, texto_limpio = separar_razonamiento_y_respuesta(texto)

    if not texto_limpio or len(texto_limpio) < longitud_esperada_min:
        errores.append(f"Texto de salida excesivamente corto o vacío ({len(texto_limpio)} caracteres).")

    # Verificar balance de bloques de código markdown ```
    fences = texto_limpio.count("```")
    if fences % 2 != 0:
        advertencias.append("Bloque de código Markdown sin cerrar (número impar de triples comillas invertidas).")

    # Ratio de preservación si se proporciona la longitud original
    score_calidad = 100.0
    if longitud_original and longitud_original > 0:
        ratio = min(len(texto_limpio), longitud_original) / max(len(texto_limpio), longitud_original)
        score_calidad = round(ratio * 100.0, 1)
        if ratio < 0.4:
            advertencias.append(f"Ratio de preservación inusualmente bajo ({score_calidad}%). Posible pérdida de contenido.")

    es_valido = len(errores) == 0

    return AuditResult(
        es_valido=es_valido,
        score_calidad=score_calidad,
        errores=errores,
        advertencias=advertencias,
        razonamiento_capturado=razonamiento,
        texto_limpio=texto_limpio
    )


# ---------------------------------------------------------------------------
# Contratos Pydantic y Guardrails para Modelos de Visión (VLM)
# ---------------------------------------------------------------------------
from pydantic import BaseModel, Field, ConfigDict


class ElementoVisual(BaseModel):
    id: str = ""
    type: str = "elemento"
    label: str = ""
    location: str = ""
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class RelacionVisual(BaseModel):
    origen: str = Field(default="", alias="from")
    destino: str = Field(default="", alias="to")
    relation: str = "conecta"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    model_config = ConfigDict(populate_by_name=True)


class MetadatosVisuales(BaseModel):
    image_id: str
    source_document: str = ""
    page: int = 1
    position: int = 1
    format: str = "png"
    width: int = 0
    height: int = 0
    sha256_hash: str = ""
    visual_type: str = "general"
    title: str = ""
    caption: str = ""
    visible_text: List[str] = Field(default_factory=list)
    elements: List[ElementoVisual] = Field(default_factory=list)
    relationships: List[RelacionVisual] = Field(default_factory=list)
    reconstructed_markdown: str = ""
    accessibility_alt_text: str = ""
    warnings: List[str] = Field(default_factory=list)
    overall_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    requires_human_review: bool = False


def validar_y_reparar_metadatos_visuales(
    texto_raw: str,
    image_id: str,
    doc_name: str = "",
    sha256_hash: str = "",
    umbral_revision_humana: float = 0.6
) -> MetadatosVisuales:
    """
    Parsea, valida y auto-repara la salida JSON de un VLM, garantizando
    la conformidad estricta con el contrato de metadatos visuales.
    Si el JSON está incompleto o ausente, genera un fallback seguro
    marcado para revisión humana (Gaps V-03, V-04, V-05, V-12).
    """
    _, texto_limpio = separar_razonamiento_y_respuesta(texto_raw)
    bloque_json = extraer_bloque_json(texto_limpio)
    data: Dict[str, Any] = {}

    if bloque_json:
        try:
            data = json.loads(bloque_json)
        except json.JSONDecodeError:
            reparado = reparar_json_incompleto(texto_limpio)
            if isinstance(reparado, dict):
                data = reparado
            elif isinstance(reparado, str):
                try:
                    data = json.loads(reparado)
                except Exception:
                    data = {}

    if not isinstance(data, dict) or not data:
        return MetadatosVisuales(
            image_id=image_id,
            source_document=doc_name,
            sha256_hash=sha256_hash,
            visual_type="no_reconocido",
            caption="Fallo en la extracción de metadatos visuales estructurados.",
            reconstructed_markdown=f"> [IMAGEN: {image_id}]\n> Estado: Error de decodificación VLM.",
            warnings=["No se pudo parsear JSON válido del modelo visual."],
            overall_confidence=0.0,
            requires_human_review=True
        )

    visual_type = str(data.get("visual_type") or "general").strip()
    title = str(data.get("title") or "").strip()
    caption = str(data.get("caption") or "").strip()

    raw_visible = data.get("visible_text", [])
    visible_text_list: List[str] = []
    if isinstance(raw_visible, list):
        for item in raw_visible:
            if isinstance(item, dict) and "text" in item:
                visible_text_list.append(str(item["text"]))
            elif isinstance(item, str) and item.strip():
                visible_text_list.append(item.strip())

    elementos_list: List[ElementoVisual] = []
    raw_elements = data.get("elements", [])
    if isinstance(raw_elements, list):
        for elem in raw_elements:
            if isinstance(elem, dict):
                conf = float(elem.get("confidence", 0.8))
                conf = max(0.0, min(1.0, conf))
                elementos_list.append(
                    ElementoVisual(
                        id=str(elem.get("id") or ""),
                        type=str(elem.get("type") or "nodo"),
                        label=str(elem.get("label") or ""),
                        location=str(elem.get("location") or ""),
                        confidence=conf
                    )
                )

    relaciones_list: List[RelacionVisual] = []
    raw_rel = data.get("relationships", [])
    if isinstance(raw_rel, list):
        for r in raw_rel:
            if isinstance(r, dict):
                conf = float(r.get("confidence", 0.8))
                conf = max(0.0, min(1.0, conf))
                relaciones_list.append(
                    RelacionVisual(
                        origen=str(r.get("from") or r.get("origen") or ""),
                        destino=str(r.get("to") or r.get("destino") or ""),
                        relation=str(r.get("relation") or "conecta"),
                        confidence=conf
                    )
                )

    overall_conf = float(data.get("overall_confidence", 0.8))
    overall_conf = max(0.0, min(1.0, overall_conf))

    warnings_list = [str(w) for w in data.get("warnings", []) if str(w).strip()]
    req_review = overall_conf < umbral_revision_humana or len(warnings_list) > 0

    reconstructed_md = str(data.get("reconstructed_markdown") or "").strip()
    if not reconstructed_md:
        lineas_md = [f"> [IMAGEN: {image_id}]", f"> Tipo: {visual_type}"]
        if title:
            lineas_md.append(f"> Título: {title}")
        if caption:
            lineas_md.append(f"> Descripción: {caption}")
        if visible_text_list:
            lineas_md.append(f"> Texto visible: {', '.join(visible_text_list[:5])}")
        reconstructed_md = "\n".join(lineas_md)

    return MetadatosVisuales(
        image_id=image_id,
        source_document=doc_name,
        sha256_hash=sha256_hash,
        visual_type=visual_type,
        title=title,
        caption=caption,
        visible_text=visible_text_list,
        elements=elementos_list,
        relationships=relaciones_list,
        reconstructed_markdown=reconstructed_md,
        accessibility_alt_text=str(data.get("accessibility_alt_text") or caption),
        warnings=warnings_list,
        overall_confidence=overall_conf,
        requires_human_review=req_review
    )

