"""
exceptions.py

Excepciones específicas del módulo de metadata.
"""

from core.exceptions import BaseAppError


class MetadataGenerationError(BaseAppError):
    """Se lanza cuando la IA falla al generar título/descripción/etiquetas."""
    pass