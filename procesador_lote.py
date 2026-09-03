"""
procesador_lote.py - Orquestador principal del pipeline por lotes.
Recorre carpetas, convierte documentos, procesa inferencia con IA y guarda resultados.
Incluye ledger de estado (historial_procesados.json) y barra de progreso.
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm

from config import Config
from logs import logger, configurar_logger
from explorador import explorar_directorio, DocumentoTarea
from conversor import convertir_a_markdown, ConversionError
from corrector import CorrectorOllama, InferenciaError
from reconstructor import guardar_documento_corregido, ReconstruccionError

class ProcesadorLote:
    """Orquestador de procesamiento batch para documentos con IA local."""

    def __init__(self, config: Config, tipo_documento: str = "general") -> None:
        self.config = config
        self.tipo_documento = tipo_documento
        self.corrector = CorrectorOllama(config)
        self.ruta_ledger = self.config.ruta_salida / "historial_procesados.json"
        self.historial = self._cargar_historial()

    def _cargar_historial(self) -> Dict[str, dict]:
        if self.ruta_ledger.exists():
            try:
                with open(self.ruta_ledger, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Historial corrupto. Se reiniciará el ledger.")
                return {}
        return {}

    def _guardar_historial(self) -> None:
        self.ruta_ledger.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ruta_ledger, "w", encoding="utf-8") as f:
            json.dump(self.historial, f, ensure_ascii=False, indent=2)

    def procesar_documento(self, tarea: DocumentoTarea) -> bool:
        """
        Ejecuta el ciclo de vida completo para un documento individual.
        """
        logger.info(f"--- Iniciando procesamiento: {tarea.ruta_relativa} ---")

        # 1. Comprobar si ya fue procesado con el mismo hash
        if tarea.hash_sha256 in self.historial:
            logger.info(f"Omitiendo {tarea.ruta_relativa} (ya procesado con idéntico contenido).")
            return True

        ruta_destino = self.config.ruta_salida / tarea.ruta_relativa

        try:
            # 2. Conversión a Markdown
            markdown_original = convertir_a_markdown(tarea.ruta_origen)
            if not markdown_original.strip():
                logger.warning(f"Documento sin texto extraíble: {tarea.ruta_relativa}")
                return False

            # 3. Corrección con IA local
            markdown_corregido = self.corrector.corregir_texto(
                markdown_original,
                tipo_documento=self.tipo_documento
            )

            # 4. Guardado y Reconstrucción
            ruta_final = guardar_documento_corregido(
                texto_corregido=markdown_corregido,
                ruta_original=tarea.ruta_origen,
                ruta_destino=ruta_destino
            )

            # 5. Registrar en ledger
            self.historial[tarea.hash_sha256] = {
                "archivo_origen": str(tarea.ruta_origen),
                "archivo_destino": str(ruta_final),
                "tamano_bytes": tarea.tamano_bytes,
                "tipo_documento": self.tipo_documento,
                "modelo": self.config.modelo
            }
            self._guardar_historial()

            logger.info(f"[OK] Documento completado con éxito: {tarea.ruta_relativa}")
            return True

        except (ConversionError, InferenciaError, ReconstruccionError, Exception) as e:
            logger.error(f"[ERROR] Fallo al procesar {tarea.ruta_relativa}: {e}", exc_info=True)
            # Copiar a ruta de errores para aislamiento eficiente
            destino_error = self.config.ruta_errores / tarea.ruta_relativa
            destino_error.parent.mkdir(parents=True, exist_ok=True)
            try:
                import shutil
                shutil.copy2(tarea.ruta_origen, destino_error)
                logger.info(f"Documento con error archivado en: {destino_error}")
            except Exception as copy_err:
                logger.error(f"No fue posible aislar el documento con error: {copy_err}")
            return False

    def ejecutar_lote(self) -> None:
        """Recorre y procesa todos los documentos encontrados en la ruta de entrada."""
        tareas = explorar_directorio(self.config.ruta_entrada, self.config.extensiones_soportadas)
        if not tareas:
            logger.info("No se encontraron documentos para procesar en la ruta de entrada.")
            return

        exitosos = 0
        fallidos = 0

        logger.info(f"Iniciando procesamiento de lote: {len(tareas)} documento(s)...")

        for tarea in tqdm(tareas, desc="Procesando documentos", unit="doc"):
            if self.procesar_documento(tarea):
                exitosos += 1
            else:
                fallidos += 1

        logger.info(f"Resumen de lote completado: {exitosos} exitosos, {fallidos} fallidos.")

def main() -> None:
    parser = argparse.ArgumentParser(description="Procesador de documentos con IA local (Ollama)")
    parser.add_argument("--origen", type=str, default="datos/entrada", help="Ruta de entrada de documentos")
    parser.add_argument("--destino", type=str, default="datos/salida", help="Ruta de salida para documentos corregidos")
    parser.add_argument("--tipo", type=str, default="general", choices=["general", "legal", "tecnico", "academico", "comercial"], help="Tipo de documento")
    parser.add_argument("--modelo", type=str, default="qwen2.5:7b", help="Modelo de Ollama principal")
    parser.add_argument("--fallback", type=str, default=None, help="Modelo de Ollama para fallback en caso de agotamiento de reintentos")
    parser.add_argument("--url", type=str, default="http://localhost:11434", help="URL de Ollama")
    parser.add_argument("--chunk-size", type=int, default=3500, help="Tamaño máximo de caracteres por chunk semántico")

    args = parser.parse_args()

    config = Config(
        ruta_entrada=Path(args.origen),
        ruta_salida=Path(args.destino),
        modelo=args.modelo,
        modelo_fallback=args.fallback,
        ollama_url=args.url,
        chunk_size=args.chunk_size
    )

    procesador = ProcesadorLote(config, tipo_documento=args.tipo)
    procesador.ejecutar_lote()

if __name__ == "__main__":
    main()
