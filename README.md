# Telegram Crosspoint Sendbot (v1.0.1)

Bot de Telegram para enviar libros de forma inalámbrica a e-readers con firmware **Crosspoint Reader** (Xteink X4/X3).

## Características

- **Interactivo**: Pregunta el destino (Carpeta base o Autor) mediante botones Inline.
- **Detección de Metadatos**: Intenta leer el autor automáticamente de archivos EPUB.
- **Chat Limpio**: Elimina los archivos enviados y los mensajes de estado una vez procesados.
- **Gestión de Carpetas**: Los libros se mueven de `/books/pending` a `/books/transfered` tras el éxito.
- **Organización en el Lector**: Soporta la creación de subcarpetas por autor (configurable al vuelo).

## Configuración del Entorno

### Variables de entorno (.env)

```env
BOT_TOKEN=tu_token_de_telegram
AUTHORIZED_USER_ID=tu_id_de_usuario
```

*(Nota: La IP y la carpeta base ahora se gestionan vía comandos interactivos y se guardan en `/config/config.ini` de forma persistente).*

## Estructura de Carpetas

- **Local (Docker)**:
  - `/books/pending`: Libros recibidos esperando a ser enviados.
  - `/books/transfered`: Historial de libros ya enviados con éxito.
  - `/config`: Contiene `config.ini` con tus ajustes persistentes (IP del lector, carpeta de guardado, etc.)
- **Remoto (Lector)**:
  - Ruta configurable mediante `/setfolder` (ej: `/Books`).
  - Creación de subcarpetas automáticas según el autor, habilitable con `/setauthor`.

## Comandos

- `/start` o `/help`: Muestra la configuración actual y la guía rápida.
- `/status`: Realiza un ping API para verificar que el lector esté al alcance (File Transfer encendido).
- `/id`: Muestra tu ID de Telegram (para configurarlo en el `.env`).
- `/send`: Inicia la transferencia WiFi de todos los libros en la cola mostrando un resumen de éxito y errores al finalizar.
- `/setcrosspointip <IP>`: Cambia la IP del lector de forma persistente.
- `/setfolder <Ruta>`: Cambia la carpeta base en el lector (ej: `/Books`). (*Nota: `/crosspointfolder` sigue funcionando por compatibilidad*).
- `/setauthor <on|off>`: Activa o desactiva la organización de los libros por subcarpetas de autor.

## Flujo de Uso

1. **Envío**: Mandas un `.epub` al bot en Telegram.
2. **Selección**: El bot detecta el autor y te da a elegir entre guardarlo en la raíz o en la carpeta del autor correspondiente.
3. **Limpieza**: Tras elegir, el bot borra tu archivo del chat para mantener la privacidad.
4. **Sincronización**: Entras en "File Transfer" en tu lector e-ink.
5. **Verificación (Opcional)**: Usas `/status` para asegurar que está conectado.
6. **Subida**: Ejecutas `/send` y el bot manda los archivos iterativamente y reporta qué ocurrió.

## Instalación

1. Clona el repositorio.
2. Configura el `.env` con tu User ID y Bot Token.
3. Inicia el servidor mediante Docker:

```bash
docker-compose up -d --build
```
