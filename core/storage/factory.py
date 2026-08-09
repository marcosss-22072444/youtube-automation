"""
factory.py

Punto único de construcción del backend de almacenamiento por
defecto del proyecto. Cambiar de almacenamiento local a uno en la
nube en el futuro consiste en modificar únicamente esta función.
"""

from core.storage.base import StorageBackend
from core.storage.local_storage import LocalStorage


def get_default_storage() -> StorageBackend:
    """Devuelve el backend de almacenamiento por defecto del proyecto (local)."""
    return LocalStorage()