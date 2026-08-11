"""
models.py

Define la estructura de datos de Metadata: título, descripción y
etiquetas generados para un Script (vídeo) concreto.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Metadata:
    """Representa el título, descripción y etiquetas de un vídeo."""

    script_id: int
    title: str
    description: str
    tags: list[str] = field(default_factory=list)
    id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    @property
    def tags_as_string(self) -> str:
        """Etiquetas como string separado por comas, tal como espera la API de YouTube."""
        return ",".join(self.tags)