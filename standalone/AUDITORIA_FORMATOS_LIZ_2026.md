# Auditoría técnica de formatos EPG — 2026-10-12

## Fuente institucional confirmada
Correo de GradUA del 03/09/2026, «COMUNICADO | ACTUALIZACIÓN DE FORMATOS PARA REPOSITORIO».
Carpeta: https://drive.google.com/drive/folders/1sC5_-O1BiYuv8RtkkdrQPDjnIiw0Fd0A
Incluye logo «LOGO AUTÓNOMA NARANJA.png», formularios diferenciados para maestría (TI) y segunda especialidad (TA). La carpeta oficial no es lo mismo que las plantillas legacy del repositorio.

## Reglas obligatorias basadas en plantillas y en la comunicación institucional
1. Elegir **TI/maestría o TA/segunda especialidad** antes de seleccionar plantilla. No aplicar automáticamente una plantilla TI a TA.
2. Seleccionar hoja de metadatos 1, 2 o 3 autores según autores **verificados**. Los Word oficiales incluyen nombres, DNI, ORCID, asesor, jurado, título y líneas **de ejemplo**: reemplazar todos con datos del expediente o marcar sin completar. Nunca transmitir ejemplos al expediente final.
3. En metadatos también se exigen asesor, jurado con tres cargos, ORCID, título definitivo, línea institucional, línea del programa, línea RSU, dos disciplinas OCDE. No rellenar con estimaciones ni asumir líneas.
4. Declaración jurada: hay tabla de **hasta 3 autores** con columnas nombre, DNI, firma y huella. Exigir prueba auténtica **por autor** para cada fila; prohibido replicar firma o huella entre personas.
5. Declaración de originalidad / autorización de publicación: no dar por firmadas las plantillas que solo tienen campo de firma vacío.
6. Formulario de autorización: además de datos personales, requiere decisión explícita del titular sobre licencia, acceso abierto, embargo o restricción y en su caso fecha de embargo. No marcar opciones unilateralmente.
7. Acta de originalidad: el porcentaje de similitud debe derivar del informe Turnitin correspondiente a **esa versión**, con fecha y trazabilidad; una cifra histórica no autoriza documento final. La firma del asesor puede gestionarse internamente, según correo del 09/10/2026 «DOCUMENTOS PARA REPOSITORIO: MALDONADO - PANDAL».
8. Acta de sustentación: jurados reales, fechas, veredicto, nota y actas auténticas. No generar un acta oficial antes de sustentación ni inferirla por etapa F3/F4/F5/F6.
9. Mantener diseños, logos, tablas y disposición exactos de las plantillas: no crear un documento visualmente parecido con párrafos nuevos. Preservar estilos de runs OOXML. QA visual DOCX y PDF individual por tipología.
10. Nombre y apellidos en orden indicado, según DNI; título en formato oración, sin mayúsculas sostenidas; comunicación institucional pide remitir Word y firmas/huellas legibles.

## Resultado de auditoría de los borradores V2
Analizados con python-docx: 504 archivos Word, 84 carpetas de equipo.
- 84 archivos de metadatos usan plantilla 1 autor **sin cotejo previo**.
- 252 documentos contienen posiciones de firmas cuya evidencia no está verificada.
- 168 documentos (actas) carecen de validación de jurado/sustentación.
- El escaneo específico de siete cadenas de ejemplos mostró cero coincidencias en los 504 borradores, **pero** no confirma que el resto del documento esté saneado o completo.
- Ningún borrador queda aprobado para repositorio por este análisis.

## Contrato de datos por expediente para próxima generación
```json
{
 "group_id": "EPG-###",
 "program_type": "TI|TA",
 "phase": "F3|F4|F5|F6",
 "authors": [{"name": "", "dni": "", "orcid": "", "email": "", "phone": "",
   "signature_source": null, "fingerprint_source": null}],
 "adviser": {"name": "", "dni": "", "orcid": "", "signature_source": null},
 "jury": {"president": {}, "secretary": {}, "vocal": {}},
 "research": {"title": "", "institutional_line": "", "program_line": "", "rsu_action_line": "",
   "ocde_disciplines": []},
 "defense": {"date": null, "verdict": null, "score": null, "acta_source": null},
 "turnitin": {"percent": null, "report_date": null, "version_hash": null, "report_source": null},
 "publication": {"choice": null, "embargo_until": null, "license": null,
   "author_authorization_source": null},
 "sources": {"drive_folder": "", "emails": [], "official_template_id": ""},
 "quality": {"source_completeness": false, "signatures_verified": false, "fingerprints_verified": false}
}
```
Los datos sensibles solo deben almacenarse en ámbitos autorizados; no introducir DNI, firmas o huellas en commits públicos de GitHub.

## Precedencia documental
Fuente firmada original y expediente Drive del equipo > comunicación institucional vigente con el trabajo definitivo > hojas de metadatos validadas > datos de identificación del sistema > alias de equipo para búsqueda solamente. Ante contradicción, bloquear y marcar discrepancia; no adivinar.

## Bloqueadores reales para producir versión definitiva
Recuperación autorizada por equipo de documentos y evidencias, unión inequívoca grupo↔integrantes, verificación individual de firma/huella, versión final de TI/TA y Turnitin, y pruebas de reproducción de plantilla oficial.
