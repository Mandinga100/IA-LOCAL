# Matriz de Compatibilidad Universal y Transformación de Formatos

## 1. Visión General y Estrategia de Interoperabilidad

La **Plataforma de IA Local** está diseñada sobre un paradigma de **Pivote Central en Markdown**. Este principio desacopla la extracción del contenido de la inferencia y de la reconstrucción:

```
                  ┌────────────────────────────────────────────────────────┐
                  │                    ENTRADAS (INGESTIÓN)                │
                  │   .docx, .doc, .odt, .rtf, .txt, .md, .pdf,            │
                  │   .pptx, .ppt, .xlsx, .xls, .csv, .epub, .html         │
                  └───────────────────────────┬────────────────────────────┘
                                              │
                                              ▼  [Extracción a Markdown]
                                  ┌────────────────────────┐
                                  │   Markdown UTF-8 Puro  │
                                  │   (Pivote Central)     │
                                  └───────────┬────────────┘
                                              │
                                              ▼  [Inferencia LLM Ollama]
                                  ┌────────────────────────┐
                                  │   Markdown Corregido   │
                                  └───────────┬────────────┘
                                              │
                                              ▼  [Reconstrucción / Export]
                  ┌────────────────────────────────────────────────────────┐
                  │                    SALIDAS GENERADAS                   │
                  │   Nativo: .docx, .odt, .rtf, .html, .txt, .md, .csv   │
                  │   Auditable: .corregido.md / .pdf (print-ready HTML)   │
                  └────────────────────────────────────────────────────────┘
```

---

## 2. Matriz Exhaustiva de Formatos Soportados y a Integrar

| Extensión | Tipo de Documento | Estado Actual | Motor de Extracción Propuesto | Motor de Reconstrucción Propuesto | Librería Python |
|---|---|---|---|---|---|
| **`.docx`** | Microsoft Word (OpenXML) | ✅ Nativo | `MarkItDown` / `python-docx` | `python-docx` (H1-H3, listas, tablas) | `python-docx` |
| **`.doc`** | Microsoft Word (Legacy OLE2) | 🟡 Por integrar | `antiword` / `olefile` / `pypandoc` | Export a `.docx` / `.corregido.md` | `olefile` / `pypandoc` |
| **`.odt`** | OpenDocument Text (LibreOffice) | 🟡 Por integrar | `odfpy` / `MarkItDown` / `zipfile` | `odfpy` (`OpenDocumentText`) | `odfpy` |
| **`.rtf`** | Rich Text Format | 🟡 Por integrar | `striprtf` (pure python) | Generador RTF / `.corregido.md` | `striprtf` |
| **`.txt`** | Texto Plano | ✅ Nativo | Python `open(encoding='utf-8')` | Python `open(encoding='utf-8')` | Built-in |
| **`.md`** | Markdown Document | ✅ Nativo | Python `open(encoding='utf-8')` | Python `open(encoding='utf-8')` | Built-in |
| **`.pdf`** | Portable Document Format | ✅ Nativo | `MarkItDown` (vía `pdfminer`/`pypdfium2`) | `.corregido.md` / HTML imprimible | `pypdfium2` / `weasyprint` |
| **`.pptx`** | Microsoft PowerPoint (OpenXML) | ✅ Nativo | `MarkItDown` (vía `python-pptx`) | `.corregido.md` / `python-pptx` | `python-pptx` |
| **`.ppt`** | Microsoft PowerPoint (Legacy OLE2)| 🟡 Por integrar | `olefile` / `ppthtml` | `.corregido.md` | `olefile` |
| **`.xlsx`** | Microsoft Excel (OpenXML) | ✅ Nativo | `MarkItDown` (vía `openpyxl`) | `.corregido.md` / `openpyxl` | `openpyxl` |
| **`.xls`** | Microsoft Excel (Legacy BIFF8) | 🟡 Por integrar | `xlrd` (pure python para .xls) | `.corregido.md` / `.csv` | `xlrd` |
| **`.csv`** | Valores Separados por Comas | 🟡 Por integrar | `csv` built-in ➔ Tabla Markdown | `csv` built-in ➔ CSV corregido | `csv` |
| **`.html`** | Documento Web HTML5 | ✅ Nativo | `MarkItDown` (vía `beautifulsoup4`) | HTML5 maquetado con CSS UTF-8 | `beautifulsoup4` |
| **`.epub`** | Libro Electrónico | 🟡 Por integrar | `ebooklib` + `beautifulsoup4` | `.corregido.md` / `.epub` | `ebooklib` |

---

## 3. Especificación Técnica de Transformación por Formato

### 3.1. Formato OpenDocument Text (`.odt`)
- **Arquitectura:** Contenedor ZIP estandarizado por OASIS conteniendo `content.xml`, `styles.xml` y `meta.xml`.
- **Estrategia de Ingestión:**
  1. Abrir el archivo con `zipfile.ZipFile` de forma segura.
  2. Parsear `content.xml` utilizando `xml.etree.ElementTree` con protección contra ataques de entidad (defusedxml).
  3. Mapear etiquetas `<text:h text:outline-level="1">` a `# Título`, `<text:p>` a párrafos y `<text:list-item>` a `- viñeta`.
- **Estrategia de Reconstrucción:**
  - Uso de la librería `odfpy` para crear instancias de `OpenDocumentText`, aplicando estilos de párrafo y cabeceras compatibles con LibreOffice y Microsoft Word.

---

### 3.2. Formato Rich Text Format (`.rtf`)
- **Arquitectura:** Documento en texto plano con grupos de control y comandos de formato de Microsoft (ej: `{\rtf1\ansi\deff0 ...}`).
- **Estrategia de Ingestión:**
  - Utilización de `striprtf`, librería pura en Python de alto rendimiento y cero dependencias binarias, que extrae el texto limpio y decodifica entidades ANSI/Unicode (`\uN?`).
- **Estrategia de Reconstrucción:**
  - Generación de documento RTF básico con cabecera estándar `{\rtf1\ansi\ansicpg1252\deff0 ...}` o exportación a `.docx` / `.corregido.md` para máxima fidelidad visual.

---

### 3.3. Formatos Binarios Legacy de Microsoft Office (`.doc`, `.xls`, `.ppt`)
- **Arquitectura:** Contenedor binario OLE2 (Compound File Binary Format).
- **Estrategia de Ingestión:**
  - Para `.doc`: Uso de `olefile` para inspeccionar streams de WordDocument o fallback a `pypandoc` / `docx2txt`.
  - Para `.xls`: Uso de `xlrd` (versión 2.0.1 que soporta exclusivamente el formato `.xls` histórico de forma segura).
  - Para `.ppt`: Extracción de streams de texto mediante `olefile`.
- **Estrategia de Reconstrucción:**
  - Dado que los formatos binarios OLE2 están obsoletos y son inherentemente inseguros para re-escritura binaria, la política recomendada es la **modernización de formato**: reconstruir hacia `.docx`, `.xlsx` o `.corregido.md`, garantizando compatibilidad con software moderno sin corrupción de datos.

---

### 3.4. Formato Tabular CSV / TSV (`.csv`, `.tsv`)
- **Estrategia de Ingestión:**
  - Módulo nativo `csv.Sniffer` para detectar delimitadores (`,`, `;`, `\t`).
  - Conversión a tabla Markdown:
    ```markdown
    | Columna 1 | Columna 2 | Columna 3 |
    |---|---|---|
    | Dato A | Dato B | Dato C |
    ```
- **Estrategia de Reconstrucción:**
  - Parseo de la tabla Markdown corregida y reescritura en CSV con codificación UTF-8 pura y delimitador configurable.

---

## 4. Patrón de Diseño para la Arquitectura Modular de Parsers

Para evitar bloques `if/elif` extensos y permitir una arquitectura orientada a plugins, se define la siguiente interfaz desacoplada:

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type

class BaseExtractor(ABC):
    """Interfaz abstracta para extracción de texto a Markdown."""
    @abstractmethod
    def extract(self, ruta: Path) -> str:
        pass

class BaseReconstructor(ABC):
    """Interfaz abstracta para reconstrucción de documentos corregidos."""
    @abstractmethod
    def reconstruct(self, texto_markdown: str, ruta_original: Path, ruta_destino: Path) -> Path:
        pass

class DocumentFormatRegistry:
    """Registro desacoplado de extractores y reconstructores por extensión."""
    _extractors: Dict[str, BaseExtractor] = {}
    _reconstructors: Dict[str, BaseReconstructor] = {}

    @classmethod
    def register_extractor(cls, extension: str, extractor: BaseExtractor) -> None:
        cls._extractors[extension.lower()] = extractor

    @classmethod
    def register_reconstructor(cls, extension: str, reconstructor: BaseReconstructor) -> None:
        cls._reconstructors[extension.lower()] = reconstructor

    @classmethod
    def get_extractor(cls, extension: str) -> BaseExtractor:
        return cls._extractors.get(extension.lower())

    @classmethod
    def get_reconstructor(cls, extension: str) -> BaseReconstructor:
        return cls._reconstructors.get(extension.lower())
```

---

## 5. Plan de Dependencias para Soporte Universal

Para habilitar la suite completa sin inflar el entorno virtual con dependencias pesadas, se estructuran los paquetes en `requirements.txt`:

```text
# Motores principales de extracción y reconstrucción
markitdown[all]>=0.0.1a4
python-docx>=1.1.2
openpyxl>=3.1.5
python-pptx>=1.0.2

# Formatos de texto enriquecido y abiertos (ligeros, pure python)
striprtf>=0.0.26        # Soporte para .rtf
odfpy>=1.4.1            # Soporte completo para .odt, .ods, .odp
xlrd>=2.0.1             # Soporte para .xls legacy
defusedxml>=0.7.1       # Protección contra ataques XXE en XML/ZIP

# Inferencia HTTP y utilidades
httpx>=0.28.1
tqdm>=4.67.1
```

---

## 6. Hoja de Ruta de Implementación de Formatos (Sprint 3 y 4)

- **Fase 1 (Inmediata - Sprint 3):**
  - Añadir soporte nativo para `.odt` y `.rtf` (extracción y reconstrucción).
  - Añadir soporte para `.csv` (tablas tabulares).
  - Actualizar `config.py` con `EXTENSIONES_SOPORTADAS = frozenset({".pdf", ".docx", ".doc", ".odt", ".rtf", ".pptx", ".ppt", ".xlsx", ".xls", ".csv", ".html", ".txt", ".md"})`.
- **Fase 2 (Sprint 4):**
  - Refactorizar `conversor.py` y `reconstructor.py` al patrón `DocumentFormatRegistry`.
  - Añadir suite de tests unitarios específicos para cada nuevo formato en `tests/unit/test_formatos_nuevos.py`.
