"""
exceptions.py

Excepciones específicas de los proveedores de medios (vídeos de stock).
"""

from core.exceptions import BaseAppError


class ProviderUnavailableError(BaseAppError):
    """
    Se lanza cuando un proveedor de stock falla de forma que indica
    que está bloqueado/caído (ej: 429, error de red), a diferencia de
    una búsqueda concreta sin resultados (que no es un error).
    """
    pass