# GRADUATE EPG Word Renderer V1

Servicio para recibir datos canónicos desde n8n y poblar los formatos Word institucionales sin reconstruirlos dentro del Code node.

## Endpoint
`POST /v1/word/render`

Payload mínimo:
```json
{
  "template_key": "ACTA_SUSTENTACION",
  "group_id": "G023",
  "fields": {
    "PROGRAM": "Maestría en ...",
    "TITLE": "Título definitivo",
    "AUTHORS_LABEL": "los bachilleres",
    "AUTHORS_DISPLAY": "APELLIDOS Y NOMBRES",
    "GRADE": "Maestro",
    "VERDICT": "APROBADO",
    "SCORE": "18",
    "SUST_DATE_LONG": "20 de septiembre de 2026",
    "JURY_PRESIDENT_NAME": "...",
    "JURY_SECRETARY_NAME": "...",
    "JURY_VOCAL_NAME": "..."
  },
  "images": {
    "JURY_PRESIDENT_SIGNATURE": {"content_type":"image/png","base64":"..."}
  },
  "make_pdf": true
}
```

El resultado devuelve DOCX y PDF en base64 y `unresolved_tokens`. Si queda un token crítico sin resolver, n8n debe bloquear el expediente.

## Render
Construir como Docker Web Service. No necesita Microsoft Word instalado. LibreOffice se usa solo para convertir DOCX a PDF.
