# db.py
import sqlite3
from config import DB_DIR, DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            chat_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            moneda TEXT DEFAULT '$',
            creado_en TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            monto REAL NOT NULL,
            categoria TEXT NOT NULL,
            descripcion TEXT
        )
        """
    )

    conn.commit()
    conn.close()
