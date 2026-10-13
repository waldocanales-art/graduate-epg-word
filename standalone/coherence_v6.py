"""Coherencia documento-a-documento para expedientes EPG.

Pure functions: inputs come from a verified institutional extractor. Never
assume source values, substitute empty fields, or certify a signature image.
"""
from __future__ import annotations
import re
import unicodedata

COMPARE = ("TITLE", "PROGRAM", "GUIDE", "STYLE", "ADVISER", "JURY",
           "SUST_DATE", "VERDICT", "TURNITIN_VERSION")
AUTHOR_FIELDS = ("NAME", "DNI", "ORCID")
ORCID = re.compile(r"^\d{4}-\d{4}-\d{4}-[\dX]{4}$")
DNI = re.compile(r"^[0-9]{8}$")


def normalized(x):
    text = unicodedata.normalize("NFKD", str(x or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[\w]+", text.casefold()))


def _status(expected, observed):
    if not str(observed or "").strip(): return "SIN_EVIDENCIA"
    if not str(expected or "").strip(): return "SIN_CANONICO"
    return "COINCIDE" if normalized(expected) == normalized(observed) else "DIFERENTE"


def orcid_valid(raw):
    s = str(raw or "").replace("-", "").upper()
    if len(s) != 16 or not ORCID.fullmatch(str(raw or "").upper()):
        return False
    total=0
    for c in s[:15]:
        total=(total+int(c))*2
    check=(12-(total%11))%11
    return s[-1] == ("X" if check==10 else str(check))


def validate_extracted_sources(canonical, source_documents):
    """All fields require independent provenance; no output is a signed doc."""
    observations = []
    for doc in source_documents:
        doc_id = str(doc.get("document_id", "SIN_ID"))
        fields = doc.get("fields") or {}
        if not isinstance(fields, dict): continue
        for key in COMPARE:
            if key not in fields: continue
            expected = (canonical.get("fields") or {}).get(key)
            observed = fields.get(key)
            observations.append({
                "document_id": doc_id, "field": key,
                "status": _status(expected, observed),
                "source_id": doc.get("source_id"),
                "expected_present": bool(expected),
                "observed_present": bool(observed),
            })
        by_id={str(a.get("author_id")):a for a in canonical.get("authors",[]) if a.get("author_id")}
        for author in doc.get("authors",[]):
            author_id=str(author.get("author_id",""))
            ref=by_id.get(author_id)
            if not ref:
                observations.append({"document_id":doc_id,"field":"AUTHOR_ID",
                    "status":"AUTOR_NO_VINCULADO","source_id":doc.get("source_id")})
                continue
            for field in AUTHOR_FIELDS:
                if field not in author:continue
                obs=author.get(field)
                status=_status(ref.get(field),obs)
                if field=="DNI" and obs and not DNI.fullmatch(str(obs)):
                    status="DNI_FORMATO_INVALIDO"
                if field=="ORCID" and obs and not orcid_valid(str(obs)):
                    status="ORCID_FORMATO_O_CHECK_INVALIDO"
                observations.append({"document_id":doc_id,
                    "field":"AUTHOR_"+author_id+"_"+field,
                    "status":status,"source_id":doc.get("source_id")})
        if doc.get("requires_signature") and not doc.get("original_signed_source"):
            observations.append({"document_id":doc_id,"field":"SIGNATURE",
                                 "status":"NO_ACREDITADA","source_id":doc.get("source_id")})
        if doc.get("requires_fingerprint") and not doc.get("original_fingerprint_source"):
            observations.append({"document_id":doc_id,"field":"FINGERPRINT",
                                 "status":"NO_ACREDITADA","source_id":doc.get("source_id")})
    return {"checks":observations,
            "differences":[o for o in observations
                           if o["status"] not in ("COINCIDE",)],
            "new_documents_signed":0,
            "ready_for_release":False}
