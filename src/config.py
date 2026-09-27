import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent

# Project Data Directories
DATA_DIR = ROOT_DIR / "data"
PHOTOS_DIR = DATA_DIR / "photos"
REELS_DIR = DATA_DIR / "reels"
LOG_FILE = DATA_DIR / "log.json"
STYLE_HISTORY_FILE = DATA_DIR / "style_history.json"

# Models and Assets Directories
MODELS_DIR = ROOT_DIR / "models"
ASSETS_DIR = ROOT_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
AUDIO_DIR = ASSETS_DIR / "audio"

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
_raw_auth_id = os.getenv("AUTHORIZED_CHAT_ID", "").strip()
AUTHORIZED_CHAT_ID = int(_raw_auth_id) if _raw_auth_id and _raw_auth_id.lstrip('-').isdigit() else None

# AI Motion Flag
USE_AI_MOTION = os.getenv("USE_AI_MOTION", "True").lower() in ("true", "1", "yes")

# Video Specs
TARGET_WIDTH = int(os.getenv("TARGET_WIDTH", 1080))
TARGET_HEIGHT = int(os.getenv("TARGET_HEIGHT", 1920))
FPS = int(os.getenv("FPS", 30))
REEL_DURATION_SEC = float(os.getenv("REEL_DURATION_SEC", 15.0))

# Ensure required directories exist
def init_directories():
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    REELS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

init_directories()
