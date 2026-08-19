"""
factory.py

Punto único de construcción del CredentialsStore por defecto del
proyecto. Cambiar de almacenamiento local a un secret manager en la
nube en el futuro consiste en modificar únicamente esta función.
"""

from core.credentials.base import CredentialsStore
from core.credentials.local_encrypted_store import LocalEncryptedCredentialsStore

_instance: CredentialsStore | None = None


def get_default_credentials_store() -> CredentialsStore:
    """
    Devuelve el CredentialsStore por defecto del proyecto (cifrado
    local), reutilizando la misma instancia entre llamadas para no
    regenerar el objeto Fernet innecesariamente.
    """
    global _instance
    if _instance is None:
        _instance = LocalEncryptedCredentialsStore()
    return _instance