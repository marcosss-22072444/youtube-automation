"""
models.py

Define la estructura de datos de una Idea de vídeo. No sabe nada de
SQL ni de IA: solo representa la forma que tiene una idea en memoria.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Idea:
    """Representa una idea de vídeo generada para un canal concreto."""

    channel_id: int
    content_type: str  # "short" o "long" (ver core.constants.VALID_CONTENT_TYPES)
    title: str
    summary: str
    used: bool = False
    id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()