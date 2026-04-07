import os
import asyncio
import logging
import httpx
import json
import sys
import shutil
from pathlib import Path
import configparser
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Try to import EbookLib for metadata extraction
try:
    from ebooklib import epub
except ImportError:
    epub = None

# Load environment variables
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
AUTH_USER_ID = os.getenv("AUTHORIZED_USER_ID")
CONFIG_FILE = Path("/config/config.ini")
METADATA_FILE = Path("/books/pending_metadata.json")
BOT_VERSION = "1.0.1"

# Root book directory configuration
PENDING_DIR = Path("/books/pending")
TRANSFERED_DIR = Path("/books/transfered")

# Ensure folders exist
PENDING_DIR.mkdir(parents=True, exist_ok=True)
TRANSFERED_DIR.mkdir(parents=True, exist_ok=True)

# Detailed Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
# Silence noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.ERROR)
logger = logging.getLogger("CrosspointSendbot")

def get_config():
    """Load or return default bot configuration."""
    conf = {"CROSSPOINT_IP": "192.168.1.XXX", "BASE_FOLDER": "/", "SAVE_BY_AUTHOR": True}
    if CONFIG_FILE.exists():
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            if 'DEFAULT' in config:
                if 'CROSSPOINT_IP' in config['DEFAULT']:
                    conf['CROSSPOINT_IP'] = config['DEFAULT']['CROSSPOINT_IP']
                if 'BASE_FOLDER' in config['DEFAULT']:
                    conf['BASE_FOLDER'] = config['DEFAULT']['BASE_FOLDER']
                if 'SAVE_BY_AUTHOR' in config['DEFAULT']:
                    conf['SAVE_BY_AUTHOR'] = config['DEFAULT'].getboolean('SAVE_BY_AUTHOR')
        except Exception as e:
            logger.error(f"[CONFIG] Error: {e}")
    return conf

def save_config(conf):
    """Save configuration to persistent file."""
    try:
        config = configparser.ConfigParser()
        config['DEFAULT'] = {
            'CROSSPOINT_IP': str(conf['CROSSPOINT_IP']),
            'BASE_FOLDER': str(conf['BASE_FOLDER']),
            'SAVE_BY_AUTHOR': str(conf.get('SAVE_BY_AUTHOR', True))
        }
        with open(CONFIG_FILE, "w") as f:
            config.write(f)
    except Exception as e:
        logger.error(f"[CONFIG] Error: {e}")

def get_pending_metadata():
    """Load or return pending book metadata."""
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except Exception: pass
    return {}

def save_pending_metadata(data):
    """Save metadata to persistent file."""
    try:
        with open(METADATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"[METADATA] Error: {e}")

def get_help_text(conf):
    return (
        f"Crosspoint Sendbot v{BOT_VERSION} - User Guide\n\n"
        "This bot manages the wireless delivery of books to your Xteink e-reader.\n\n"
        "Current Configuration:\n"
        f"IP: {conf['CROSSPOINT_IP']}\n"
        f"Base folder: {conf['BASE_FOLDER']}\n"
        f"Save by author: {'Yes' if conf.get('SAVE_BY_AUTHOR', True) else 'No'}\n\n"
        "Commands:\n"
        "/send - Upload all pending books.\n"
        "/setcrosspointip <IP> - Change the reader's IP.\n"
        "/setfolder <Path> - Define the base folder (e.g. / or /Books).\n"
        "/setauthor <on|off> - Enable or disable saving by author.\n"
        "/status - Check the connection with the reader.\n"
        "/id - Show your Telegram ID.\n\n"
        "Workflow:\n"
        "1. Send a book to the bot.\n"
        "2. Choose whether to save it in the root or by author (buttons).\n"
        "3. The bot will clean the chat by deleting the sent file.\n"
        "4. When ready, enable 'File Transfer' on the reader.\n"
        "5. Run /send to upload everything."
    )

async def post_init(application):
    """Notify the user that the bot is online."""
    logger.info(f"[SYSTEM] Bot started v{BOT_VERSION}")
    if AUTH_USER_ID:
        try:
            conf = get_config()
            text = f"Crosspoint Sendbot v{BOT_VERSION} Started\n\n" + get_help_text(conf)
            await application.bot.send_message(
                chat_id=AUTH_USER_ID, 
                text=text
            )
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in post_init: {e}")

async def check_auth(update: Update):
    """Verify if the user is authorized to use the bot."""
    user_id = str(update.effective_user.id)
    if AUTH_USER_ID and user_id != str(AUTH_USER_ID):
        logger.warning(f"[SECURITY] Unauthorized access attempt from ID: {user_id}")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and display current configuration."""
    if not await check_auth(update): return
    conf = get_config()
    await update.message.reply_text(get_help_text(conf))

async def set_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update the base folder on the device."""
    if not await check_auth(update): return
    if not context.args:
        await update.message.reply_text("Usage: /setfolder /Books")
        return
    conf = get_config()
    conf["BASE_FOLDER"] = context.args[0]
    save_config(conf)
    await update.message.reply_text(f"Base folder updated to: {conf['BASE_FOLDER']}")

async def set_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle saving by author."""
    if not await check_auth(update): return
    if not context.args or context.args[0].lower() not in ['on', 'off', 'true', 'false']:
        await update.message.reply_text("Usage: /setauthor [on|off]")
        return
    
    val = context.args[0].lower() in ['on', 'true']
    conf = get_config()
    conf["SAVE_BY_AUTHOR"] = val
    save_config(conf)
    await update.message.reply_text(f"Save by author updated to: {'Enabled' if val else 'Disabled'}")

async def set_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update the device IP address."""
    if not await check_auth(update): return
    if not context.args:
        await update.message.reply_text("Usage: /setcrosspointip IP")
        return
    conf = get_config()
    conf["CROSSPOINT_IP"] = context.args[0]
    save_config(conf)
    await update.message.reply_text(f"IP address updated to: {conf['CROSSPOINT_IP']}")

def extract_author(file_path):
    """Try to extract author metadata from EPUB files."""
    if not epub or not str(file_path).lower().endswith(".epub"):
        return None
    try:
        book = epub.read_epub(file_path)
        author = book.get_metadata('DC', 'creator')
        if author:
            return author[0][0]
    except Exception: pass
    return None

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming ebook documents."""
    if not await check_auth(update): return
    doc = update.message.document
    file_path = PENDING_DIR / doc.file_name
    
    logger.info(f"[DOWNLOAD] Receiving: {doc.file_name}")
    try:
        new_file = await context.bot.get_file(doc.file_id)
        await new_file.download_to_drive(custom_path=file_path)
        
        await update.message.reply_text(f"Book received: {doc.file_name}\nUse /send to upload it to your device.")
        
    except Exception as e:
        logger.error(f"[DOWNLOAD] Error: {e}")
        await update.message.reply_text("Error downloading book.")

class ProgressFile:
    """Wrapper to track file read progress."""
    def __init__(self, path, msg_callback):
        self.f = open(path, "rb")
        self.size = os.path.getsize(path)
        self.uploaded = 0
        self.msg_callback = msg_callback
        self.last_p = -1
        self.name = os.path.basename(path)

    def read(self, n):
        chunk = self.f.read(n)
        if chunk:
            self.uploaded += len(chunk)
            p = int((self.uploaded / self.size) * 100)
            if p >= self.last_p + 10 or p == 100:
                self.last_p = p
                bar = "#" * (p // 10) + "-" * (10 - (p // 10))
                asyncio.create_task(self.msg_callback(f"Uploading: {self.name}\n[{bar}] {p}%"))
        return chunk

    def tell(self): return self.f.tell()
    def seek(self, offset, whence=0): return self.f.seek(offset, whence)
    def __len__(self): return self.size
    def close(self): self.f.close()

async def send_to_device(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Upload all pending books to the device."""
    if not await check_auth(update): return
    conf = get_config()
    ip = conf['CROSSPOINT_IP']
    files = list(PENDING_DIR.glob("*"))
    
    if not files:
        await update.message.reply_text("No pending books in /books/pending.")
        return

    logger.info(f"[UPLOAD] Starting upload process for {len(files)} files to {ip}")
    status_msg = await update.message.reply_text(f"Connecting to {ip}...")
    
    successes = []
    failures = []

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                await client.get(f"http://{ip}/", timeout=5.0)
            except Exception as e:
                logger.error(f"[UPLOAD] Connection to {ip} failed: {e}")
                await status_msg.edit_text(f"Error: Device not found at {ip}.\nMake sure 'File Transfer' is active.")
                return

            for file in files:
                author = extract_author(file) if conf.get('SAVE_BY_AUTHOR', True) else None
                base_f = conf['BASE_FOLDER']
                if base_f != '/' and base_f.endswith('/'):
                    base_f = base_f[:-1]
                target_path = f"{base_f}/{author}" if author else (base_f if base_f else "/")
                target_path = target_path.replace('//', '/')
                
                logger.info(f"[UPLOAD] File: {file.name} -> Target: {target_path}")
                await status_msg.edit_text(f"Uploading: {file.name}...")
                
                async def update_progress(text):
                    try: await status_msg.edit_text(text)
                    except: pass

                pf = ProgressFile(file, update_progress)
                try:
                    # Create directory if needed (using multipart/form-data)
                    if author:
                        try:
                            mkdir_files = {
                                "name": (None, str(author)),
                                "path": (None, str(conf['BASE_FOLDER']))
                            }
                            await client.post(f"http://{ip}/mkdir", files=mkdir_files)
                        except Exception as e:
                            logger.warning(f"[UPLOAD] mkdir failed (expected if path exists): {e}")

                    # Upload file (path should be a query parameter)
                    response = await client.post(
                        f"http://{ip}/upload",
                        params={"path": target_path},
                        files={"file": (file.name, pf, "application/octet-stream")},
                        timeout=None
                    )

                    if response.status_code == 200:
                        logger.info(f"[SUCCESS] Uploaded {file.name}")
                        shutil.move(str(file), str(TRANSFERED_DIR / file.name))
                        successes.append((file.name, target_path))
                    else:
                        logger.error(f"[ERROR] Upload {file.name} failed with HTTP {response.status_code}")
                        failures.append((file.name, f"HTTP {response.status_code}"))
                except Exception as e:
                    logger.error(f"[ERROR] Exception uploading {file.name}: {e}")
                    failures.append((file.name, str(e)))
                finally:
                    pf.close()

        # Final cleanup and report
        try: await status_msg.delete()
        except: pass
        
        summary = "Upload Results:\n\n"
        if successes:
            summary += f"✅ Successful ({len(successes)}):\n"
            for fname, tpath in successes:
                summary += f"- {fname}\n  -> {tpath}\n"
        if failures:
            summary += f"\n❌ Failed ({len(failures)}):\n"
            for fname, reason in failures:
                summary += f"- {fname} ({reason})\n"
                
        if len(summary) > 4000:
            summary = summary[:4000] + "...\n(Message too long, truncated)"
            
        await update.message.reply_text(summary)

    except Exception as e:
        logger.error(f"[SYSTEM] Unexpected error in send_to_device: {e}")
        await update.message.reply_text(f"Critical error during upload: {e}")

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the connection status with the eink reader."""
    if not await check_auth(update): return
    conf = get_config()
    ip = conf['CROSSPOINT_IP']
    
    status_msg = await update.message.reply_text(f"Checking connection with {ip}...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://{ip}/api/status")
            if response.status_code == 200:
                try:
                    data = response.json()
                    await status_msg.edit_text(f"✅ Successful connection to {ip}\nStatus:\n```json\n{json.dumps(data, indent=2)}\n```", parse_mode="MarkdownV2")
                except:
                    await status_msg.edit_text(f"✅ Successful connection to {ip}\n(Raw response):\n{response.text[:500]}")
            else:
                await status_msg.edit_text(f"❌ The device responded with an error: HTTP {response.status_code}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Connection error with {ip}:\n{str(e)}\n\nMake sure 'File Transfer' is active on the reader.")

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respond with the user's Telegram ID."""
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("send", send_to_device))
    app.add_handler(CommandHandler("setcrosspointip", set_ip))
    app.add_handler(CommandHandler("crosspointfolder", set_folder))
    app.add_handler(CommandHandler("setfolder", set_folder))
    app.add_handler(CommandHandler("setauthor", set_author))
    app.add_handler(CommandHandler("status", check_status))
    
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    app.run_polling()
