"""
models.py

Define la estructura de datos de un Visual: una imagen generada para
una escena concreta de un Script.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Visual:
    """Representa una imagen generada para una escena de un guion."""

    script_id: int
    scene_number: int
    image_prompt: str
    file_path: str
    id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()