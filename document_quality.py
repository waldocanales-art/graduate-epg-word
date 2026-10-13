"""Auditoría no invasiva de documentos DOCX generados por HAWKS.

No modifica la plantilla ni el documento y nunca presume que una firma existe.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from lxml import etree

TOKEN = re.compile(r"\{\{\s*([A-Za-z][A-Za-z0-9_]*)\s*\}\}")
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
REQUIRED_BY_TEMPLATE = {
    "ACTA_SUSTENTACION": ("PROGRAM", "TITLE", "AUTHORS_DISPLAY", "SUST_DATE_LONG"),
    "ACTA_ORIGINALIDAD": ("TITLE", "AUTHORS_DISPLAY"),
    "AUTORIZACION_PUBLICACION": ("TITLE", "AUTHORS_DISPLAY"),
    "DECLARACION_ORIGINALIDAD": ("TITLE", "AUTHORS_DISPLAY"),
    "DECLARACION_JURADA": ("TITLE", "AUTHORS_DISPLAY"),
    "METADATA_1": ("TITLE",),
    "METADATA_2": ("TITLE",),
    "METADATA_3": ("TITLE",),
}


def _inspect_xml_docx(path):
    visible = []
    xml_parts = 0
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        if "[Content_Types].xml" not in names or "word/document.xml" not in names:
            raise ValueError("DOCX sin estructura Word válida")
        for name in sorted(names):
            if not (name.startswith("word/") and name.endswith(".xml")):
                continue
            content = archive.read(name)
            try:
                root = etree.fromstring(content)
            except etree.XMLSyntaxError as exc:
                raise ValueError("XML inválido en " + name) from exc
            xml_parts += 1
            for paragraph in root.xpath(".//w:p", namespaces=NS):
                text = "".join(t.text or "" for t in paragraph.xpath(".//w:t", namespaces=NS))
                if text:
                    visible.append(text)
    return visible, xml_parts


def audit_document(path, template_key, fields=None, images=None):
    """Devuelve hallazgos verificables; no certifica cumplimiento normativo."""
    fields = fields or {}
    images = images or {}
    key = str(template_key).strip().upper()
    findings = []
    if key not in REQUIRED_BY_TEMPLATE:
        findings.append({"severity": "error", "code": "UNKNOWN_TEMPLATE", "detail": key})
    required = REQUIRED_BY_TEMPLATE.get(key, ())
    for field in required:
        if not str(fields.get(field, "") or "").strip():
            findings.append({"severity": "error", "code": "MISSING_FIELD", "detail": field})
    path = Path(path)
    try:
        paragraphs, part_count = _inspect_xml_docx(path)
    except (OSError, BadZipFile, ValueError, KeyError) as exc:
        return {"ok": False, "template_key": key,
                "findings": findings + [{"severity": "error", "code": "INVALID_DOCX", "detail": str(exc)}]}
    text = "\n".join(paragraphs)
    unresolved = sorted(set(TOKEN.findall(text)))
    for token in unresolved:
        findings.append({"severity": "error", "code": "UNRESOLVED_TOKEN", "detail": token})
    for k in images:
        if not str(k).upper().startswith("IMG_"):
            findings.append({"severity": "warning", "code": "IMAGE_KEY_NOT_CANONICAL", "detail": str(k)})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "template_key": key,
        "unresolved_tokens": unresolved,
        "xml_parts_checked": part_count,
        "findings": findings,
        "limitation": "Firmas, huellas, autenticidad, paginación PDF y conformidad institucional requieren revisión específica.",
    }
