"""Resolución de evidencias originales en el expediente EPG.

Este módulo NO firma documentos ni modifica firmas/huellas; localiza evidencia
preexistente del mismo titular y equipo para evitar solicitarla de nuevo.
No almacenar bytes biométricos en GitHub ni en registros.
"""
from collections import defaultdict


def resolve_existing_evidence(group_id, authors, evidence_items):
    """Devuelve referencias de firmas, huellas y pendientes por autor.

    Los documentos originales deben tener group_id, author_id, kind,
    source_id y provenance_verified=True tras reconciliación institucional.
    """
    out = {"group_id": str(group_id), "authors": {}, "exceptions": []}
    matched = defaultdict(list)
    for ev in evidence_items:
        if not isinstance(ev, dict):
            continue
        if str(ev.get("group_id", "")) != str(group_id):
            continue
        if ev.get("kind") not in {"signature", "fingerprint"}:
            continue
        if not ev.get("source_id") or ev.get("provenance_verified") is not True:
            continue
        matched[(str(ev.get("author_id", "")), ev["kind"])].append(ev)
    for author in authors:
        author_id = str(author.get("author_id", ""))
        if not author_id:
            out["exceptions"].append("Autor sin identificador canónico")
            continue
        entry = {}
        for kind in ("signature", "fingerprint"):
            sources = matched.get((author_id, kind), [])
            # No usar evidencia cruzada de otra persona o grupo; preservar
            # una referencia al archivo original, no una imagen aislada.
            sources = sorted(sources, key=lambda s: (str(s.get("verified_at", "")), str(s["source_id"])), reverse=True)
            entry[kind] = {
                "available": bool(sources),
                "source_id": sources[0]["source_id"] if sources else None,
                "source_document_id": sources[0].get("source_document_id") if sources else None,
                "status": "RECOVERED_EXISTING" if sources else "MISSING_SOURCE",
            }
            if not sources:
                out["exceptions"].append(f"{author_id}: evidencia {kind} no localizada")
        out["authors"][author_id] = entry
    return out
