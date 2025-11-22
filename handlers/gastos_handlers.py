# handlers/gastos_handlers.py
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import user_is_allowed
from repos.usuarios_repo import actualizar_datos_usuario
from repos.gastos_repo import agregar_gasto, resumen_dia

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if not user_is_allowed(chat_id):
        await update.message.reply_text(
            "🚫 Todavía no estás autorizado para usar este bot.\n\n"
            "👉 Para solicitar acceso:\n"
            "1. Envía el comando /mi_id para ver tu *chat_id*.\n"
            "2. Envía ese número al administrador del bot.\n\n"
            "Cuando el admin te autorice, recibirás un mensaje con las instrucciones y comandos disponibles. 😊"
        )
        return

    # Aquí ya está autorizado
    actualizar_datos_usuario(chat_id, user.username, user.first_name)

    await update.message.reply_text(
        f"👋 ¡Hola {user.first_name or 'amix'}! Ya tienes acceso al bot de gastos.\n\n"
        "Comandos:\n"
        "• /gasto Monto Categoria Descripción opcional\n"
        "   Ej: /gasto 150 comida tacos al pastor\n"
        "• /hoy - ver resumen de hoy (total + categorías)\n"
        "• /grafica_hoy - gráfica por categoría de hoy\n"
        "• /grafica_semana - gráfica de los últimos 7 días\n"
        "• /grafica_mes - gráfica por categoría del mes actual\n"
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
