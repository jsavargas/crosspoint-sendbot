# Telegram Crosspoint Bot (v2.0)

Bot de Telegram para enviar libros de forma inalámbrica a e-readers con firmware **Crosspoint Reader** (Xteink X4/X3).

## Nuevas Características v2.0

- **Interactivo**: Pregunta el destino (Carpeta base o Autor) mediante botones Inline.
- **Detección de Metadatos**: Intenta leer el autor automáticamente de archivos EPUB.
- **Chat Limpio**: Elimina los archivos enviados y los mensajes de estado una vez procesados.
- **Gestión de Carpetas**: Los libros se mueven de `/books/pending` a `/books/transfered` tras el éxito.
- **Organización en el Lector**: Soporta la creación de subcarpetas por autor.

## Configuración del Entorno (.env)

```env
BOT_TOKEN=tu_token_de_telegram
AUTHORIZED_USER_ID=tu_id_de_usuario
CROSSPOINT_IP=192.168.1.XXX
```

## Estructura de Carpetas

- **Local (Docker)**:
  - `/books/pending`: Libros recibidos esperando a ser enviados.
  - `/books/transfered`: Historial de libros ya enviados con éxito.
- **Remoto (Lector)**:
  - Ruta configurable mediante `/crosspointfolder` (ej: `/Books`).

## Comandos

- `/start` o `/help`: Muestra la configuración actual y guía rápida.
- `/id`: Muestra tu ID de Telegram (para el .env).
- `/send`: Inicia la transferencia WiFi de todos los libros en la cola.
- `/crosspointip <IP>`: Cambia la IP del lector de forma persistente.
- `/crosspointfolder <Ruta>`: Cambia la carpeta base en el lector (ej: `/MyLibrary`).

## Flujo de Uso

1. **Envío**: Mandas un `.epub` al bot.
2. **Selección**: El bot detecta el autor y te da a elegir entre guardarlo en la raíz o en la carpeta del autor.
3. **Limpieza**: Tras elegir, el bot borra tu archivo del chat para mantener la privacidad.
4. **Sincronización**: Entras en "File Transfer" en tu Xteink, escribes `/send` en el bot y listo.

## Instalación

```bash
docker-compose up -d --build
```
