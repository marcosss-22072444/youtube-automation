"""
exceptions.py

Excepciones específicas del módulo de investigación/verificación factual.
"""

from core.exceptions import BaseAppError


class SearchProviderError(BaseAppError):
    """Se lanza cuando falla la búsqueda web (fallo real, no 'sin resultados')."""
    pass


class FactExtractionError(BaseAppError):
    """Se lanza cuando falla la extracción estructurada de hechos desde las fuentes."""
    pass