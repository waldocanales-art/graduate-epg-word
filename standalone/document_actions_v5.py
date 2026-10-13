"""HAWKS: control documental por grupo y acciones de recuperación por documento.

La tabla de evidencias es privada en una variable de Render; este módulo no
incluye datos personales ni enlaces de carpetas en el repositorio de GitHub.
Los botones de descarga conservan el original, sin alterar firmas ni huellas.
"""
from __future__ import annotations
import json
import os
import re

DOC_TYPES = [
    ("METADATA", "Hoja de metadatos"),
    ("DECLARACION_JURADA", "Declaración jurada de autoría"),
    ("DECLARACION_ORIGINALIDAD", "Declaración de originalidad"),
    ("AUTORIZACION_PUBLICACION", "Autorización de publicación"),
    ("ACTA_ORIGINALIDAD", "Acta de originalidad"),
    ("ACTA_SUSTENTACION", "Acta de sustentación"),
]
ID = re.compile(r"^[a-zA-Z0-9_-]{10,128}$")
TYPE = re.compile(r"^[A-Z_0-9]{3,60}$")


def read_private_catalog() -> dict:
    raw = os.environ.get("HAWKS_V5_DOCUMENT_CATALOG_JSON", "")
    if not raw:
        return {}
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("Catálogo privado inválido")
    if not isinstance(result, dict):
        raise ValueError("Catálogo privado no es un objeto")
    return result


def link(file_id: str | None):
    if not file_id or not ID.fullmatch(str(file_id)):
        return None
    return "https://drive.google.com/file/d/" + file_id + "/view"


def document_rows(group_id: str, catalog: dict | None = None) -> list[dict]:
    catalog = read_private_catalog() if catalog is None else catalog
    group_rows = catalog.get(str(group_id))
    if not isinstance(group_rows, list):
        return [
            {"id": name, "name": title,
             "status": "BUSQUEDA_DE_EVIDENCIAS_PENDIENTE", "word_url": None,
             "pdf_url": None, "source": "Sin inventario individual verificado",
             "can_download": False}
            for name, title in DOC_TYPES
        ]
    results = []
    used = set()
    for row in group_rows:
        if not isinstance(row, list) or not 3 <= len(row) <= 5:
            raise ValueError("Formato de fuente inválido")
        doc_id, title, word = row[:3]
        pdf = row[3] if len(row) >= 4 else ""
        if not TYPE.fullmatch(str(doc_id)) or doc_id in used:
            raise ValueError("Documento duplicado o ID inválido")
        used.add(doc_id)
        if word and not link(word) or pdf and not link(pdf):
            raise ValueError("Enlace de evidencia inválido")
        word_url, pdf_url = link(word), link(pdf)
        results.append({
            "id": doc_id,
            "name": str(title)[:180],
            "status": "ORIGINAL_LOCALIZADO_EN_DRIVE" if word_url or pdf_url else "PENDIENTE_FUENTE",
            "word_url": word_url, "pdf_url": pdf_url,
            "can_download": bool(word_url or pdf_url),
            "source": "Expediente institucional del equipo en Drive",
            "can_generate_new": False,
        })
    for code, title in DOC_TYPES:
        if not any(row["id"] == code or row["id"].startswith(code + "_") for row in results):
            results.append({"id": code, "name": title,
                            "status": "PENDIENTE_FUENTE", "word_url": None,
                            "pdf_url": None, "can_download": False,
                            "source": "No localizado en inventario verificado",
                            "can_generate_new": False})
    return results


def selected_document(group_id: str, doc_id: str) -> dict:
    found = [d for d in document_rows(group_id) if d["id"] == doc_id]
    if len(found) != 1:
        raise LookupError("Documento no localizado inequívocamente")
    return found[0]
