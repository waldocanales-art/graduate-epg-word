# HAWKS Documentos V3 · Rama experimental
La rama `feature/hawks-documentos-v3-auditoria` NO modifica n8n, los endpoints publicados ni el renderer V1.

## Hallazgos confirmados en V1
- `app.py` ya implementa ocho plantillas: Acta de Sustentación, Acta de Originalidad, Autorización de Publicación, Declaración de Originalidad, Declaración Jurada y Hojas de Metadatos para 1, 2 y 3 autores.
- Sustituye tokens en párrafos y XML de Word; la sustitución reconstruyendo el texto en el primer run puede alterar estilos tipográficos en documentos complejos.
- Devuelve documentos incluso cuando quedan `unresolved_tokens`; un consumidor debe bloquear el expediente.
- El PDF es opcional y su conversión con LibreOffice no confirma por sí misma fidelidad de paginación.
- Ni el reconocimiento de firma/huella ni la validación jurídica deben inferirse por simple presencia de imagen.

## Alcance implementado
`document_quality.py` es un auditor independiente y de solo lectura que verifica estructura ZIP/XML del DOCX, placeholders sin resolver incluso si están fragmentados en varios runs y ausencia de campos críticos del payload por tipo de documento. Produce hallazgos trazables. No modifica archivo de entrada.

## Uso local
```python
from document_quality import audit_document
resultado = audit_document("salida.docx", "DECLARACION_JURADA",
                            {"TITLE": "Trabajo", "AUTHORS_DISPLAY": "Autores"})
assert resultado["ok"], resultado["findings"]
```

## Pendiente antes de habilitar producción
1. Conseguir copias controladas de las ocho plantillas Word y revisar sus placeholders reales.
2. Comparar salidas con documentos de referencia institucional autorizados.
3. Validar firmas, huellas, títulos, nombres, ORCID, DNI y autoría por fuente confiable.
4. Integrar auditoría como etapa previa a devolver el paquete; bloquear errores sin afectar V1.
5. Ejecutar pruebas DOCX y PDF con 1, 2 y 3 autores, más ausencias de datos y saltos de página.
6. Acordar integración explícita posterior; NO cambiar n8n durante desarrollo.
