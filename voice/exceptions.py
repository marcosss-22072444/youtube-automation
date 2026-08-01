"""
exceptions.py

Excepciones específicas del módulo de voz.
"""

from core.exceptions import BaseAppError


class VoiceTrackNotFoundError(BaseAppError):
    """Se lanza cuando se busca un audio por id y no existe."""
    pass