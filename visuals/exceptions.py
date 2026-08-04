"""
exceptions.py

Excepciones específicas del módulo de visuales.
"""

from core.exceptions import BaseAppError


class SceneSplittingError(BaseAppError):
    """Se lanza cuando la IA falla al dividir el guion en escenas."""
    pass