"""
models.py

Define la estructura de datos de un Video: el vídeo final montado a
partir de un Script, su audio y sus imágenes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Video:
    """Representa el vídeo final generado para un guion concreto."""

    script_id: int
    file_path: str
    srt_path: Optional[str]
    duration_seconds: float
    id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()