# db.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_DIR = Path("data")
DB_PATH = DB_DIR / "gastos.db"


def init_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Tabla de gastos
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

    # Tabla de usuarios AUTORIZADOS
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

    conn.commit()
    conn.close()

# ----- AUTORIZACIÓN -----

def autorizar_usuario(chat_id: int):
    """Crea el registro del usuario en la BD (lo marca como autorizado)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO usuarios (chat_id, creado_en)
        VALUES (?, ?)
        """,
        (chat_id, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()
    
def esta_autorizado(chat_id: int) -> bool:
    """Un usuario está autorizado si existe en la tabla usuarios."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM usuarios WHERE chat_id = ?", (chat_id,))
    res = cur.fetchone()
    conn.close()
    return res is not None

# ----- USUARIOS REGISTRADOS -----

def actualizar_datos_usuario(chat_id: int, username: str | None, first_name: str | None):
    """Actualiza username/first_name del usuario ya autorizado."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE usuarios
        SET username = ?, first_name = ?
        WHERE chat_id = ?
        """,
        (username, first_name, chat_id),
    )
    conn.commit()
    conn.close()

def obtener_chat_ids():
    """Todos los usuarios autorizados (para resumen diario)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM usuarios")
    filas = cur.fetchall()
    conn.close()
    return [f[0] for f in filas]

# ----- GASTOS -----


def agregar_gasto(chat_id: int, monto: float, categoria: str, descripcion: str | None = None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d")
    cur.execute(
        "INSERT INTO gastos (chat_id, fecha, monto, categoria, descripcion) VALUES (?, ?, ?, ?, ?)",
        (chat_id, fecha, monto, categoria, descripcion),
    )
    conn.commit()
    conn.close()

def resumen_dia(chat_id: int, fecha: str | None = None):
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE chat_id = ? AND fecha = ?",
        (chat_id, fecha),
    )
    total = cur.fetchone()[0] or 0

    cur.execute(
        """
        SELECT categoria, COALESCE(SUM(monto), 0)
        FROM gastos
        WHERE chat_id = ? AND fecha = ?
        GROUP BY categoria
        ORDER BY SUM(monto) DESC
        """,
        (chat_id, fecha),
    )
    por_categoria = cur.fetchall()
    conn.close()

    return total, por_categoria

def categorias_por_rango(chat_id: int, fecha_inicio: str, fecha_fin: str):
    """
    Devuelve lista [(categoria, total_categoria), ...] entre fecha_inicio y fecha_fin (YYYY-MM-DD).
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT categoria, COALESCE(SUM(monto), 0)
        FROM gastos
        WHERE chat_id = ?
          AND fecha BETWEEN ? AND ?
        GROUP BY categoria
        ORDER BY SUM(monto) DESC
        """,
        (chat_id, fecha_inicio, fecha_fin),
    )
    filas = cur.fetchall()
    conn.close()
    return filas

def totales_por_dia(chat_id: int, fecha_inicio: str, fecha_fin: str):
    """
    Devuelve lista [(fecha, total_dia), ...] entre fecha_inicio y fecha_fin (YYYY-MM-DD),
    agrupado por fecha.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT fecha, COALESCE(SUM(monto), 0) AS total
        FROM gastos
        WHERE chat_id = ?
          AND fecha BETWEEN ? AND ?
        GROUP BY fecha
        ORDER BY fecha ASC
        """,
        (chat_id, fecha_inicio, fecha_fin),
    )
    filas = cur.fetchall()
    conn.close()
    return filas