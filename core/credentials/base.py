"""
base.py

Define el contrato (interfaz) que debe cumplir cualquier almacén de
credenciales por canal. Es la ÚNICA capa autorizada a manejar
credenciales en texto plano (solo en memoria, nunca en logs ni
respuestas). Cambiar de almacenamiento local cifrado a un secret
manager en la nube en el futuro consiste en crear una nueva clase que
herede de CredentialsStore.
"""

from abc import ABC, abstractmethod


class CredentialsStore(ABC):
    """Interfaz abstracta para el almacén de credenciales por canal."""
def resolve_credential(
    channel_id: int,
    provider_name: str,
    global_value: str | None,
    store: "CredentialsStore",
) -> str | None:
    """
    Resuelve qué credencial usar para un canal y proveedor concretos:
    1. Si el canal tiene una credencial propia, se usa esa.
    2. Si no, y el fallback global está activado (config.yaml:
       credentials.allow_global_fallback), se usa la clave global de
       .env, registrando el uso del fallback SIN mostrar el valor.
    3. Si no hay ni credencial propia ni fallback disponible, devuelve None.
    """
    from core.config import settings
    from core.logger import get_logger

    logger = get_logger("core.credentials")

    channel_value = store.get(channel_id, provider_name)
    if channel_value:
        return channel_value

    if settings.credentials.get("allow_global_fallback", True) and global_value:
        logger.info(f"Canal {channel_id}: usando credencial global de {provider_name} como fallback.")
        return global_value

    return None

    @abstractmethod
    def get(self, channel_id: int, provider_name: str) -> str | None:
        """
        Devuelve la credencial guardada para ese canal y proveedor, o
        None si no existe ninguna credencial propia para ese canal.
        """
        raise NotImplementedError

    @abstractmethod
    def set(self, channel_id: int, provider_name: str, value: str) -> None:
        """Guarda (o sobrescribe) una credencial para ese canal y proveedor."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, channel_id: int, provider_name: str) -> None:
        """Elimina la credencial guardada para ese canal y proveedor, si existe."""
        raise NotImplementedError

    @abstractmethod
    def list_configured_providers(self, channel_id: int) -> list[str]:
        """
        Devuelve la lista de nombres de proveedor que tienen credencial
        propia configurada para ese canal (sin revelar los valores) —
        pensado para que una futura UI muestre qué está configurado.
        """
        raise NotImplementedError