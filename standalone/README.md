# HAWKS Documentos V3 — motor autónomo

Servicio independiente dentro de la rama experimental. No se modifica `app.py`, ningún workflow n8n ni el servicio Render de V1.

## API
- `GET /health` muestra plantillas disponibles.
- `POST /v3/documents/render`, encabezado `X-API-Key`, recibe el mismo cuerpo de `/v1/word/render`.
- Si falta una variable `DOCUMENTOS_V3_API_KEY`, devuelve 503 (cerrado por defecto).
- Si quedan campos obligatorios o tokens sin sustituir, devuelve HTTP 422 y elimina DOCX/PDF base64 del resultado.
- Si se solicita PDF y no se genera, devuelve HTTP 422.
- Una salida válida se etiqueta `GENERATED_PENDING_INSTITUTIONAL_REVIEW`: **no** certifica firmas, huellas ni cumplimiento formal.

## Ejecución aislada
Desde la raíz del repositorio:
```bash
docker build -f standalone/Dockerfile -t hawks-documentos-v3 .
docker run --rm -p 10001:10000 -e DOCUMENTOS_V3_API_KEY="clave-local-de-prueba" hawks-documentos-v3
```
Visitar `http://localhost:10001/health`; enviar solicitudes a `http://localhost:10001/v3/documents/render`.

## Precauciones
1. No desplegar sobre un servicio Render existente.
2. No configurar rutas de n8n hacia esta API hasta la validación y autorización expresa.
3. Comparar las plantillas originales y completar reglas de campos según normativa institucional.
4. Validar la fidelidad visual DOCX/PDF, firmas y huellas con expediente real anonimizado.
5. El motor heredado todavía usa una sustitución que puede modificar estilos; se conserva solo para compatibilidad temporal y necesita reemplazo antes de producción.

## Separación completa
La carpeta `standalone/` es el punto de partida del proyecto. Por ahora reside en la rama `feature/hawks-documentos-v3-auditoria` del repositorio existente; no representa todavía un segundo repositorio GitHub ni un despliegue público.
