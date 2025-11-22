# handlers/charts_handlers.py

from datetime import datetime, timedelta
import os

from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import user_is_allowed
from repos.gastos_repo import categorias_por_rango, totales_por_dia
from charts import grafica_categorias, grafica_linea_fechas


async def grafica_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gráfica de gastos por categoría del día de hoy."""
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    hoy = datetime.now().date()
    fecha_str = hoy.strftime("%Y-%m-%d")

    datos = categorias_por_rango(chat_id, fecha_str, fecha_str)

    if not datos:
        await update.message.reply_text("📭 Hoy no tienes gastos registrados para graficar.")
        return

    categorias = [fila[0] for fila in datos]
    montos = [fila[1] for fila in datos]

    filename = grafica_categorias(hoy.strftime("%d/%m/%Y"), categorias, montos)

    try:
        with open(filename, "rb") as f:
            await context.bot.send_photo(chat_id=chat_id, photo=f)
    finally:
        if os.path.exists(filename):
            os.remove(filename)


async def grafica_semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gráfica de gastos diarios de los últimos 7 días (línea)."""
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    hoy = datetime.now().date()
    inicio = hoy - timedelta(days=6)  # últimos 7 días

    fecha_inicio = inicio.strftime("%Y-%m-%d")
    fecha_fin = hoy.strftime("%Y-%m-%d")

    datos = totales_por_dia(chat_id, fecha_inicio, fecha_fin)

    if not datos:
        await update.message.reply_text("📭 No tienes gastos en los últimos 7 días para graficar.")
        return

    # mapa fecha -> total
    mapa_totales = {fila[0]: fila[1] for fila in datos}

    fechas_rango = [inicio + timedelta(days=i) for i in range(7)]
    labels = [f.strftime("%d/%m") for f in fechas_rango]
    valores = [mapa_totales.get(f.strftime("%Y-%m-%d"), 0) for f in fechas_rango]

    titulo = "Gastos diarios – últimos 7 días"
    filename = grafica_linea_fechas(titulo, labels, valores)

    try:
        with open(filename, "rb") as f:
            await context.bot.send_photo(chat_id=chat_id, photo=f)
    finally:
        if os.path.exists(filename):
            os.remove(filename)


async def grafica_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gráfica de gastos por categoría del mes actual."""
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    hoy = datetime.now().date()
    inicio_mes = hoy.replace(day=1)

    fecha_inicio = inicio_mes.strftime("%Y-%m-%d")
    fecha_fin = hoy.strftime("%Y-%m-%d")

    datos = categorias_por_rango(chat_id, fecha_inicio, fecha_fin)

    if not datos:
        await update.message.reply_text("📭 No tienes gastos en este mes para graficar.")
        return

    categorias = [fila[0] for fila in datos]
    montos = [fila[1] for fila in datos]

    label_mes = hoy.strftime("%m/%Y")
    filename = grafica_categorias(label_mes, categorias, montos)

    try:
        with open(filename, "rb") as f:
            await context.bot.send_photo(chat_id=chat_id, photo=f)
    finally:
        if os.path.exists(filename):
            os.remove(filename)
