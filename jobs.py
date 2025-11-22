# jobs.py

from datetime import datetime

from telegram.ext import ContextTypes

from repos.usuarios_repo import obtener_chat_ids
from repos.gastos_repo import resumen_dia


async def enviar_resumen_diario(context: ContextTypes.DEFAULT_TYPE):
    """
    Job que se ejecuta diario y manda resumen a todos los usuarios autorizados.
    Se programa en main.py con job_queue.run_daily(...)
    """
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    chat_ids = obtener_chat_ids()

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
            # Por ejemplo, usuario bloqueó el bot o error de red temporal
            print(f"Error enviando resumen a {chat_id}: {e}")
