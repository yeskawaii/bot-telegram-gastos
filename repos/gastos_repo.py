# repos/gastos_repo.py
from datetime import datetime
from db import get_connection

def agregar_gasto(chat_id: int, monto: float, categoria: str, descripcion: str | None = None):
    conn = get_connection()
    cur = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d")
    cur.execute(
        "INSERT INTO gastos (chat_id, fecha, monto, categoria, descripcion) VALUES (?, ?, ?, ?, ?)",
        (chat_id, fecha, monto, categoria, descripcion),
    )
    conn.commit()
    conn.close()


def resumen_dia(chat_id: int, fecha: str):
    conn = get_connection()
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
    conn = get_connection()
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
    conn = get_connection()
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
