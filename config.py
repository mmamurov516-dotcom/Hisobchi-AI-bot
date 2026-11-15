import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_raw_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
# Agar Render sozlamalarida eski gemini-3.5-flash qolgan bo'lsa ham avtomatik flash-lite ishlatiladi
if _raw_model in ["gemini-3.5-flash", "gemini-2.5-flash"]:
    GEMINI_MODEL = "gemini-3.5-flash-lite"
else:
    GEMINI_MODEL = _raw_model
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "accounting_bot.db")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN ko'rsatilmagan! .env faylini tekshiring.")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY ko'rsatilmagan! .env faylini tekshiring.")
