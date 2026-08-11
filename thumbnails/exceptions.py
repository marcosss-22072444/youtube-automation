"""
exceptions.py

Excepciones específicas del módulo de miniaturas.
"""

from core.exceptions import BaseAppError


class ThumbnailGenerationError(BaseAppError):
    """Se lanza cuando falla la generación de una miniatura."""
    pass