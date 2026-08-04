"""
factory.py

Punto único de construcción del proveedor de imágenes por defecto del
proyecto. Cambiar de SDXL local a FLUX, otro modelo local, o una API
en el futuro consiste en modificar únicamente esta función.
"""

from core.image_providers.base import ImageProvider
from core.image_providers.sdxl_local_provider import SDXLLocalProvider


def get_default_image_provider() -> ImageProvider:
    """Devuelve el proveedor de imágenes por defecto del proyecto (SDXL local)."""
    return SDXLLocalProvider()