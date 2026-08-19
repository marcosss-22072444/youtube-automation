"""
manager.py

Lógica de negocio para gestionar horarios de canales. Esta es la capa
que debe usar el resto de la aplicación (y, en el futuro, la Remote
API para la app de escritorio/Android) — nunca deben llamar
directamente a scheduler.repository.
"""

from scheduler import repository
from scheduler.models import ScheduleEntry
from scheduler.exceptions import ScheduleEntryError
from core.constants import VALID_CONTENT_TYPES
from core.logger import get_logger

logger = get_logger(__name__)

_VALID_DAYS = range(7)
_VALID_TIME_FORMAT_LENGTH = 5  # "HH:MM"


def _validate_entry_data(content_type: str, day_of_week: int, time_of_day: str) -> None:
    if content_type not in VALID_CONTENT_TYPES:
        raise ScheduleEntryError(f"content_type inválido: '{content_type}'.")

    if day_of_week not in _VALID_DAYS:
        raise ScheduleEntryError(f"day_of_week debe estar entre 0 (lunes) y 6 (domingo), recibido: {day_of_week}.")

    if len(time_of_day) != _VALID_TIME_FORMAT_LENGTH or time_of_day[2] != ":":
        raise ScheduleEntryError(f"time_of_day debe tener formato 'HH:MM', recibido: '{time_of_day}'.")


def add_schedule_entry(channel_id: int, content_type: str, day_of_week: int, time_of_day: str) -> ScheduleEntry:
    """Añade una franja de publicación recurrente para un canal."""
    _validate_entry_data(content_type, day_of_week, time_of_day)

    entry = ScheduleEntry(
        channel_id=channel_id, content_type=content_type,
        day_of_week=day_of_week, time_of_day=time_of_day,
    )
    saved = repository.create_entry(entry)
    logger.info(f"Canal {channel_id}: horario añadido ({content_type}, día={day_of_week}, hora={time_of_day})")
    return saved


def remove_schedule_entry(entry_id: int) -> None:
    """Elimina una franja de publicación."""
    repository.delete_entry(entry_id)
    logger.info(f"Horario {entry_id} eliminado.")


def list_schedule_for_channel(channel_id: int) -> list[ScheduleEntry]:
    """Lista todas las franjas configuradas para un canal."""
    return repository.list_entries_by_channel(channel_id)