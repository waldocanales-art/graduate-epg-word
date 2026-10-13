"""HAWKS V6: expedientes por grupo, validación cruzada y paquete íntegro.

El plan siempre funciona con el catálogo histórico. La descarga autenticada
de archivos SOLO se habilita con credenciales Drive de solo lectura en Render.
No estampa firmas, huellas ni altera archivos originales.
"""
from __future__ import annotations
import csv
import io
import json
import os
import re
import unicodedata
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import PurePosixPath

MAX_FILES = 180
MAX_FILE = 16 * 1024 * 1024
MAX_TOTAL = 100 * 1024 * 1024
FAMILIES = ("METADATA", "DECLARACION_JURADA", "DECLARACION_ORIGINALIDAD",
            "AUTORIZACION_PUBLICACION", "ACTA_ORIGINALIDAD",
            "ACTA_SUSTENTACION", "TURNITIN", "TRABAJO")
REQUIRED_BASE = FAMILIES[:5]
NAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")
PCT_RE = re.compile(r"(?<![0-9])([0-9]{1,3})\s*%")
TI_DATE = re.compile(r"(?<!\d)(\d{1,2})[-_.](\d{1,2})[-_.](20\d{2})(?!\d)")

def _norm(text):
    text = unicodedata.normalize("NFKD", str(text))
    return "".join(ch for ch in text if not unicodedata.combining(ch)).upper()

def _family(s):
    x = _norm(s)
    if "METADATA" in x: return "METADATA"
    if "DECLARACION" in x and "JURADA" in x: return "DECLARACION_JURADA"
    if "DECLARACION" in x and "ORIGINALIDAD" in x: return "DECLARACION_ORIGINALIDAD"
    if "AUTORIZACION" in x and "PUBLICACION" in x: return "AUTORIZACION_PUBLICACION"
    if "ACTA" in x and "ORIGINALIDAD" in x: return "ACTA_ORIGINALIDAD"
    if "ACTA" in x and "SUSTENTACION" in x: return "ACTA_SUSTENTACION"
    if "TURNITIN" in x: return "TURNITIN"
    if "TRABAJO" in x or ("TESIS" in x and "AUDITORIA" not in x) or x.startswith("TI_"): return "TRABAJO"
    return None

def _date(s):
    m = TI_DATE.search(s)
    return "%s-%s-%s" % (m.group(3), m.group(2).zfill(2), m.group(1).zfill(2)) if m else None

def _rows(group_id, docs):
    result = []
    for doc in docs:
        family = _family(doc.get("id", "")) or _family(doc.get("name", ""))
        if not family:
            continue
        urls = [u for u in (doc.get("word_url"), doc.get("pdf_url")) if u]
        if not urls:
            continue
        result.append({"group": group_id, "id": doc["id"], "category": family,
                       "name": doc["name"], "urls": urls})
    return result

def _normative(files):
    names = " ".join(_norm(f.get("name", "")) for f in files)
    has018 = bool(re.search(r"(?<!\d)018[-_ ]?2024", names))
    has088 = bool(re.search(r"(?<!\d)088[-_ ]?2023", names))
    return "018-2024-VRI-UA" if has018 and not has088 else (
        "088-2023-VRI-UA" if has088 and not has018 else
        "CONFLICTO_018_088" if has018 and has088 else "NO_CONFIRMADA")

def audit_group(group_id, team, program, phase, docs, live_files=None):
    rows = _rows(group_id, docs)
    counts = Counter(r["category"] for r in rows)
    # Catálogo estático: no equivale a lectura del contenido del archivo.
    live = live_files is not None
    source = live_files if live else [{"name": r["name"]} for r in rows]
    all_names = " ".join(_norm(x.get("name", "")) for x in source)
    guide = _normative(source)
    style = sorted(set(x for x, pattern in (
        ("APA7_023", r"(?:APA\s*7|023[-_ ]?2024)"),
        ("IEEE_025", r"(?:IEEE|025[-_ ]?202[45])"),
        ("VANCOUVER_024", r"(?:VANCOUVER|024[-_ ]?2024)"))
        if re.search(pattern, all_names)))
    reports = []
    for item in source:
        name = str(item.get("name", ""))
        if "TURNITIN" in _norm(name):
            pcts = [int(x) for x in PCT_RE.findall(name)]
            reports.append({"name": name, "percentages_named": pcts,
                            "date_from_filename": _date(name),
                            "needs_version_reconciliation": True})
    findings = []
    def flag(code, severity, detail):
        findings.append({"code": code, "severity": severity, "detail": detail})
    if not live:
        flag("SNAPSHOT_ONLY", "PENDIENTE", "El servidor no puede leer ahora los contenidos de Drive; los enlaces son referencias históricas")
    if not counts:
        flag("SIN_DOCUMENTOS_INDIVIDUALES", "PENDIENTE", "El padrón identifica al equipo pero aún no tiene documentos individualizados")
    for key in REQUIRED_BASE:
        if not counts[key]:
            flag("FALTA_"+key, "PENDIENTE", "No hay fuente de "+key+" identificada en el catálogo revisado")
    if not counts["TRABAJO"]:
        flag("TI_NO_VINCULADO", "PENDIENTE", "No se identificó versión final verificable de TI/TA en el inventario")
    if not counts["TURNITIN"]:
        flag("TURNITIN_NO_VINCULADO", "PENDIENTE", "Falta informe Turnitin relacionado con el TI/TA definitivo")
    if guide == "NO_CONFIRMADA":
        flag("GUIA_NO_CONFIRMADA", "PENDIENTE", "Determinar con resolución y documento institucional si aplica 018 o 088")
    if guide == "CONFLICTO_018_088":
        flag("GUIA_CONFLICTIVA", "REVISION", "Detectadas 018 y 088: resolver la guía aplicable antes de completar los formatos")
    if not style:
        flag("ESTILO_NO_CONFIRMADO", "PENDIENTE", "No se acreditó APA7, Vancouver o IEEE a partir de evidencias disponibles")
    if len(style) > 1:
        flag("ESTILO_CONFLICTIVO", "REVISION", "Las fuentes refieren varios estilos: "+", ".join(style))
    for rpt in reports:
        pct = rpt["percentages_named"]
        if len(pct) != 1:
            flag("TURNITIN_MULTIPLES_PORCENTAJES", "REVISION", rpt["name"])
        elif pct[0] > 20:
            flag("TURNITIN_SUPERA_20_HISTORICO", "REVISION", "Porcentaje nombrado "+str(pct[0])+"%; verificar versión final")
        ti_dates = sorted(filter(None, (_date(r["name"]) for r in rows if r["category"] == "TRABAJO")))
        if rpt["date_from_filename"] and ti_dates and rpt["date_from_filename"] < ti_dates[-1]:
            flag("TURNITIN_ANTERIOR_AL_TI", "REVISION", "Informe "+rpt["date_from_filename"]+" previo al TI "+ti_dates[-1])
    if not live:
        flag("COHERENCIA_CONTENIDO_PENDIENTE", "PENDIENTE",
             "Sin lectura del texto no es posible certificar título, DNI, ORCID, autores, asesor, jurado, firmas ni huellas")
    if counts["ACTA_SUSTENTACION"] == 0 and str(phase).upper() in ("F5", "F6"):
        flag("ACTA_SUSTENTACION_PENDIENTE", "REVISION", "La fase no prueba que exista un acta de sustentación válida")
    return {"group_id": str(group_id), "team": team, "program": program,
            "phase": phase, "validation_level": "METADATOS_Y_NOMBRES" if not live else "ARCHIVOS_ENUMERADOS_SIN_CERTIFICACION",
            "normative_guide": guide, "styles_detected": style, "family_counts": dict(counts),
            "turnitin_candidates": reports, "documents": rows, "issues": findings,
            "ready_for_institutional_release": False,
            "new_documents_generated": 0,
            "live_drive_read": bool(live),
            "verified_original_signatures": False,
            "verified_original_fingerprints": False}

def _csv(items, headings):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(headings)
    for row in items: writer.writerow(row)
    return stream.getvalue().encode("utf-8-sig")

def build_control_zip(report, originals=None, generated=None):
    """Entrega ZIP auditable. Originales solo si se pudieron bajar con autenticación."""
    gid = report["group_id"]
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("CONTROL/VALIDACION_CRUZADA.json", json.dumps(report, ensure_ascii=False, indent=2))
        z.writestr("CONTROL/DOCUMENTOS_EXISTENTES.csv", _csv(
            ([d["category"],d["id"],d["name"]," | ".join(d["urls"])] for d in report["documents"]),
            ["tipo","documento_id","archivo","enlaces_drive"]))
        z.writestr("CONTROL/OBSERVACIONES.csv", _csv(
            ([i["code"],i["severity"],i["detail"]] for i in report["issues"]),
            ["regla","severidad","observacion"]))
        z.writestr("LEER_PRIMERO.txt",
            "HAWKS expediente "+gid+"\n"
            "Estado: CONTROL DOCUMENTAL, NO EXPEDIENTE DEFINITIVO.\n"
            "Los enlaces Drive son a documentos fuente sin modificación.\n"
            "El diagnóstico de normativas, autores, Turnitin y firmas requiere cotejo del contenido.\n"
            "La generación de documentos faltantes necesita fuentes verificadas y plantillas oficiales.\n"
            "Ninguna firma o huella se crea o superpone automáticamente.\n")
        for i, entry in enumerate(originals or []):
            filename, contents = entry
            sanitized = NAME_RE.sub("_", PurePosixPath(filename).name)[:145]
            z.writestr("ORIGINALES/%03d_%s" % (i+1,sanitized), contents)
        for i, entry in enumerate(generated or []):
            filename, contents = entry
            sanitized = NAME_RE.sub("_", PurePosixPath(filename).name)[:145]
            z.writestr("GENERADOS_EN_REVISION/%03d_%s" % (i+1,sanitized), contents)
    return bio.getvalue()
