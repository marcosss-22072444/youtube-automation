"""
models.py

Define las estructuras de datos del Scheduler:
- ScheduleEntry: una franja de publicación recurrente (canal + tipo +
  día de la semana + hora).
- ScheduleRun: el registro de una ejecución concreta de una franja,
  en una fecha concreta (garantiza idempotencia vía UNIQUE en BD).
- Job: una unidad de trabajo en la cola, lista para ser procesada.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"

# 0=lunes ... 6=domingo (convención ISO, independiente de locale)
MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)


@dataclass
class ScheduleEntry:
    """Representa una franja de publicación recurrente de un canal."""

    channel_id: int
    content_type: str  # "short" o "long"
    day_of_week: int   # 0=lunes ... 6=domingo
    time_of_day: str   # "HH:MM", 24h
    enabled: bool = True
    id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class ScheduleRun:
    """Representa una ejecución concreta (o intento) de una ScheduleEntry en una fecha."""

    schedule_entry_id: int
    run_date: str  # "YYYY-MM-DD"
    status: str = STATUS_QUEUED
    uploaded_video_id: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    next_retry_at: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        now = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now


@dataclass
class Job:
    """Unidad de trabajo encolada, lista para que un worker la procese."""

    schedule_run_id: int
    channel_id: int
    content_type: str