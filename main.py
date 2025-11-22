# main.py

import matplotlib.pyplot as plt
import tempfile

from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, time, timedelta

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from db import (
    init_db,
    autorizar_usuario,
    esta_autorizado,
    actualizar_datos_usuario,
    obtener_chat_ids,
    agregar_gasto,
    resumen_dia,
    categorias_por_rango,
    totales_por_dia,
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# ---------- Helpers ----------
def es_admin(chat_id: int) -> bool:
    return chat_id == ADMIN_CHAT_ID

def user_is_allowed(chat_id: int) -> bool:
    return es_admin(chat_id) or esta_autorizado(chat_id)

# ---------- Comandos ----------

async def mi_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"🆔 Tu chat_id es: {chat_id}")
    
async def autorizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not es_admin(chat_id):
        await update.message.reply_text("🚫 Solo el administrador puede autorizar usuarios.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Uso: /autorizar <chat_id>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("El chat_id debe ser un número.")
        return

    autorizar_usuario(target_id)
    await update.message.reply_text(f"✅ Usuario {target_id} autorizado.")

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text="✅ Has sido autorizado para usar el bot de gastos."
        )
    except Exception:
        pass
    
# ---------- Comandos principales ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    user = update.effective_user
    actualizar_datos_usuario(chat_id, user.username, user.first_name)

    await update.message.reply_text(
        f"👋 ¡Hola {user.first_name or 'amix'}! Ya quedaste registrado para resúmenes diarios.\n\n"
        "Comandos:\n"
        "• /gasto Monto Categoria Descripción opcional\n"
        "• /hoy - ver resumen de hoy"
    )


async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Uso:\n"
            "/gasto Monto Categoria Descripción opcional\n"
            "Ej: /gasto 150 comida tacos al pastor"
        )
        return

    try:
        monto = float(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ El monto debe ser un número. Ej: /gasto 150 comida")
        return

    categoria = context.args[1]
    descripcion = " ".join(context.args[2:]) if len(context.args) > 2 else ""

    agregar_gasto(chat_id, monto, categoria, descripcion or None)

    await update.message.reply_text(
        f"✅ Gasto registrado:\n"
        f"💰 Monto: {monto}\n"
        f"📂 Categoría: {categoria}\n"
        f"📝 Descripción: {descripcion if descripcion else '(sin descripción)'}"
    )

async def hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    total, por_categoria = resumen_dia(chat_id, fecha_hoy)

    if total == 0:
        await update.message.reply_text("📭 Hoy no tienes gastos registrados.")
        return

    texto = [f"📅 Resumen de hoy ({fecha_hoy}):"]
    texto.append(f"💰 Total del día: {total:.2f}")

    if por_categoria:
        texto.append("\n📂 Por categoría:")
        for cat, monto in por_categoria:
            texto.append(f"• {cat}: {monto:.2f}")

    await update.message.reply_text("\n".join(texto))

async def grafica_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    datos = categorias_por_rango(chat_id, fecha_hoy, fecha_hoy)

    if not datos:
        await update.message.reply_text("📭 Hoy no tienes gastos registrados para graficar.")
        return

    categorias = [fila[0] for fila in datos]
    montos = [fila[1] for fila in datos]

    # 🎨 Estilo bonito global
    plt.style.use("seaborn-v0_8")

    # 🎨 Paleta personalizada
    colores = [
        "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
        "#59a14f", "#edc949", "#af7aa1", "#ff9da7",
    ]

    plt.figure(figsize=(8, 5))

    # Gráfica de barras
    plt.bar(
        categorias,
        montos,
        color=colores[:len(categorias)],
        edgecolor="black",
        linewidth=1,
    )

    # Mejoras visuales
    plt.title(f"Gastos por categoría – {fecha_hoy}", fontsize=16, fontweight="bold")
    plt.xlabel("Categoría", fontsize=12)
    plt.ylabel("Monto", fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()

    # Guardar en archivo temporal
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        filename = tmp.name
        plt.savefig(filename, dpi=200)

    plt.close()

    # Enviar imagen
    with open(filename, "rb") as f:
        await context.bot.send_photo(chat_id=chat_id, photo=f)

    os.remove(filename)

async def grafica_semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    hoy = datetime.now().date()
    inicio = hoy - timedelta(days=6)  # últimos 7 días (hoy incluido)

    fecha_inicio = inicio.strftime("%Y-%m-%d")
    fecha_fin = hoy.strftime("%Y-%m-%d")

    datos = totales_por_dia(chat_id, fecha_inicio, fecha_fin)

    if not datos:
        await update.message.reply_text("📭 No tienes gastos en los últimos 7 días para graficar.")
        return

    # Crear un mapa fecha -> total
    mapa_totales = {fila[0]: fila[1] for fila in datos}

    # Lista de todas las fechas del rango, aunque no haya gasto (se muestran como 0)
    fechas_rango = [
        (inicio + timedelta(days=i)) for i in range(7)
    ]
    labels = [f.strftime("%d/%m") for f in fechas_rango]
    valores = [mapa_totales.get(f.strftime("%Y-%m-%d"), 0) for f in fechas_rango]

    # 🎨 Estilo
    plt.style.use("seaborn-v0_8")
    colores = "#4e79a7"  # un color bonito para la línea

    plt.figure(figsize=(8, 5))

    # Gráfica de línea + marcadores
    plt.plot(labels, valores, marker="o", linestyle="-", color=colores)

    plt.title("Gastos diarios – últimos 7 días", fontsize=16, fontweight="bold")
    plt.xlabel("Día", fontsize=12)
    plt.ylabel("Monto", fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()

    # Guardar en archivo temporal
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        filename = tmp.name
        plt.savefig(filename, dpi=200)

    plt.close()

    # Enviar imagen
    with open(filename, "rb") as f:
        await context.bot.send_photo(chat_id=chat_id, photo=f)

    os.remove(filename)

async def grafica_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # 🎨 Estilo bonito
    plt.style.use("seaborn-v0_8")
    colores = [
        "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
        "#59a14f", "#edc949", "#af7aa1", "#ff9da7",
    ]

    plt.figure(figsize=(8, 5))

    plt.bar(
        categorias,
        montos,
        color=colores[:len(categorias)],
        edgecolor="black",
        linewidth=1,
    )

    plt.title(f"Gastos por categoría – {hoy.strftime('%m/%Y')}", fontsize=16, fontweight="bold")
    plt.xlabel("Categoría", fontsize=12)
    plt.ylabel("Monto", fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        filename = tmp.name
        plt.savefig(filename, dpi=200)

    plt.close()

    with open(filename, "rb") as f:
        await context.bot.send_photo(chat_id=chat_id, photo=f)

    os.remove(filename)


# ---------- Tarea programada (resumen diario) ----------

async def enviar_resumen_diario(context: ContextTypes.DEFAULT_TYPE):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    chat_ids = obtener_chat_ids()  # solo usuarios autorizados

    for chat_id in chat_ids:
        total, por_categoria = resumen_dia(chat_id, fecha_hoy)

        if total == 0:
            texto = f"📅 Hoy ({fecha_hoy}) no registraste gastos."
        else:
            partes = [
                f"📅 Resumen de hoy ({fecha_hoy}):",
                f"💰 Total del día: {total:.2f}",
            ]

            if por_categoria:
                partes.append("\n📂 Por categoría:")
                for cat, monto in por_categoria:
                    partes.append(f"• {cat}: {monto:.2f}")

            texto = "\n".join(partes)

        try:
            await context.bot.send_message(chat_id=chat_id, text=texto)
        except Exception as e:
            print(f"Error enviando resumen a {chat_id}: {e}")
            
            
# ---------- Main ----------

def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Falta la variable de entorno TELEGRAM_TOKEN")

    init_db()

    # Opcional: asegúrate de que el admin esté autorizado desde el inicio
    autorizar_usuario(ADMIN_CHAT_ID)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # utilitarios
    app.add_handler(CommandHandler("mi_id", mi_id))
    app.add_handler(CommandHandler("autorizar", autorizar))

    # comandos normales
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("hoy", hoy))
    app.add_handler(CommandHandler("grafica_hoy", grafica_hoy))
    app.add_handler(CommandHandler("grafica_semana", grafica_semana))
    app.add_handler(CommandHandler("grafica_mes", grafica_mes))

    # job diario
    job_queue = app.job_queue
    hora_envio = time(hour=20, minute=0)
    job_queue.run_daily(enviar_resumen_diario, time=hora_envio)

    print("Bot corriendo localmente...")
    app.run_polling()


if __name__ == "__main__":
    main()