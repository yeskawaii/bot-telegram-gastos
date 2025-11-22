# config.py
from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta TELEGRAM_TOKEN en .env")

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))  # lo pones tú en .env

DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "gastos.db"
