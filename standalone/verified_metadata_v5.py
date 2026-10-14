"""HAWKS V5 metadata DOCX generation with verifiable private group fields.

A newly generated Word is never presented as signed or institutionally approved.
The service uses its configured template, which may predate Liz's September version.
"""
from __future__ import annotations
import io, os, json, unicodedata, zipfile
from docx import Document
from pathlib import Path

def _n(s):
    t=unicodedata.normalize("NFD",str(s or ""))
    return "".join(x for x in t if unicodedata.category(x)!="Mn").upper().strip()

def profiles():
    raw=os.getenv("HAWKS_V5_VERIFIED_METADATA_JSON","")
    if not raw:return {}
    obj=json.loads(raw)
    if not isinstance(obj,dict):raise ValueError("Perfil verificado inválido")
    return obj

def eligible(group_id):
    d=profiles().get(str(group_id))
    return isinstance(d,dict) and len(d.get("authors",[])) in (1,2,3) and bool(d.get("research",{}).get("title"))

def _fill(cell,value):
    p=cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
    if p.runs:
        p.runs[0].text=str(value)
        p.runs[0].font.bold=False
        for r in p.runs[1:]:r.text=""
    else:p.add_run(str(value))
    for p in cell.paragraphs[1:]:
        for r in p.runs:r.text=""

def _remove_body_callouts(doc):
    """Remove ONLY embedded Liz instructional text callouts, preserving branding."""
    removed=0
    for element in list(doc.element.body.xpath('.//*[local-name()="AlternateContent"]')):
        texts=" ".join(x.text or "" for x in element.xpath('.//*[local-name()="t"]'))
        normalized=_n(texts)
        if any(marker in normalized for marker in (
            "COLOCAR LOS DATOS", "COLOCAR EL TITULO",
            "EL OCDE ES DIFERENTE", "REVISAR SI EN EL DNI"
        )):
            element.getparent().remove(element)
            removed+=1
    # Algunas anotaciones están ancladas en celdas que desaparecen al
    # reemplazar texto; no exigir un número fijo de overlays eliminados.
    for element in doc.element.body.xpath('.//*[local-name()="AlternateContent"]'):
        texts=" ".join(x.text or "" for x in element.xpath('.//*[local-name()="t"]'))
        normalized=_n(texts)
        if any(marker in normalized for marker in (
            "COLOCAR LOS DATOS", "COLOCAR EL TITULO",
            "EL OCDE ES DIFERENTE", "REVISAR SI EN EL DNI"
        )):
            raise ValueError("Persisten indicaciones de Liz superpuestas al contenido")
    return removed

def generate_metadata(group_id,template_path):
    item=profiles().get(str(group_id))
    if not item:raise ValueError("No hay campos documentales cotejados para este grupo")
    authors=item.get("authors",[])
    if len(authors) not in (1,2,3):raise ValueError("Cantidad de autores sin verificar")
    from .liz_template_loader_v7 import validate_official_template
    if not isinstance(template_path, bytes):
        raise ValueError("La plantilla debe provenir del original autorizado de Liz en Drive")
    validate_official_template(template_path, len(authors))
    doc=Document(io.BytesIO(template_path))
    author_idx=-1;mode="";jury="";filled=[]
    for table in doc.tables:
        for row in table.rows:
            if len(row.cells)<2:continue
            label=_n(row.cells[0].text)
            if "DATOS DEL AUTOR" in label:
                author_idx+=1;mode="author";jury="";continue
            if "DATOS DEL ASESOR" in label:mode="adviser";jury="";continue
            if "DATOS DEL JURADO" in label:mode="jury";jury="";continue
            if "PRESIDENTE DEL JURADO" in label:jury="president";continue
            if "SECRETARIO DEL JURADO" in label:jury="secretary";continue
            if "VOCAL DEL JURADO" in label:jury="vocal";continue
            if "DATOS DE LA INVESTIGACION" in label:mode="research";jury="";continue
            if mode=="author":entry=authors[author_idx] if author_idx<len(authors) else {}
            elif mode=="adviser":entry=item.get("adviser",{})
            elif mode=="jury":entry=item.get("jury",{}).get(jury,{})
            elif mode=="research":entry=item.get("research",{})
            else:continue
            field=None
            if "NOMBRES Y APELLIDOS" in label:field="name"
            elif "TIPO DE DOCUMENTO" in label:field="document_type"
            elif "NUMERO DE DOCUMENTO" in label:field="document_number"
            elif "URL DE ORCID" in label:field="orcid"
            elif mode=="research":
                if "TITULO DE LA INVESTIGACION" in label:field="title"
                elif "LINEA DE INVESTIGACION INSTITUCIONAL" in label:field="institutional_line"
                elif "LINEA DE INVESTIGACION DEL PROGRAMA" in label:field="program_line"
                elif "LINEA DE ACCION RSU" in label:field="rsu_line"
                elif "URL DE DISCIPLINAS OCDE" in label:field="ocde"
            if field:
                value=entry.get(field)
                if not value or not str(value).strip():
                    raise ValueError("Dato no verificado para "+mode+"."+field)
                _fill(row.cells[1],value)
                filled.append((mode,field))
    expected_count=4*len(authors)+4+9+5
    if len(filled)!=expected_count or author_idx+1!=len(authors) or not any(f=="title" for _,f in filled):
        raise ValueError("La plantilla no permitió sustituir TODOS los campos verificados; documento bloqueado")
    _remove_body_callouts(doc)
    stream=io.BytesIO();doc.save(stream);payload=stream.getvalue()
    check=Document(io.BytesIO(payload))
    text="\n".join(c.text for t in check.tables for r in t.rows for c in r.cells)
    needed=[a["name"] for a in authors]+[item["research"]["title"]]
    if any(x not in text for x in needed):
        raise ValueError("Campos del expediente no aparecen en el Word generado")
    return payload, {"fields_replaced":len(filled),"author_count":len(authors),
       "source":"Formato oficial de Liz obtenido de Drive (archivo validado por SHA256)",
       "status":"GENERATED_PENDING_INSTITUTIONAL_REVIEW",
       "template_variant":"LIZ_ORIGINAL_2026_09_VERIFIED",
       "note":"Relleno automático de plantilla Liz con datos cotejados; requiere revisión institucional. Ninguna firma o huella se ha simulado."}
