"""
exceptions.py

Excepciones específicas del módulo de guiones.
"""

from core.exceptions import BaseAppError


class ScriptNotFoundError(BaseAppError):
    """Se lanza cuando se busca un guion por id y no existe."""
    pass


class ScriptGenerationError(BaseAppError):
    """Se lanza cuando la IA falla al generar un guion."""
    pass