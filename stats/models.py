"""
models.py

Define la estructura de datos de VideoStats: una "foto" (snapshot) de
las métricas de un vídeo y su canal en un momento dado. Se guarda un
snapshot nuevo en cada recogida, formando un histórico en el tiempo.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class VideoStats:
    """Representa un snapshot de estadísticas de un vídeo publicado."""

    uploaded_video_id: int
    channel_id: int
    view_count: int
    like_count: int
    comment_count: int
    subscriber_count: int
    id: Optional[int] = None
    collected_at: Optional[str] = None

    def __post_init__(self):
        if self.collected_at is None:
            self.collected_at = datetime.now().isoformat()