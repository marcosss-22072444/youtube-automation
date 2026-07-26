"""
exceptions.py

Excepciones específicas del módulo de ideas.
"""

from core.exceptions import BaseAppError


class IdeaNotFoundError(BaseAppError):
    """Se lanza cuando se busca una idea por id y no existe."""
    pass


class IdeaGenerationError(BaseAppError):
    """Se lanza cuando la IA falla al generar una idea nueva y original."""
    pass