# handlers/common.py
from config import ADMIN_CHAT_ID
from repos.usuarios_repo import esta_autorizado

def es_admin(chat_id: int) -> bool:
    return chat_id == ADMIN_CHAT_ID

def user_is_allowed(chat_id: int) -> bool:
    return es_admin(chat_id) or esta_autorizado(chat_id)
