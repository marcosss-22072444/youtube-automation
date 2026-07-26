"""
manager.py

Lógica de negocio para gestionar canales. Esta es la capa que debe
usar el resto de la aplicación (scheduler, remote_api, etc.) — nunca
deben llamar directamente a channels.repository.
"""

from channels import repository
from channels.models import Channel
from channels.exceptions import ChannelNotFoundError
from core.exceptions import ConfigError
from core.logger import get_logger

logger = get_logger(__name__)

_VALID_STATUSES = ("active", "paused")


def _validate_channel_data(name: str, topic: str, shorts_per_week: int, long_videos_per_week: int):
    if not name or not name.strip():
        raise ConfigError("El nombre del canal no puede estar vacío.")

    if not topic or not topic.strip():
        raise ConfigError("La temática del canal no puede estar vacía.")

    if shorts_per_week < 0 or long_videos_per_week < 0:
        raise ConfigError("La frecuencia de publicación no puede ser negativa.")

    if shorts_per_week == 0 and long_videos_per_week == 0:
        raise ConfigError(
            "El canal debe publicar al menos un short o un vídeo largo por semana."
        )


def create_channel(name: str, topic: str, shorts_per_week: int = 0, long_videos_per_week: int = 0) -> Channel:
    """Crea y guarda un canal nuevo, validando los datos antes."""
    _validate_channel_data(name, topic, shorts_per_week, long_videos_per_week)

    channel = Channel(
        name=name.strip(),
        topic=topic.strip(),
        shorts_per_week=shorts_per_week,
        long_videos_per_week=long_videos_per_week,
    )

    saved_channel = repository.create(channel)
    logger.info(f"Canal creado: '{saved_channel.name}' (id={saved_channel.id})")
    return saved_channel


def get_channel(channel_id: int) -> Channel:
    """Obtiene un canal por su id."""
    return repository.get_by_id(channel_id)


def list_channels(only_active: bool = False) -> list[Channel]:
    """Lista todos los canales, o solo los activos si only_active=True."""
    channels = repository.list_all()
    if only_active:
        return [c for c in channels if c.is_active]
    return channels


def pause_channel(channel_id: int) -> Channel:
    """Pausa un canal (deja de publicarse en él)."""
    channel = repository.get_by_id(channel_id)
    channel.status = "paused"
    repository.update(channel)
    logger.info(f"Canal pausado: '{channel.name}' (id={channel.id})")
    return channel


def activate_channel(channel_id: int) -> Channel:
    """Reactiva un canal pausado."""
    channel = repository.get_by_id(channel_id)
    channel.status = "active"
    repository.update(channel)
    logger.info(f"Canal activado: '{channel.name}' (id={channel.id})")
    return channel


def delete_channel(channel_id: int) -> None:
    """Elimina un canal permanentemente."""
    channel = repository.get_by_id(channel_id)  # lanza ChannelNotFoundError si no existe
    repository.delete(channel_id)
    logger.info(f"Canal eliminado: '{channel.name}' (id={channel_id})")