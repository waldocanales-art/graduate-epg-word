"""Conexión de solo lectura HAWKS → Google Drive por cuenta de servicio.

Credenciales exclusivamente por variable de entorno privada en Render.
No transfiere tokens de ChatGPT ni habilita modificaciones de archivos.
"""
import json
import os
import re
from collections import deque

FOLDER_ID = re.compile(r"^[A-Za-z0-9_-]{10,128}$")
FOLDER_MIME = "application/vnd.google-apps.folder"
DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
SCOPE = "https://www.googleapis.com/auth/drive.readonly"


class DriveConnectionError(Exception):
    pass


def connection_status():
    raw = os.getenv("HAWKS_DRIVE_SA_JSON", "")
    result = {"configured": bool(raw), "mode": "SERVICE_ACCOUNT_READ_ONLY",
              "source": "GOOGLE_DRIVE", "access_confirmed": False}
    if not raw:
        result["status"] = "CREDENTIALS_NOT_CONFIGURED"
        return result
    try:
        config = json.loads(raw)
        if config.get("type") != "service_account" or not config.get("client_email"):
            raise ValueError("Invalid account type")
        result["service_account_email"] = config["client_email"]
        result["status"] = "CREDENTIALS_PRESENT_NOT_YET_TESTED"
    except (ValueError, TypeError, AttributeError):
        result["status"] = "INVALID_SERVICE_ACCOUNT_JSON"
    return result


def _session():
    raw = os.getenv("HAWKS_DRIVE_SA_JSON", "")
    if not raw:
        raise DriveConnectionError("Configurar HAWKS_DRIVE_SA_JSON en Render (Environment), sin enviarla por chat")
    try:
        payload = json.loads(raw)
        if payload.get("type") != "service_account":
            raise ValueError("Tipo inválido")
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
        credentials = service_account.Credentials.from_service_account_info(
            payload, scopes=[SCOPE])
        return AuthorizedSession(credentials)
    except (ValueError, KeyError, TypeError) as exc:
        raise DriveConnectionError("La credencial Drive de Render no tiene formato válido") from exc


def _request(session, url, params):
    try:
        response = session.get(url, params=params, timeout=(7, 25))
        if response.status_code in (401, 403):
            raise DriveConnectionError("Cuenta de servicio sin permiso de lectura; comparte la carpeta EPG con su correo")
        if response.status_code == 404:
            raise DriveConnectionError("Carpeta no accesible o inexistente para la cuenta de servicio")
        response.raise_for_status()
        return response.json()
    except DriveConnectionError:
        raise
    except Exception as exc:
        raise DriveConnectionError("No se pudo consultar Google Drive; revisar conectividad y permisos") from exc


def list_folder_tree(folder_id, *, max_files=160, max_depth=3, session=None):
    """Solo nombres y metadatos; nunca descarga archivos ni escribe en Drive."""
    if not FOLDER_ID.fullmatch(str(folder_id)):
        raise DriveConnectionError("Identificador de carpeta inválido en el índice institucional")
    if not 1 <= max_files <= 300 or not 0 <= max_depth <= 5:
        raise DriveConnectionError("Límites de consulta inválidos")
    session = session or _session()
    root = _request(session, DRIVE_FILES_URL + "/" + folder_id,
                    {"fields": "id,name,mimeType", "supportsAllDrives": "true"})
    if root.get("mimeType") != FOLDER_MIME:
        raise DriveConnectionError("El vínculo asignado al grupo no es una carpeta")
    pending = deque([(folder_id, 0)])
    visited = set()
    files = []
    truncated = False
    while pending:
        if len(visited) >= 80:
            truncated = True
            break
        parent, depth = pending.popleft()
        if parent in visited:
            continue
        visited.add(parent)
        next_page = None
        while True:
            data = _request(session, DRIVE_FILES_URL, {
                "q": "'" + parent + "' in parents and trashed = false",
                "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime,webViewLink,md5Checksum)",
                "pageSize": 100,
                "pageToken": next_page or "",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
                "orderBy": "name"
            })
            for item in data.get("files", []):
                if item.get("mimeType") == FOLDER_MIME:
                    if depth < max_depth and len(visited) + len(pending) < 80:
                        pending.append((item["id"], depth + 1))
                    else:
                        truncated = True
                    continue
                if len(files) >= max_files:
                    truncated = True
                    break
                files.append({
                    "id": item.get("id"), "name": item.get("name"),
                    "mime_type": item.get("mimeType"),
                    "bytes": int(item["size"]) if item.get("size") else None,
                    "modified_time": item.get("modifiedTime"),
                    "md5_checksum": item.get("md5Checksum"),
                    "url": item.get("webViewLink")
                })
            if truncated:
                break
            next_page = data.get("nextPageToken")
            if not next_page:
                break
        if truncated:
            break
    return {"root_folder_id": folder_id, "files": files,
            "file_count": len(files), "truncated": truncated,
            "read_only": True, "content_verified": False,
            "identity_linkage_verified": False,
            "notice": "Inventario real de Drive; falta cotejar grupo↔carpeta y contenido de originales antes de emitir formatos oficiales"}
