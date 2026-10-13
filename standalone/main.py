"""HAWKS Documentos V3: API autónoma, sin alterar el renderer V1 ni n8n."""
import base64
import json
import os
import secrets
from io import BytesIO

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from docx import Document
from app import RenderRequest, TEMPLATES, render as legacy_render
from document_quality import audit_document

app = FastAPI(title="HAWKS Documentos V3 (experimental)", version="3.0.0-rc1")

def auth(x_api_key):
    expected = os.environ.get("DOCUMENTOS_V3_API_KEY")
    if not expected:
        raise HTTPException(503, "Falta configurar DOCUMENTOS_V3_API_KEY")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(401, "Acceso no autorizado")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).with_name("index.html"), media_type="text/html")

@app.get("/health")
def health():
    return {"ok": True, "service": "hawks-documentos-v3", "templates": sorted(TEMPLATES)}

@app.post("/v3/documents/render")
def render(req: RenderRequest, x_api_key: str | None = Header(default=None)):
    auth(x_api_key)
    key = req.template_key.upper().strip()
    if key not in TEMPLATES:
        raise HTTPException(400, "Plantilla no soportada")
    # No emitir documentos que requieran firmas o huellas sin evidencia real provista.
    # Jamás crear, reutilizar arbitrariamente ni simular firmas/huellas.
    signer_docs = {"DECLARACION_JURADA", "DECLARACION_ORIGINALIDAD",
                   "AUTORIZACION_PUBLICACION", "ACTA_SUSTENTACION", "ACTA_ORIGINALIDAD"}
    image_keys = {str(k).upper().removeprefix("IMG_") for k in req.images}
    if key in signer_docs:
        author_count = (3 if key == "METADATA_3" else 2 if key == "METADATA_2" else
                        int(req.fields.get("AUTHOR_COUNT") or 1))
        if author_count < 1 or author_count > 3:
            raise HTTPException(422, "AUTHOR_COUNT debe estar entre 1 y 3")
        required_signatures = (
            {f"AUTHOR{i}_SIGNATURE" for i in range(1, author_count + 1)}
            if author_count > 1 else {"AUTHOR_SIGNATURE"}
        )
        if key.startswith("ACTA_"):
            required_signatures = {"JURY_PRESIDENT_SIGNATURE", "JURY_SECRETARY_SIGNATURE",
                                   "JURY_VOCAL_SIGNATURE"}
        missing = sorted(required_signatures - image_keys)
        if missing:
            raise HTTPException(422, {"status": "MISSING_AUTHENTIC_SIGNATURES",
                                       "required_images": missing})
    if key == "DECLARACION_JURADA":
        count = int(req.fields.get("AUTHOR_COUNT") or 1)
        required_prints = ({f"AUTHOR{i}_FINGERPRINT" for i in range(1, count + 1)}
                           if count > 1 else {"AUTHOR1_FINGERPRINT"})
        missing_prints = sorted(required_prints - image_keys)
        if missing_prints:
            raise HTTPException(422, {"status": "MISSING_AUTHENTIC_FINGERPRINTS",
                                       "required_images": missing_prints})
    # API aislada reutiliza motor V1 sin editarlo; audita el resultado antes de devolverlo.
    response = legacy_render(req)
    output = json.loads(response.body)
    raw = base64.b64decode(output["docx_base64"], validate=True)
    from pathlib import Path
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as td:
        path = Path(td) / "resultado.docx"
        path.write_bytes(raw)
        audit = audit_document(path, key, req.fields, req.images)
    output["quality"] = audit
    # Política estricta: un documento incompleto no se declara listo.
    if not audit["ok"]:
        output["ok"] = False
        output["status"] = "REJECTED_QUALITY"
        # No devolver archivo listo para distribución si la validación detecta errores.
        output["docx_base64"] = None
        output["pdf_base64"] = None
        return JSONResponse(output, status_code=422)
    if req.make_pdf and not output.get("pdf_generated"):
        output["ok"] = False
        output["status"] = "PDF_NOT_GENERATED"
        output["docx_base64"] = None
        output["pdf_base64"] = None
        return JSONResponse(output, status_code=422)
    output["status"] = "GENERATED_PENDING_INSTITUTIONAL_REVIEW"
    return JSONResponse(output)


# HAWKS V5 — consulta de control por número de grupo (instantánea privada)
# No configura Drive/Gmail en Render ni da documentos por firmados.
import re as _re
import zlib as _zlib
from .document_actions_v5 import document_rows, selected_document, read_private_catalog
from .verified_metadata_v5 import generate_metadata, eligible, profiles
from .metadata_fallback_v5 import new_metadata
from app import TEMPLATE_DIR

_DOCUMENT_TYPES_V5 = [
    ("METADATOS", "Hoja de metadatos"),
    ("DECLARACION_JURADA", "Declaración jurada de autoría"),
    ("DECLARACION_ORIGINALIDAD", "Declaración de originalidad"),
    ("AUTORIZACION_PUBLICACION", "Autorización de publicación"),
    ("ACTA_ORIGINALIDAD", "Acta de originalidad"),
    ("ACTA_SUSTENTACION", "Acta de sustentación"),
]

def _v5_index():
    """Índice no público: solo proviene de variable de entorno privada Render."""
    raw = os.getenv("HAWKS_V5_GROUP_INDEX_ZLIB_B64", "") or "".join(os.getenv(f"HAWKS_V5_INDEX_PART{i}", "") for i in range(3))
    if not raw:
        return {}
    try:
        data = json.loads(_zlib.decompress(base64.b64decode(raw, validate=True)))
        if isinstance(data, dict) and "groups" in data:
            names, statuses = data.get("programs", []), data.get("statuses", [])
            return {
                gid: [v[0], names[v[1]], "F" + str(v[2]), v[3], statuses[v[4]],
                      "Carpeta candidata localizada; revisar documentos originales de Drive."]
                for gid, v in data["groups"].items()
                if isinstance(v, list) and len(v) >= 5
            }
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError, OSError):
        raise HTTPException(503, "Índice de grupos no legible; revisar configuración de Render")

def _v5_group(group_number):
    if not _re.fullmatch(r"[0-9]{1,9}", str(group_number).strip()) or int(group_number) < 1:
        raise HTTPException(422, "Escribe solamente el número del grupo")
    return str(int(group_number))

def _v5_documents(gid):
    rows = document_rows(gid)
    if eligible(gid):
        count = len(profiles()[gid]["authors"])
        found = False
        for row in rows:
            if row["id"].startswith("METADATA"):
                row["can_generate_new"] = True
                row["generation_status"] = "NUEVO_WORD_EN_REVISION"
                found = True
        if not found:
            rows.insert(0, {"id": "METADATA_" + str(count),
                            "name": "Hoja de metadatos · " + str(count) + " autores",
                            "status": "LISTO_PARA_BORRADOR",
                            "can_download": False,
                            "can_generate_new": True})
    return rows

@app.get("/v5/groups/{group_number}")
def lookup_group_v5(group_number: str, x_api_key: str | None = Header(default=None)):
    auth(x_api_key)
    group_id = _v5_group(group_number)
    index = _v5_index()
    if not index:
        raise HTTPException(503, "Catálogo todavía no sincronizado. El servicio no tiene acceso a Drive/Gmail.")
    item = index.get(group_id)
    if not item:
        raise HTTPException(404, "Grupo no encontrado en los 84 registros de control; no se inventarán sus datos.")
    if not isinstance(item, list) or len(item) < 6:
        raise HTTPException(503, "Entrada de control incompleta")
    name, program, phase, folder_id, source_status, findings = item[:6]
    folder_url = "https://drive.google.com/drive/folders/" + folder_id if folder_id else None
    return {
        "ok": True,
        "group_id": group_id,
        "team": name,
        "program": program,
        "phase": phase,
        "folder_url": folder_url,
        "source_status": source_status,
        "findings": findings,
        "snapshot_date": "2026-10-13",
        "live_drive_connected": False,
        "generation_ready": False,
        "documents": _v5_documents(group_id),
        "notice": "Esta es una instantánea de expedientes localizados. Los datos definitivos y el Word oficial requieren conectar las fuentes institucionales en el servidor."
    }

@app.get("/v5/groups/{group_number}/documents")
def list_group_docs_v5(group_number: str, x_api_key: str | None = Header(default=None)):
    auth(x_api_key)
    gid = _v5_group(group_number)
    if gid not in _v5_index():
        raise HTTPException(404, "Grupo no identificado")
    return {"group_id": gid, "documents": _v5_documents(gid)}


@app.post("/v5/groups/{group_number}/documents/{document_id}/generate")
def generate_one_v5(group_number: str, document_id: str, x_api_key: str | None = Header(default=None)):
    """Recupera 1 original auténtico: enlaces Word/PDF, nunca finge firmar."""
    auth(x_api_key)
    group_id = _v5_group(group_number)
    if group_id not in _v5_index():
        raise HTTPException(404, "Grupo no encontrado en el padrón")
    try:
        doc = selected_document(group_id, document_id)
    except (LookupError, ValueError):
        raise HTTPException(404, "No hay documento inequívoco para este grupo")
    if not doc["can_download"]:
        raise HTTPException(409, {
            "status": "PENDIENTE_EVIDENCIA",
            "group_id": group_id, "document_id": document_id,
            "detail": "No existe enlace de Word/PDF auténtico verificado. Revisar expediente, no inventar firmas, huellas ni actas."
        })
    return {
        "ok": True,
        "group_id": group_id, "document_id": document_id,
        "status": "ORIGINAL_RECUPERABLE",
        "mode": "PRESERVE_EXISTING_DOCUMENT",
        "word_url": doc["word_url"],
        "pdf_url": doc["pdf_url"],
        "message": "Documento ya entregado al expediente. Abre/descarga su original de Drive: no se reemplaza una firma ni se modifica el contenido.",
        "new_word_generated": False
    }


def _render_verified_metadata(gid, count):
    # Try institutional-style installed template first, then a transparent,
    # explicitly provisional reconstructed layout if it is incompatible.
    try:
        return generate_metadata(gid, TEMPLATE_DIR / TEMPLATES["METADATA_" + str(count)])
    except (ValueError, OSError, KeyError):
        return new_metadata(gid, profiles()[gid])


@app.post("/v5/groups/{group_number}/documents/{document_id}/generate-word")
def generate_word_v5(group_number: str, document_id: str, x_api_key: str | None = Header(default=None)):
    """Real Word generation with current installed template, pending Liz QA."""
    auth(x_api_key)
    gid = _v5_group(group_number)
    if gid not in _v5_index():
        raise HTTPException(404, "Equipo fuera del padrón")
    if not eligible(gid):
        raise HTTPException(409, "No hay suficientes campos originales cotejados; no se generan datos inventados")
    count = len(profiles()[gid]["authors"])
    if not document_id.startswith("METADATA") or (
        document_id.startswith("METADATA_") and
        document_id[9:].isdigit() and int(document_id[9:]) != count
    ):
        raise HTTPException(409, "Solo metadatos, con la cantidad auténtica de autores, está habilitado para nuevo Word")
    template = TEMPLATE_DIR / TEMPLATES["METADATA_" + str(count)]
    try:
        payload, qa = _render_verified_metadata(gid, count)
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(409, {"status":"DOCUMENT_NOT_GENERATED", "detail":str(exc)})
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition":'attachment; filename="HAWKS_EPG_'+gid+'_METADATOS_BORRADOR.docx"',
                 "Cache-Control":"private, no-store",
                 "X-HAWKS-DOCUMENT-STATUS":"BORRADOR_PENDIENTE_REVISION",
                 "X-HAWKS-FIELDS-REPLACED":str(qa["fields_replaced"]),
                 "X-HAWKS-TEMPLATE-STATUS":str(qa.get("template_variant","INSTALLED_TEMPLATE_PENDING_LIZ_QA"))}
    )


@app.get("/v5/generation-health")
def generation_health_v5():
    """Non-sensitive self-test; never returns author data or bytes."""
    tested={}
    for gid, profile in profiles().items():
        count=len(profile.get("authors", []))
        if count not in (1,2,3):continue
        try:
            binary,qa=_render_verified_metadata(gid,count)
            tested[gid]={"generates_docx":binary[:2]==b"PK",
                         "bytes":len(binary),"filled_fields":qa["fields_replaced"],"template_variant":qa.get("template_variant","INSTALLED_TEMPLATE_PENDING_LIZ_QA")}
        except Exception as exc:
            tested[gid]={"generates_docx":False,"error_type":type(exc).__name__, "error_detail":str(exc)[:160]}
    return {"ok":all(x["generates_docx"] for x in tested.values()),
            "groups_with_verified_metadata":len(tested),
            "tests":tested,
            "official_2026_09_template_verified":False}


@app.get("/v5/index-health")
def index_health_v5():
    """Diagnóstico no sensible: confirma tamaño de índice, nunca expone datos."""
    try:
        index = _v5_index()
        docs = read_private_catalog()
        # Verifica estructura, IDs y URLs de cada documento sin exponer PII.
        broken = []
        for gid in docs:
            try:
                document_rows(gid, docs)
            except (ValueError, TypeError, KeyError):
                broken.append(gid)
        return {"ok": len(index) == 84 and not broken,
                "indexed_groups": len(index),
                "catalogued_document_groups": len(docs),
                "document_sources_catalogued": sum(len(v) for v in docs.values() if isinstance(v, list)),
                "invalid_document_groups": len(broken),
                "snapshot_date": "2026-10-13",
                "live_drive_connected": False}
    except HTTPException:
        return JSONResponse({"ok": False, "indexed_groups": 0,
                             "status": "INDEX_UNREADABLE"}, status_code=503)


# V6: generar paquete de control de todas las fuentes del grupo.
# No se declara concluida la generación oficial mientras no se tenga lectura
# autorizada del contenido de TI, resoluciones y plantillas de Liz.
from .batch_v6 import audit_group, build_control_zip
from fastapi.responses import Response

def _v6_report(group_number):
    gid = _v5_group(group_number)
    index = _v5_index()
    if gid not in index:
        raise HTTPException(404, "Grupo no encontrado en el padrón de control")
    team, program, phase = index[gid][:3]
    docs = document_rows(gid)
    report = audit_group(gid, team, program, phase, docs)
    # Auditorías de contenido REAL realizadas en una sesión institucional
    # pueden adjuntarse vía variable privada de Render, sin copiar PII a GitHub.
    try:
        reviews = json.loads(os.environ.get("HAWKS_V6_REVIEWED_CONTENT_JSON", "{}"))
        reviewed = reviews.get(gid)
    except (ValueError, AttributeError):
        reviewed = None
    if isinstance(reviewed, dict):
        report["validation_level"] = "COTEJO_PARCIAL_DE_CONTENIDO"
        report["partially_cross_checked"] = reviewed.get("checks", [])
        report["review_scope"] = reviewed.get("scope", "")
        guide = reviewed.get("guide")
        if guide:
            report["normative_guide"] = guide
            report["issues"] = [x for x in report["issues"] if x["code"] != "GUIA_NO_CONFIRMADA"]
        style = reviewed.get("style")
        if isinstance(style, str) and style:
            report["styles_detected"] = [style]
            report["issues"] = [x for x in report["issues"] if x["code"] != "ESTILO_NO_CONFIRMADO"]
        for item in reviewed.get("checks", []):
            if item.get("status") in ("OBSERVACION", "REVISAR", "PENDIENTE"):
                report["issues"].append({
                    "code": item.get("code","COTEJO"),
                    "severity": "REVISION",
                    "detail": item.get("description","Verificar discrepancia de documentos")
                })
    # Contraste de campos: cuando el extractor institucional aporte
    # fuentes probadas, aplica comparaciones estrictas documento a documento.
    try:
        field_snapshots = json.loads(os.environ.get("HAWKS_V6_EXTRACTED_FIELDS_JSON", "{}"))
        field_group = field_snapshots.get(gid)
    except (ValueError, AttributeError):
        field_group = None
    if isinstance(field_group, dict):
        from .coherence_v6 import validate_extracted_sources
        comparison = validate_extracted_sources(
            field_group.get("canonical", {}), field_group.get("documents", []))
        report["field_level_comparison"] = comparison
        for difference in comparison["differences"]:
            report["issues"].append({
                "code": "DIFERENCIA_"+str(difference.get("field", "")),
                "severity": "REVISION",
                "detail": "Documento "+str(difference.get("document_id",""))+
                          ": "+str(difference.get("status",""))
            })
    return report

@app.get("/v6/groups/{group_number}/audit")
def audit_group_v6(group_number: str, x_api_key: str | None = Header(default=None)):
    auth(x_api_key)
    return _v6_report(group_number)

@app.post("/v6/groups/{group_number}/generate-all")
def generate_all_v6(group_number: str, x_api_key: str | None = Header(default=None)):
    auth(x_api_key)
    report = _v6_report(group_number)
    generated = []
    gid = report["group_id"]
    if eligible(gid):
        try:
            count = len(profiles()[gid]["authors"])
            payload, qa = _render_verified_metadata(gid, count)
            generated.append(("HAWKS_EPG_"+gid+"_METADATOS_BORRADOR.docx",payload))
            report["new_documents_generated"] = 1
            report["generated_file_status"] = qa["status"]
            report["generated_template_variant"] = qa.get("template_variant", "INSTALLED_TEMPLATE_PENDING_LIZ_QA")
            report["issues"].append({"code":"GENERATED_DRAFT_PENDING_LIZ_QA","severity":"REVISION",
                "detail":"Word nuevo generado y entregado como borrador. Revisar la plantilla de Liz antes de liberar al repositorio."})
        except Exception:
            report["issues"].append({"code":"GENERATION_FAILED","severity":"PENDIENTE",
                "detail":"La construcción del Word no se completó; revisar campos e instalación de plantilla."})
    content = build_control_zip(report, generated=generated)
    filename = "HAWKS_EPG_" + report["group_id"] + "_CONTROL_Y_CRUCES.zip"
    return Response(content, media_type="application/zip",
                    headers={
                        "Content-Disposition": 'attachment; filename="' + filename + '"',
                        "Cache-Control": "no-store",
                        "X-HAWKS-Release-Status": "CONTROL_ONLY_NOT_FINAL_DOCUMENTS",
                    })



@app.get("/v6/self-test")
def batch_selftest_v6():
    """Sin datos personales. Verifica motor ZIP, reglas y seguridad básica."""
    import io
    import zipfile
    sample = audit_group("999", "EQUIPO DE PRUEBA", "MAESTRIA", "F4", [])
    package = build_control_zip(sample)
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        valid = archive.testzip() is None
        files = archive.namelist()
    return {"ok": valid and not sample["ready_for_institutional_release"],
            "report_files": len(files), "issues_found": len(sample["issues"]),
            "unsupported_compliance_claims": sample["ready_for_institutional_release"],
            "document_generation_enabled": False}
