# REQUERIMIENTO INTEGRAL HAWKS DOCUMENTOS V4
**Proyecto:** Motor documental autónomo para Escuela de Posgrado — Universidad Autónoma del Perú  
**Estado:** Especificación técnica para implementar; NO representa una función terminada ni una aprobación institucional  
**Línea base:** 90 registros F3–F6 / 84 códigos de equipo únicos; 504 Word V3 como **borradores** de comparación, no como expedientes válidos.  
**Restricción innegociable:** n8n y el generador productivo original deben permanecer intactos.

> **ACTUALIZACIÓN OPERATIVA PRIORITARIA — 13/10/2026:** La única información que proporciona el operador es el **número del grupo**. Todos los otros campos se resuelven automáticamente desde el expediente; se muestran los documentos del grupo para **generar o recuperar exactamente uno por acción**. Esta regla sustituye cualquier formulario manual de nombres, DNI, títulos, JSON, firmas, huellas o Turnitin. Requerimiento y controles detallados: [V5 — solo número y un documento por vez](REQUERIMIENTO_SOLO_NUMERO_GRUPO_DOCUMENTOS_INDIVIDUALES_V5.md). **Aún no está implementada la conexión Drive/Gmail en Render; no confundir el requerimiento con una función desplegada.**

## 0. Directriz operativa de atención urgente — coordinación EPG (13/10/2026)
La Coordinación de Investigación de Posgrado ha establecido como instrucción operativa **no volver a solicitar firmas ni huellas que los egresados ya entregaron**. La prioridad es reducir la demora acumulada y aprovechar inmediatamente la evidencia existente en Drive, Gmail y el expediente de cada autor.

**Flujo preferente:**
1. Recuperar del mismo expediente los documentos ya suscritos, sus firmas y huellas, y los informes Turnitin disponibles; no pedir al alumno que repita la carga por defecto.
2. Asociar inequívocamente cada evidencia a su **titular real** y equipo mediante nombres, DNI y fuente original; conservar identificador/hash y copia original.
3. Utilizar originales firmados íntegros siempre que correspondan; si se prepara un nuevo formulario institucional, documentar la base de autorización que invoca la Coordinación para reutilizar la evidencia de ese autor en ese trámite. No atribuirle a un firmante una declaración distinta que no haya aprobado.
4. Procesar en lote todas las evidencias recuperables; elevar a excepción únicamente los casos donde el documento original no existe, no es legible, pertenece a otro titular o presenta contradicción material.
5. Extraer el Turnitin guardado en Drive sin nueva solicitud y distinguir informe de versión histórica de la última versión. No bloquear la recuperación y prellenado por un informe antiguo: reportar discrepancia y continuar con los demás documentos del equipo.
6. No demorar **todos** los archivos de un expediente por la observación puntual de uno: entregar los documentos auténticos ya aptos y reportar aparte los documentos pendientes, sin llamarlos definitivos.
7. Mantener íntegramente n8n y los servicios productivos; aplicar esta prioridad únicamente en la rama experimental.

La instrucción sobre reutilización se registra como criterio operativo comunicado por la Coordinación, **no como una determinación jurídica autónoma sobre el consentimiento de cada titular**. Debe conservarse trazabilidad verificable de fuente, identidad y autorización institucional aplicada.

## 1. Problema que resuelve
Se construyeron 504 Word bajo seis categorías por 84 equipos, pero actualmente no está demostrada la asignación correcta de programa, cantidad de autores, identidad, datos académicos, jurados, formato oficial, firma/huella por firmante ni Turnitin de la versión final. Además, las actas podrían no corresponder a etapas previas a la sustentación. El requerimiento sustituye la generación ciega por un expediente canónico por equipo con controles de evidencia y estado de publicación explícito.

## 2. Fuentes oficiales
- Correo «COMUNICADO | ACTUALIZACIÓN DE FORMATOS PARA REPOSITORIO», 03/09/2026; carpeta de referencia: https://drive.google.com/drive/folders/1sC5_-O1BiYuv8RtkkdrQPDjnIiw0Fd0A
- Logo «LOGO AUTÓNOMA NARANJA.png», ID Drive `1OGj0zI2V-JkzGqLZTKLooHB9rnOuCU2S`.
- Plantillas diferenciadas TI (maestría) y TA (segunda especialidad), según `standalone/official_templates_2026_09.json`. Existen 8 claves TI y 7 TA identificadas; TA no incluye una plantilla de acta de sustentación en el inventario confirmado.
- Correo sobre documentos para repositorio MALDONADO–PANDAL, 09/10/2026: nombres según DNI, firma/huella legibles, título en formato oración, conservar documento Word y modelo original. La firma del asesor del acta de originalidad se gestiona internamente, sin inventarla.
- Expedientes reales en Drive de cada grupo, anexos originales de Gmail, hoja de metadatos firmada y fuentes institucionales de identidad.
- Turnitin de la **versión efectiva del TI/TA**; resultados anteriores solo son históricos.

## 3. Requerimientos funcionales priorizados
| ID | Prioridad | Especificación | Aceptación objetiva |
|---|---|---|---|
| RF-01 | P0 | Ingestar el padrón F3–F6 y desduplicar por ID canónico del grupo. | 90 filas registradas, 84 IDs únicos en la línea base; casos adicionales dinámicos; no se pierde evidencia de filas repetidas. |
| RF-02 | P0 | Resolver carpeta Drive canónica, documentos TI, adjuntos y correos del equipo. | Cada fuente registra ID, fecha, tipo, autor, hash y URL; colisiones de Drive/ID se bloquean. |
| RF-03 | P0 | Contrastar programa TI (maestría) vs TA (segunda especialidad) con evidencia matricular. | No se usa plantilla de programa distinto ni se infiere tipo por nombre. |
| RF-04 | P0 | Confirmar identidad y cantidad de autores (1 a 3) y relación inequívoca con el equipo. | Se valida nombre en orden y escritura DNI, documento de identidad, ORCID si el campo oficial lo exige; no se reasigna ningún autor por coincidencia parcial. |
| RF-05 | P0 | Seleccionar la **plantilla Word original** según tipo TI/TA + documento + número de autores. | Conserva logo, OOXML, tablas, márgenes, encabezados, paginación y tipografía; no parte de un DOCX fabricado. |
| RF-06 | P0 | Extraer datos obligatorios por campo: autores, asesor, jurado, título, programa, fecha, líneas de investigación, RSU, disciplinas OCDE. | Cada valor tiene referencia de origen y estado verificado/no verificado/conflicto; los ejemplos de plantilla se eliminan. |
| RF-07 | P0 | Incorporar firma y huella únicamente desde **documento original firmado** del titular, con procedencia y autorización. | Identidad del firmante, tipo de documento y evidencia coinciden; nunca se copian a otro firmante o acto distinto sin autorización documentada. |
| RF-08 | P0 | Validar consentimiento de publicación individual: acceso abierto/restricción/embargo y fechas según lo firmado. | Nunca se marca una opción por defecto; falta de consentimiento mantiene pendiente. |
| RF-09 | P0 | Asociar informe Turnitin al hash de la versión final del trabajo e identificar fecha, similitud y fuente. | Reporte histórico separado; similitud >20 % bloquea conformidad si ese umbral es aplicable; IA (≤30 %) se evalúa por evidencia distinta, sin confundir métricas. |
| RF-10 | P0 | Respetar el estado académico real, sustentación y actas emitidas. | Ningún acta se da por válida sin fecha, jurados, veredicto, calificación si procede y firmas autorizadas. El estado F3–F6 no prueba sustentación. |
| RF-11 | P0 | Preservar legalmente el documento original ya firmado. | Preferir original íntegro y trazable cuando sea válido; no reconstruir ni trasplantar firmas/huellas en nuevas declaraciones de manera automática. |
| RF-12 | P0 | Ejecutar control final por archivo: integridad DOCX, tokens, campos, fuentes, autenticidad, formato y revisiones visuales. | 0 campos críticos pendientes, 0 tokens sin resolver, 0 contradicciones en estado `APTO`. |
| RF-13 | P0 | Generar paquete por equipo solo para documentos **que le correspondan**, no seis por defecto. | Índice explica aplicabilidad por etapa, obligatoriedad, existencia, versión y estado de cada documento. |
| RF-14 | P0 | Diferenciar `BORRADOR`, `PENDIENTE_FIRMA`, `PENDIENTE_DATOS`, `EN_REVISION`, `APTO_REPOSITORIO`. | Ningún estado pendiente se denomina definitivo ni se exporta como válido. |
| RF-15 | P1 | Exportación masiva con ZIP general, ZIP por equipo, manifest CSV/JSON y reporte de discrepancias. | Un archivo de control por cada equipo; sumatoria y estado coinciden con originales recuperados. |
| RF-16 | P1 | Reanudar lotes, registrar errores por equipo y repetir solo lo afectado. | Una falla aislada no reinicia la totalidad ni duplica documentos. |
| RF-17 | P1 | Vista web con búsqueda de equipo, documentos recuperados, fuentes y motivo de bloqueo. | Usuario puede verificar origen sin exposición de datos sensibles innecesarios. |
| RF-18 | P1 | Registrar versión de plantilla y reglas aplicadas a cada documento. | Documento reproducible con hashes, fecha, plantilla, reglas y fuentes verificadas. |

## 4. Matriz de documentos y compuertas
| Documento | Datos mínimos | Evidencia indispensable | Condición de emisión |
|---|---|---|---|
| Hoja de metadatos | 1/2/3 autores; identidad; programa; título definitivo; asesor; jurado; ORCID, líneas y OCDE según plantilla | Fuentes oficiales del expediente | Solo correcta cantidad de autores y variante TI/TA |
| Declaración jurada | Todos los autores, DNI, fecha y demás campos oficiales | Firma **y** huella propia de cada firmante si el formato la exige | No final sin evidencias verificadas |
| Declaración de originalidad | Autor, título y declaraciones exigidas | Firma y confirmación de autoría | No final sin firma válida |
| Autorización publicación | Titular, título, licencia, opción de publicación, embargo si aplica | Consentimiento individual firmado | No completar casillas por inferencia |
| Acta de aprobación de originalidad | Trabajo, asesor, informe Turnitin versión final | Acta o aprobación original del asesor; firma gestionada por canal institucional | No publicar como acta oficial sin aval |
| Acta de sustentación | Datos de sustentación, fecha, jurado, veredicto y nota cuando corresponda | Acta institucional auténtica con sus firmas | Solo si sustentación efectivamente realizada y acta emitida |

**Nota:** los formatos TA y TI no son necesariamente equivalentes. Verificar la exigibilidad según procedimiento y etapa antes de generar.

## 5. Proceso técnico y arquitectura — aislados de n8n
1. `ingest`: leer exportación y fuentes conectadas en modo lectura; no modificar flujo n8n.
2. `resolve_identity`: correlación estricta ID de grupo ↔ integrantes ↔ Drive ↔ correos; tabla de colisiones.
3. `evidence`: recopilar originales y hashes; firma/huella tratadas como datos sensibles, cifrados y de acceso controlado; nunca subir a GitHub.
4. `normalize`: expediente JSON canónico por equipo; catálogo de linaje con valor+fuente+fecha+confianza+estado.
5. `template_registry`: descargar plantillas oficiales autorizadas (TI/TA, 1/2/3 autores), asegurar versión del nuevo logo.
6. `render`: rellenar en OOXML sin aplanar estilos ni destruir encabezados/tablas; si no existe firma original adecuada, dejar documento como borrador y no como documento firmado.
7. `quality_gate`: comprobar versión, identidad, PDF de control de diseño, firmas y huellas, Turnitin, actas, consentimiento, plantillas y campos.
8. `package`: entrega ZIP por equipo / lote; `manifest.csv`, `manifest.json`, `issues.csv`, hashes SHA-256, enlace a fuente y estado.
9. `review`: aprobación manual documentada de cuestiones jurídicas e institucionales; solo entonces cambiar a `APTO_REPOSITORIO`.

## 6. Seguridad, privacidad y reglas de actuación
- No editar workflows, credenciales, hojas de n8n ni servicios productivos.
- El repositorio GitHub contiene únicamente código, instrucciones, esquemas y **datos de prueba sintéticos**. No incluir DNI reales, firmas, huellas, enlaces con tokens, informes Turnitin completos, correos ni documentos personales.
- Almacenamiento de evidencias en ubicación institucional privada, con acceso mínimo, logs sin PII y política de retención.
- No fabricar firmas, huellas, resoluciones, notas, aprobación de jurado o Turnitin. No usar una firma/huella de alguien para firmar en nombre de otra persona.
- Las evidencias deben vincularse al acto concreto, no solo a una identidad. Reutilizar el documento original firmado íntegro cuando corresponda.
- La generación de borradores es permitida; la emisión de declaración legal firmada nueva exige autorización y validación auténtica.

## 7. Pruebas obligatorias y criterios globales de éxito
- Pruebas de plantillas TI 1/2/3 autores y TA 1/2/3 autores, y de todas las categorías disponibles por programa.
- Comparación visual contra plantilla oficial de Liz: logo correcto, tablas, saltos, estilos, margen, espaciado, folios, secciones, calidad de imágenes; no declarar 100% hasta la revisión.
- Tests de colisión Drive, equipo compartido, DNI ambiguo, autor repetido, autor ausente, firmas/huellas ausentes o asignadas a otro firmante, Turnitin desactualizado, sustentación inexistente y consentimiento no seleccionado.
- En expedientes `APTO_REPOSITORIO`: 100% campos críticos con fuente; 100% firmas y huellas exigidas con soporte autenticado; 0 errores de plantilla; 0 datos ajenos; 0 actas inventadas; trazabilidad disponible.
- Los 504 Word anteriores son material de contraste solamente. **No se autoriza emitir automáticamente 504 documentos finales si algunos son inaplicables por fase.**
- Despliegue nuevo solo tras revisión de integridad y autorización; nunca actualizar silenciosamente n8n.

## 8. Plan de implementación y entregables
**P0 — Resolver fuentes y fidelidad:** matriz de campos por plantilla real, plantilla oficial TI/TA, fuente por equipo, extracción con linaje, bloqueos de firma, huella, título, jurado, Turnitin y consentimiento.

**P1 — Generación y QA:** módulo OOXML no destructivo, casos de 1/2/3 autores, pruebas automáticas y visuales con originales.

**P2 — Operación masiva:** lotes reanudables, panel web, ZIP general, índice auditado, reporte de excepciones y aprobación institucional.

**Condición de cierre:** cada expediente tiene o (A) sus documentos procedentes y validados o (B) lista exacta de impedimentos y fuentes faltantes, sin alegar cumplimiento ficticio. No basta con contar DOCX generados.
