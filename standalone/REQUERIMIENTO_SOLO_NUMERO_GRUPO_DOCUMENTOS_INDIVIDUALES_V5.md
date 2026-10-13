# HAWKS Documentos V5 — SOLO NÚMERO DE GRUPO Y DOCUMENTO POR DOCUMENTO
Fecha: 13/10/2026. Estado: requerimiento aprobado para diseño, implementación pendiente de conexión real. n8n permanece intacto.

## Objetivo
El operador dispone únicamente del número numérico del grupo. HAWKS debe localizar automáticamente su expediente, identificar autores, programa, fase, título, firmas, huellas, Turnitin, actas, asesores, jurados y formatos oficiales, y permitir procesar **un documento por vez**. Ningún dato adicional se solicita al operador por defecto.

## ÚNICO DATO DE ENTRADA
`grupo` = número entero positivo (por ejemplo `29`, `157`, `241`). Acepta ceros iniciales, normaliza a ID canónico y rechaza letras, valores vacíos y números imposibles. La clave de acceso de sesión es control de seguridad aparte: nunca se debe pedir al operador nombres, DNI, título, programa, ORCID, JSON, imagen, huella o Turnitin como requisito de búsqueda.

## Experiencia del operador
1. Abrir `https://hawks-documentos-v3-lab.onrender.com`, autenticarse mediante mecanismo seguro de sesión.
2. Escribir **solo el número de grupo** y pulsar `Buscar expediente`.
3. Mostrar cabecera **solo después de resolver fuentes**: grupo, nombres, programa, etapa, TI/TA, número de autores, carpeta Drive verificada; fuente y fecha. Ante grupo repetido o vínculo Drive conflictivo, mostrar `COLISIÓN DE IDENTIDAD` y no elegir arbitrariamente.
4. Mostrar una **lista de documentos** aplicables a ese expediente, cada fila con estado, origen en Drive/Gmail, fecha, autor, última versión y acciones:
   - `Abrir original` para evidencia institucional existente.
   - `Preparar Word` o `Generar este Word` para el único documento seleccionado, con la plantilla oficial de Liz correspondiente.
   - `Ver observaciones` para mostrar solamente diferencias específicas de ese documento.
   - `Descargar Word/PDF` tras completar QA apropiado.
5. Un clic genera **exactamente un documento** y no cambia los demás; el sistema guarda el progreso y permite elegir el próximo sin volver a buscar el equipo.
6. El sistema muestra `n de m documentos revisados / listos` y registro de acciones; no requiere un botón de envío masivo para esta modalidad.
7. Si falta una evidencia, mostrar cuál y dónde se buscó, **sin obligar a escribir campos** ni solicitar al alumno que la recargue cuando exista.

## Contrato de resolución automática (sin inventar datos)
**Precedencia:** hoja/padrón canónico ID grupo↔equipo↔Drive > documento original del expediente > correos institucionales del equipo > datos ya verificados por HAWKS. Búsqueda por alias o nombre es pista de investigación, no prueba de vínculo.

**Campos automáticos:** grupo, programa, fase, tipo académico TI/TA, 1/2/3 autores, nombres DNI ORCID, título definitivo, asesor, jurado, líneas institucional/programa/RSU, OCDE, fecha/veredicto/notas si hay sustentación, informe Turnitin de versión correspondiente, decisiones individuales de autorización para publicación, fuentes de firmas y huellas ya presentadas y documento de origen.

**Inventario Drive:** consultar carpeta del equipo, `TI`, `Otros documentos`, `REPOSITORIO`, carpetas anidadas y adjuntos de correos relacionados. Elegir versión final por expediente verificable; no confundir PDF Turnitin antiguo con resultado posterior.

**Plantillas:** correo Liz de 03/09/2026, carpeta https://drive.google.com/drive/folders/1sC5_-O1BiYuv8RtkkdrQPDjnIiw0Fd0A; usar plantillas TI o TA y hojas metadata_1/2/3 según tipo y autoría real. Las plantillas antiguas del motor V1 **no cumplen todavía** este requisito; no etiquetar como oficiales actualizados mientras no se hayan sincronizado y validado.

**Firmas y huellas:** recuperar sin pedir de nuevo los originales que el alumno ya presentó. Reutilizar exclusivamente para su propio expediente conforme a la instrucción institucional aplicable, manteniendo trazabilidad y el acto/documento suscrito; no insertar una firma ajena ni afirmar firma de un documento nuevo si la persona no aprobó su contenido.

## Estados por documento, no por grupo entero
- `ORIGINAL_EN_DRIVE`: original encontrado y enlazado, sin modificarlo.
- `DATOS_RECUPERADOS`: campos precompletados con fuentes, todavía pendiente de generar.
- `LISTO_PARA_GENERAR`: todas las fuentes requeridas para ese documento están verificadas.
- `BORRADOR_GENERADO`: Word creado pero no ha superado control final.
- `GENERADO_EN_REVISION`: documento generado, QA técnico satisfactorio; falta validación institucional si aplicable.
- `APTO_REPOSITORIO`: tras evidencias y aceptación institucional exigidas.
- `PENDIENTE_FUENTE`, `VERSION_TURNITIN_NO_COINCIDE`, `COLISION_GRUPO_DRIVE`, `DOCUMENTO_NO_APLICA`: excepciones visibles.
Nunca convertir «Word generado» en «acta emitida», «firmado» o «apto» automáticamente.

## Orden propuesto de generación por equipo (editable por operador)
1. Hoja de metadatos (1/2/3 autores según expediente).
2. Declaración jurada de autoría grupal.
3. Declaración de originalidad individual del autor 1; luego autor 2; luego autor 3 si existen.
4. Autorización de publicación individual de cada autor.
5. Acta de originalidad, cuando exista aprobación/firmas reales del asesor.
6. Acta de sustentación **solo si ya se realizó y existe acta original**; usar original autenticado preferentemente.
El menú mostrará solo documentos aplicables; cada acción procesa una sola fila y un solo autor si es individual.

## API sugerida
- `GET /v5/groups/{group_number}`: resolver expediente y fuentes; sin PII si no está autenticado.
- `GET /v5/groups/{group_number}/documents`: inventario individual, estado, campos llenos/faltantes y enlaces privados autorizados.
- `POST /v5/groups/{group_number}/documents/{document_id}/generate`: generar **exactamente un DOCX**, con idempotencia por versión de fuentes, autor y plantilla.
- `GET /v5/groups/{group_number}/documents/{document_id}/result`: Word, PDF, calidad y fuente.
Las respuestas no contienen huellas, firmas ni DNI en logs; utilizar sesión y autorización, no número de grupo como autenticación.

## Bloqueantes técnicos reales del servicio actual V3
- El sitio desplegado exige título, autores, programa y JSON manualmente. No tiene API de búsqueda por grupo.
- No existe conexión publicada y autenticada desde el servicio Render a Drive/Gmail/padrón institucional, aunque la búsqueda sí se ha realizado en esta conversación mediante conectores.
- El renderer actual usa plantillas legacy de `templates/` y puede aplanar estilos.
- El endpoint V3 exige imágenes de firma/huella en el payload pero su interfaz no las recupera de Drive.
Por ello, **el mero cambio de pantalla no hace funcionar el flujo solo-número**. Para habilitarlo se debe construir el resolver institucional seguro y sincronizar las plantillas de Liz antes de un despliegue funcional.

## Seguridad, aceptación y cierre
- Cero cambios en n8n, credenciales o servicio Render productivo original.
- Nada de archivos o datos sensibles reales en commits públicos de GitHub.
- Caso de prueba 1 autor (por ej. grupo 29), 2 autores y 3 autores, cada uno con nombre y Drive canónico verificado.
- Una sola consulta por número; cero formularios obligatorios adicionales para completar el documento; un solo documento generado por clic.
- Errores explícitos y descargables por documento; no detener el equipo completo por un único bloqueo.
- Cierre por documento basado en el documento real, no en que se han creado 504 plantillas vacías.
