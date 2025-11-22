# main.py
from telegram.ext import ApplicationBuilder, CommandHandler
from datetime import time

from config import TELEGRAM_TOKEN, ADMIN_CHAT_ID
from db import init_db
from repos.usuarios_repo import autorizar_usuario
from jobs import enviar_resumen_diario
from handlers.admin_handlers import mi_id, autorizar
from handlers.gastos_handlers import start, gasto, hoy
from handlers.charts_handlers import grafica_hoy, grafica_semana, grafica_mes


def main():
    init_db()
    autorizar_usuario(ADMIN_CHAT_ID)  # admin siempre autorizado

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("mi_id", mi_id))
    app.add_handler(CommandHandler("autorizar", autorizar))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("hoy", hoy))
    app.add_handler(CommandHandler("grafica_hoy", grafica_hoy))
    app.add_handler(CommandHandler("grafica_semana", grafica_semana))
    app.add_handler(CommandHandler("grafica_mes", grafica_mes))

    job_queue = app.job_queue
    job_queue.run_daily(enviar_resumen_diario, time=time(20, 0))

    print("Bot corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()
