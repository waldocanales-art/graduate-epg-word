"""Contrato de orquestación HAWKS: un solo número y un documento por operación.

No usa ni almacena datos personales; el expediente llega desde un
adaptador institucional privado que todavía debe integrarse.
"""
import re
from typing import Any, Mapping


class GroupLookupError(ValueError):
    pass


class SingleDocumentBlocked(ValueError):
    pass


def normalize_group_number(group_number: Any) -> str:
    """Acepta 29, '029' o ' 29 '; rechaza campos manuales y otros IDs."""
    if isinstance(group_number, bool):
        raise GroupLookupError("El número de grupo debe ser entero positivo")
    text = str(group_number).strip()
    if not re.fullmatch(r"[0-9]{1,9}", text):
        raise GroupLookupError("Introducir solo el número del grupo (máximo 9 dígitos)")
    number = int(text)
    if number == 0:
        raise GroupLookupError("El número de grupo debe ser mayor que cero")
    return str(number)


def group_document_menu(group_number: Any, resolved: Mapping[str, Any]) -> dict:
    """Genera lista por documento desde fuentes reales, no seis Word por defecto.

    resolved es el resultado de la consulta segura al padrón y a Drive/Gmail.
    No debe contener muestras de plantillas ni inferencias sin evidencia.
    """
    group_id = normalize_group_number(group_number)
    if normalize_group_number(resolved.get("group_id", "")) != group_id:
        raise GroupLookupError("El expediente devuelto no corresponde al grupo solicitado")
    if resolved.get("collision"):
        raise GroupLookupError("Colisión grupo/Drive: requiere conciliación de fuente")
    status_allowed = {
        "ORIGINAL_EN_DRIVE", "DATOS_RECUPERADOS", "LISTO_PARA_GENERAR",
        "BORRADOR_GENERADO", "GENERADO_EN_REVISION", "APTO_REPOSITORIO",
        "PENDIENTE_FUENTE", "VERSION_TURNITIN_NO_COINCIDE", "DOCUMENTO_NO_APLICA"
    }
    result = []
    used = set()
    for doc in resolved.get("documents", []):
        doc_id = str(doc.get("document_id", "")).strip()
        if not doc_id or doc_id in used:
            raise GroupLookupError("Inventario contiene un ID documental vacío o repetido")
        used.add(doc_id)
        status = doc.get("status", "PENDIENTE_FUENTE")
        if status not in status_allowed:
            raise GroupLookupError("Estado documental no reconocido")
        result.append({
            "document_id": doc_id, "kind": str(doc.get("kind", "")),
            "author_ref": doc.get("author_ref"),
            "status": status,
            "source_ref": doc.get("source_ref"),
            "ready_for_one_action": status in {
                "ORIGINAL_EN_DRIVE", "LISTO_PARA_GENERAR",
                "GENERADO_EN_REVISION", "APTO_REPOSITORIO"
            }
        })
    return {"group_id": group_id, "documents": result, "total": len(result)}


def select_single_document(menu: Mapping[str, Any], document_id: str) -> dict:
    """Devuelve UNA solicitud; no firma, no emite actas, no genera el resto."""
    matches = [
        doc for doc in menu.get("documents", [])
        if doc.get("document_id") == document_id
    ]
    if len(matches) != 1:
        raise SingleDocumentBlocked("Documento no localizado inequívocamente")
    doc = matches[0]
    if not doc.get("ready_for_one_action"):
        raise SingleDocumentBlocked(
            "Faltan fuentes verificadas para este documento. Los demás siguen disponibles."
        )
    return {"group_id": menu["group_id"], "document_id": document_id,
            "action": "DOWNLOAD_ORIGINAL" if doc["status"] == "ORIGINAL_EN_DRIVE"
                      else "GENERATE_ONE_DOCUMENT"}
