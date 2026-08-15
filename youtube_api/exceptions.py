"""
exceptions.py

Excepciones específicas del módulo de la API de YouTube.
"""

from core.exceptions import BaseAppError


class YouTubeAuthError(BaseAppError):
    """Se lanza cuando falla la autenticación OAuth de un canal."""
    pass


class YouTubeUploadError(BaseAppError):
    """Se lanza cuando falla la subida de un vídeo a YouTube."""
    pass