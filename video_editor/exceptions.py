"""
exceptions.py

Excepciones específicas del módulo de montaje de vídeo.
"""

from core.exceptions import BaseAppError


class VideoAssemblyError(BaseAppError):
    """Se lanza cuando falla el montaje del vídeo final (FFmpeg u otro paso)."""
    pass