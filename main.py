# main.py

from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, time

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

    # job diario
    job_queue = app.job_queue
    hora_envio = time(hour=20, minute=0)
    job_queue.run_daily(enviar_resumen_diario, time=hora_envio)

    print("Bot corriendo localmente...")
    app.run_polling()


if __name__ == "__main__":
    main()