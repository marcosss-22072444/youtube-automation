"""
exceptions.py

Excepciones específicas del módulo de canales. Heredan de BaseAppError
para poder capturarse también de forma genérica desde el resto del
proyecto si hace falta.
"""

from core.exceptions import BaseAppError


class ChannelNotFoundError(BaseAppError):
    """Se lanza cuando se busca un canal por id y no existe."""
    pass


class DuplicateChannelNameError(BaseAppError):
    """Se lanza al intentar crear un canal con un nombre ya existente."""
    pass