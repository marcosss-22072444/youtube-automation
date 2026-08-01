"""
models.py

Define la estructura de datos de un VoiceTrack: el audio narrado
generado a partir de un Script.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class VoiceTrack:
    """Representa el audio narrado generado para un guion concreto."""

    script_id: int
    file_path: str
    voice_name: str
    id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()