"""exceptions.py — Excepciones del módulo de ajustes por canal."""
from core.exceptions import BaseAppError

class ChannelSettingError(BaseAppError):
    """Se lanza ante fallos al leer/escribir un ajuste de canal."""
    pass