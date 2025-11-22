# handlers/__init__.py
"""
Paquete de handlers de Telegram.
Divide la lógica del bot en archivos por tema:

- common.py         -> funciones de ayuda (auth, admin)
- admin_handlers.py -> comandos de administrador (/mi_id, /autorizar, etc.)
- gastos_handlers.py-> comandos de uso normal (/start, /gasto, /hoy, ...)
- charts_handlers.py-> comandos de gráficas (/grafica_hoy, /grafica_semana, /grafica_mes)
"""
