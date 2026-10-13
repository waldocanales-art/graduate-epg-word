# HAWKS Documentos V6.2 · Conexión Google Drive y generación

## Estado de implementación
- La aplicación HAWKS del laboratorio incluye `GET /v6/demo/metadata.docx?authors=2` para probar la generación de un Word verdadero con datos totalmente ficticios; **no es la plantilla institucional de Liz**.
- `GET /v6/drive/status` (requiere `X-API-Key`) indica si el servidor tiene una cuenta de servicio configurada, sin mostrar la clave privada.
- `GET /v6/groups/{numero}/drive-files` (requiere `X-API-Key`) toma el ID de carpeta candidato del índice privado del grupo y enumera archivos de forma **solo lectura**. No permite introducir una carpeta arbitraria ni certifica que la carpeta corresponda al grupo hasta cotejar la identidad.
- El panel ofrece "Consultar archivos en Drive" para el grupo seleccionado, junto a la auditoría de brechas y la generación de borradores de metadatos ya habilitada en grupos con perfil verificado.
- ChatGPT tiene su **propia conexión** a Google Drive: ese acceso no suministra credenciales a Render. Ningún token del chat se copia al repositorio ni al servicio.

## Configuración mínima (personal responsable EPG / administrador de Google Cloud)
1. Abrir Google Cloud Console en un proyecto aprobado por la institución y **habilitar la Google Drive API**.
2. Crear una **cuenta de servicio dedicada** para HAWKS con rol mínimo. Obtener su correo de la forma `nombre@proyecto.iam.gserviceaccount.com`.
3. Si la política de seguridad lo permite, generar una **clave JSON** para esa cuenta de servicio. No enviarla por correo, chat, GitHub ni n8n. Usar un mecanismo institucional de secret management cuando esté disponible.
4. El propietario o administrador de las carpetas EPG comparte **solo la carpeta raíz autorizada** (que contenga los expedientes por equipo, TI y Otros) con ese correo, como **Lector**. No otorgar Editor ni acceso público. Si la política de Workspace bloquea compartir con cuentas de servicio, TI deberá habilitar el acceso institucional o usar un puente OAuth restringido; no abrir carpetas a cualquiera con enlace.
5. Abrir **Render → servicio `hawks-documentos-v3-lab` → Environment**. Crear `HAWKS_DRIVE_SA_JSON` y pegar **el JSON íntegro de credenciales** como valor privado. Guardar y esperar el despliegue del servicio. Render tendrá la clave en su entorno, nunca en el navegador.
6. En HAWKS ingresar la clave de acceso al servicio, buscar un número de grupo ya verificado y pulsar **Consultar archivos en Drive**. La primera prueba debería mostrar nombres de archivos; si aparece 403, falta compartir la carpeta con la cuenta técnica.
7. Verificar con 1 grupo piloto que:
    - El grupo coincida de forma unívoca con su carpeta de Drive;
    - Las carpetas TI, Otros y Repositorio se enumeren;
    - El documento original, la hoja de metadatos y el título del TI/TA pertenezcan al mismo grupo;
    - Se vea la versión final de Turnitin y se distingan **similitud ≤20%** de **escritura IA ≤30%** por lectura del informe (los nombres de archivo no certifican resultados);
    - El Word generado sea un **borrador** hasta comprobar la plantilla oficial de Liz y que no se fabriquen firmas ni huellas.
8. Solo después de las pruebas se habilitará un flujo de descarga de originales al ZIP y generación de documentos definitivos por grupo. La versión V6.2 actual **no certifica expedientes ni descarga en masa los originales**.

## Pruebas y accesos
- Interfaz HAWKS: https://hawks-documentos-v3-lab.onrender.com
- Servicio Render: https://dashboard.render.com/web/srv-db6qgeon74is738k8oeg
- Word de demostración: https://hawks-documentos-v3-lab.onrender.com/v6/demo/metadata.docx?authors=2
- Diagnóstico de conexión: `GET /v6/drive/status` con encabezado `X-API-Key`.
- Inventario de grupo: `GET /v6/groups/NUMERO/drive-files` con encabezado `X-API-Key`.

## Privacidad
- Los tokens y claves permanecen fuera de GitHub, de los documentos descargables y de la página web.
- La API usa el alcance de Drive `https://www.googleapis.com/auth/drive.readonly`.
- Ninguna consulta modifica archivos, firmas o huellas.
- El índice de grupos está almacenado como configuración privada en Render.
- Se debe comprobar el acceso por usuario y grupo antes de cualquier expansión de uso institucional: la clave compartida actual es un control básico de laboratorio, no un sistema de roles individualizado.
