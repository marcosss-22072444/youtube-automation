"""
exceptions.py

Excepciones específicas del módulo de estadísticas.
"""

from core.exceptions import BaseAppError


class StatsCollectionError(BaseAppError):
    """Se lanza cuando falla la recogida de estadísticas desde YouTube."""
    pass