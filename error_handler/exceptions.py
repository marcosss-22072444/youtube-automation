"""
exceptions.py

Excepciones específicas del módulo de gestión de errores.
"""

from core.exceptions import BaseAppError


class ErrorHandlerError(BaseAppError):
    """Se lanza ante fallos internos del propio Error Handler."""
    pass