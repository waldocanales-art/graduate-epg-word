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
