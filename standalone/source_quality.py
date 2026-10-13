"""Validación de fuente para expedientes HAWKS sin datos inventados."""
import re

def validate_expedient(data):
    issues=[]
    def err(code,detail):
        issues.append({"code":code,"detail":detail})
    typ=data.get("program_type")
    if typ not in {"TI","TA"}:err("PROGRAM_TYPE","Definir TI maestría o TA segunda especialidad")
    authors=data.get("authors") or []
    if not 1<=len(authors)<=3:err("AUTHORS_COUNT","Se requieren 1 a 3 autores comprobados")
    for i,a in enumerate(authors,1):
        if not a.get("name") or not a.get("dni"):err("AUTHOR_IDENTITY",f"Autor {i}: nombre y DNI")
        if not a.get("orcid"):err("AUTHOR_ORCID",f"Autor {i}: ORCID")
        if not a.get("signature_source"):err("AUTHOR_SIGNATURE",f"Autor {i}: firma auténtica y origen")
        if not a.get("fingerprint_source"):err("AUTHOR_FINGERPRINT",f"Autor {i}: huella auténtica y origen")
    adviser=data.get("adviser") or {}
    for k in ("name","dni","orcid"):
        if not adviser.get(k):err("ADVISER_"+k.upper(),k)
    jury=data.get("jury") or {}
    for role in ("president","secretary","vocal"):
        if not (jury.get(role) or {}).get("name"):err("JURY_"+role.upper(),role)
    research=data.get("research") or {}
    for k in ("title","institutional_line","program_line","rsu_action_line"):
        if not research.get(k):err("RESEARCH_"+k.upper(),k)
    if len(research.get("ocde_disciplines") or [])!=2:err("OCDE","Se requieren dos disciplinas OCDE comprobadas")
    t=data.get("turnitin") or {}
    for k in ("percent","report_date","version_hash","report_source"):
        if t.get(k) is None or t.get(k)=="":err("TURNITIN_"+k.upper(),k)
    if isinstance(t.get("percent"),(float,int)) and t["percent"]>20:err("TURNITIN_LIMIT","Similitud >20%")
    publication=data.get("publication") or {}
    if publication.get("choice") not in ("open","embargo","restricted"):
        err("PUBLICATION_CHOICE","Opción por autor sin seleccionar")
    if publication.get("choice")=="embargo" and not publication.get("embargo_until"):
        err("EMBARGO_DATE","Falta fecha del embargo autorizado")
    return {"ready":not issues,"issues":issues}
