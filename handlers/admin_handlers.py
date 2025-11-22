# handlers/admin_handlers.py

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_CHAT_ID
from handlers.common import es_admin
from repos.usuarios_repo import autorizar_usuario


async def mi_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Este comando debe funcionar incluso si el usuario NO está autorizado.
    Sirve para que pueda enviar su chat_id al administrador.
    """
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"🆔 Tu chat_id es: {chat_id}")


async def autorizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Solo el administrador puede autorizar usuarios.
    Una vez autorizado, se le envía automáticamente un mensaje con instrucciones y comandos.
    """
    chat_id = update.effective_chat.id

    # 1. Validar que quien llama sea el admin
    if not es_admin(chat_id):
        await update.message.reply_text("🚫 Solo el administrador puede autorizar usuarios.")
        return

    # 2. Validar argumento
    if len(context.args) != 1:
        await update.message.reply_text("Uso correcto:\n/autorizar <chat_id>")
        return

    # 3. Validar que el argumento sea un número
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ El chat_id debe ser un número.")
        return

    # 4. Guardar en la BD (lo marca como autorizado)
    autorizar_usuario(target_id)

    # 5. Avisar al admin que se autorizó correctamente
    await update.message.reply_text(f"✅ Usuario {target_id} autorizado.")

    # 6. Mensaje que se enviará automáticamente al usuario autorizado
    texto_para_usuario = (
        "🎉 ¡Has sido autorizado para usar el bot de gastos!\n\n"
        "Ahora puedes usar estos comandos:\n\n"
        "📌 <b>Comandos principales</b>\n"
        "• /start — Ver mensaje de bienvenida\n"
        "• /gasto Monto Categoria Descripción\n"
        "   Ej: /gasto 150 comida tacos\n"
        "• /hoy — Ver resumen del día\n"
        "\n"
        "📊 <b>Gráficas</b>\n"
        "• /grafica_hoy — Gráfica por categoría del día\n"
        "• /grafica_semana — Gastos últimos 7 días\n"
        "• /grafica_mes — Gastos del mes\n"
        "\n"
        "Si necesitas más funciones, pídele al administrador 😉"
    )

    # 7. Intentar enviar mensaje al usuario
    try:
        await context.bot.send_message(chat_id=target_id, text=texto_para_usuario, parse_mode="HTML")
    except Exception as e:
        # Ocurre si el usuario nunca inició chat con el bot
        print(f"No se pudo enviar mensaje a {target_id}: {e}")
