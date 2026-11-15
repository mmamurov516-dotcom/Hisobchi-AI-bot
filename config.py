import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "accounting_bot.db")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN ko'rsatilmagan! .env faylini tekshiring.")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY ko'rsatilmagan! .env faylini tekshiring.")
