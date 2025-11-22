# handlers/gastos_handlers.py
from datetime import datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

from handlers.common import user_is_allowed
from repos.usuarios_repo import actualizar_datos_usuario
from repos.gastos_repo import agregar_gasto, resumen_dia

MONTO, CATEGORIA, DESCRIPCION = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.effective_message.reply_text(
            "🚫 Todavía no estás autorizado para usar este bot.\n\n"
            "👉 Para solicitar acceso:\n"
            "1. Envía el comando /mi_id para ver tu *chat_id*.\n"
            "2. Envía ese número al administrador del bot."
        )
        return

    user = update.effective_user
    actualizar_datos_usuario(chat_id, user.username, user.first_name)

    keyboard = [
        [InlineKeyboardButton("➕ Nuevo gasto", callback_data="nuevo_gasto")],
        [
            InlineKeyboardButton("📅 Hoy", callback_data="hoy"),
            InlineKeyboardButton("📈 Semana", callback_data="semana"),
            InlineKeyboardButton("📊 Mes", callback_data="mes"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(
        f"👋 ¡Hola {user.first_name or 'amix'}!\n"
        "¿Qué quieres hacer hoy?",
        reply_markup=reply_markup
    )

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.effective_message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    if len(context.args) < 2:
        await update.effective_message.reply_text(
            "Uso:\n"
            "/gasto Monto Categoria Descripción opcional\n"
            "Ej: /gasto 150 comida tacos al pastor"
        )
        return

    try:
        monto = float(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("❌ El monto debe ser un número. Ej: /gasto 150 comida")
        return

    categoria = context.args[1]
    descripcion = " ".join(context.args[2:]) if len(context.args) > 2 else ""

    agregar_gasto(chat_id, monto, categoria, descripcion or None)

    await update.effective_message.reply_text(
        f"✅ Gasto registrado:\n"
        f"💰 Monto: {monto}\n"
        f"📂 Categoría: {categoria}\n"
        f"📝 Descripción: {descripcion if descripcion else '(sin descripción)'}"
    )


async def hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.effective_message.reply_text("🚫 No estás autorizado para usar este bot.")
        return

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    total, por_categoria = resumen_dia(chat_id, fecha_hoy)

    if total == 0:
        await update.effective_message.reply_text("📭 Hoy no tienes gastos registrados.")
        return

    texto = [f"📅 Resumen de hoy ({fecha_hoy}):"]
    texto.append(f"💰 Total del día: {total:.2f}")

    if por_categoria:
        texto.append("\n📂 Por categoría:")
        for cat, monto in por_categoria:
            texto.append(f"• {cat}: {monto:.2f}")

    await update.effective_message.reply_text("\n".join(texto))
    
# apartado de gastos paso a paso  (ConversationHandler)

async def nuevo_gasto_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not user_is_allowed(chat_id):
        await update.effective_message.reply_text("🚫 No estás autorizado para usar este bot.")
        return ConversationHandler.END

    await update.effective_message.reply_text(
        "💸 Vamos a registrar un nuevo gasto.\n\n"
        "Primero dime, ¿cuánto gastaste? (solo el número, ej: 150)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return MONTO


async def nuevo_gasto_monto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    try:
        monto = float(text.replace(",", "."))
    except ValueError:
        await update.effective_message.reply_text("❌ El monto debe ser un número. Intenta de nuevo (ej: 150).")
        return MONTO

    context.user_data["monto"] = monto

    # Teclado de categorías
    keyboard = [
        ["comida", "transporte", "servicios"],
        ["renta", "salud", "otros"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.effective_message.reply_text(
        "📂 ¿En qué categoría entra este gasto?\n"
        "Puedes elegir un botón o escribir otra categoría.",
        reply_markup=reply_markup,
    )
    return CATEGORIA


async def nuevo_gasto_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categoria = update.message.text.strip().lower()
    context.user_data["categoria"] = categoria

    await update.effective_message.reply_text(
        "📝 Escribe una breve descripción del gasto.\n"
        "Si no quieres poner descripción, manda solo un guion (-).",
        reply_markup=ReplyKeyboardRemove(),
    )
    return DESCRIPCION


async def nuevo_gasto_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    descripcion = update.message.text.strip()
    if descripcion == "-":
        descripcion = ""

    monto = context.user_data.get("monto")
    categoria = context.user_data.get("categoria")

    agregar_gasto(chat_id, monto, categoria, descripcion or None)

    await update.effective_message.reply_text(
        "✅ Gasto registrado:\n"
        f"💰 Monto: {monto}\n"
        f"📂 Categoría: {categoria}\n"
        f"📝 Descripción: {descripcion if descripcion else '(sin descripción)'}"
    )

    # Limpiar datos de la conversación
    context.user_data.clear()

    # Ofrecer comandos otra vez
    await start(update, context)  # reusa el mensaje de inicio con botones

    return ConversationHandler.END


async def nuevo_gasto_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text(
        "❌ Registro de gasto cancelado.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END
