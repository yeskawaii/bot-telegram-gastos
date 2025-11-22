# main.py
from datetime import time

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_TOKEN, ADMIN_CHAT_ID
from db import init_db
from repos.usuarios_repo import autorizar_usuario
from jobs import enviar_resumen_diario
from handlers.admin_handlers import mi_id, autorizar
from handlers.charts_handlers import grafica_hoy, grafica_semana, grafica_mes
from handlers.gastos_handlers import (
    start,
    gasto,
    hoy,
    nuevo_gasto_start,
    nuevo_gasto_monto,
    nuevo_gasto_categoria,
    nuevo_gasto_descripcion,
    nuevo_gasto_cancel,
    MONTO,
    CATEGORIA,
    DESCRIPCION,
)


async def botones_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los botones inline que NO son parte de la conversación de nuevo gasto."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "hoy":
        return await hoy(update, context)
    if data == "semana":
        return await grafica_semana(update, context)
    if data == "mes":
        return await grafica_mes(update, context)


def main():
    init_db()
    autorizar_usuario(ADMIN_CHAT_ID)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # 👇 Conversación para /nuevo_gasto, entrada por comando o por botón inline
    conv_nuevo_gasto = ConversationHandler(
        entry_points=[
            CommandHandler("nuevo_gasto", nuevo_gasto_start),
            CallbackQueryHandler(nuevo_gasto_start, pattern="^nuevo_gasto$"),
        ],
        states={
            MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, nuevo_gasto_monto)],
            CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, nuevo_gasto_categoria)],
            DESCRIPCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, nuevo_gasto_descripcion)],
        },
        fallbacks=[CommandHandler("cancelar", nuevo_gasto_cancel)],
    )
    app.add_handler(conv_nuevo_gasto)

    # 👇 Botones inline para hoy / semana / mes
    app.add_handler(CallbackQueryHandler(botones_handler, pattern="^(hoy|semana|mes)$"))

    # Admin
    app.add_handler(CommandHandler("mi_id", mi_id))
    app.add_handler(CommandHandler("autorizar", autorizar))

    # Uso normal
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("hoy", hoy))

    # Gráficas por comando (además de botones)
    app.add_handler(CommandHandler("grafica_hoy", grafica_hoy))
    app.add_handler(CommandHandler("grafica_semana", grafica_semana))
    app.add_handler(CommandHandler("grafica_mes", grafica_mes))

    # Job diario
    job_queue = app.job_queue
    job_queue.run_daily(enviar_resumen_diario, time=time(20, 0))

    print("Bot corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()
