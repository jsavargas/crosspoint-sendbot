# Telegram Crosspoint Sendbot (v1.0.1)

Telegram bot to wirelessly send books to e-readers using **Crosspoint Reader** firmware (Xteink X4/X3).

## Features

- **Interactive**: Asks for the destination (Base Folder or Author) using Inline buttons.
- **Metadata Detection**: Attempts to read the author automatically from EPUB files.
- **Clean Chat**: Deletes sent files and status messages once processed.
- **Folder Management**: Books are moved from `/books/pending` to `/books/transfered` upon success.
- **Organization on Reader**: Supports automatic subfolder creation by author (configurable on the fly).

## Environment Setup

### Environment Variables (.env)

```env
BOT_TOKEN=your_telegram_bot_token
AUTHORIZED_USER_ID=your_telegram_user_id
```

*(Note: The IP and base folder are now managed via interactive commands and persistently stored in `/config/config.ini`).*

## Folder Structure

- **Local (Docker)**:
  - `/books/pending`: Received books queued for upload.
  - `/books/transfered`: History of successfully sent books.
  - `/config`: Contains `config.ini` with your persistent settings (Reader IP, save folder, etc.)
- **Remote (Reader)**:
  - Base path configurable via `/setfolder` (e.g., `/Books`).
  - Automatic author subfolder creation, toggleable using `/setauthor`.

## Commands

- `/start` or `/help`: Shows the current configuration and quick guide.
- `/status`: Performs an API ping to verify the reader is reachable (File Transfer enabled).
- `/id`: Displays your Telegram ID (for `.env` setup).
- `/send`: Initiates WiFi transfer of all queued books, showing a summary of successes and errors at the end.
- `/setcrosspointip <IP>`: Persistently sets the reader's IP.
- `/setfolder <Path>`: Sets the base folder on the reader (e.g., `/Books`). (*Note: `/crosspointfolder` is kept for retro-compatibility*).
- `/setauthor <on|off>`: Enables/disables organizing books into author subfolders.

## Workflow

1. **Upload**: Send an `.epub` file to the bot in Telegram.
2. **Select**: The bot detects the author and lets you choose between saving to the root folder or the author's specific folder.
3. **Cleanup**: After your choice, the bot deletes the file from the chat to maintain privacy.
4. **Sync**: Launch "File Transfer" on your e-ink reader.
5. **Verify (Optional)**: Use `/status` to ensure connection is active.
6. **Send**: Run `/send`. The bot will iteratively transfer all files and report back the results.

## Installation

1. Clone the repository.
2. Configure your `.env` file with your User ID and Bot Token.
3. Start the server using Docker:

```bash
docker-compose up -d --build
```
