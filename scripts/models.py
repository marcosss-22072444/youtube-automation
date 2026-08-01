"""
models.py

Define la estructura de datos de un Script (guion) generado a partir
de una Idea. No sabe nada de SQL ni de IA.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

STATUS_DRAFT = "draft"
STATUS_APPROVED = "approved"


@dataclass
class Script:
    """Representa el guion completo de un vídeo, generado desde una Idea."""

    idea_id: int
    content: str
    word_count: int
    status: str = STATUS_DRAFT
    id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()