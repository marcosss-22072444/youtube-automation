"""
models.py

Define la estructura de datos de un Canal (Channel). Esta clase no
sabe nada de SQL ni de la base de datos: solo representa la forma
que tiene un canal en memoria, dentro de la aplicación.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Channel:
    """Representa un canal de YouTube gestionado por la aplicación."""

    name: str
    topic: str
    shorts_per_week: int = 0
    long_videos_per_week: int = 0
    status: str = "active"
    voice_name: str = "ef_dora"
    timezone: Optional[str] = None  # None = usa la zona horaria global del Scheduler
    id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    @property
    def is_active(self) -> bool:
        """True si el canal está activo (publicando normalmente)."""
        return self.status == "active"