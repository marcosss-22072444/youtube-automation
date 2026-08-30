"""manager.py — API de alto nivel: get_setting() con fallback, set_setting() upsert JSON."""
import json
from typing import Any

from channel_settings import repository
from core.logger import get_logger

logger = get_logger(__name__)


def get_setting(channel_id: int, key: str, default: Any = None) -> Any:
    """Devuelve el ajuste del canal si existe; si no, default (global)."""
    raw = repository.get_raw(channel_id, key)
    if raw is None:
        return default
    return json.loads(raw)


def set_setting(channel_id: int, key: str, value: Any) -> None:
    """Guarda (crea o actualiza) un ajuste para el canal."""
    repository.set_raw(channel_id, key, json.dumps(value))
    logger.info(f"Canal {channel_id}: ajuste '{key}' actualizado.")


def delete_setting(channel_id: int, key: str) -> None:
    """Elimina el ajuste propio del canal (vuelve a usar el global)."""
    repository.delete_setting(channel_id, key)
    logger.info(f"Canal {channel_id}: ajuste '{key}' eliminado, usará fallback global.")


def list_settings(channel_id: int) -> dict:
    return repository.list_settings_for_channel(channel_id)