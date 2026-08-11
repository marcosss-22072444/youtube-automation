"""
models.py

Define la estructura de datos de un Thumbnail: la miniatura generada
para un Script (vídeo) concreto.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Thumbnail:
    """Representa la miniatura generada para un guion/vídeo concreto."""

    script_id: int
    file_path: str
    title_text: str
    id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()