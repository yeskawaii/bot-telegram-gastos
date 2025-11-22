# repos/usuarios_repo.py
from datetime import datetime
from db import get_connection

def autorizar_usuario(chat_id: int):
    conn = get_connection()
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM usuarios WHERE chat_id = ?", (chat_id,))
    res = cur.fetchone()
    conn.close()
    return res is not None


def actualizar_datos_usuario(chat_id: int, username: str | None, first_name: str | None):
    conn = get_connection()
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM usuarios")
    filas = cur.fetchall()
    conn.close()
    return [f[0] for f in filas]