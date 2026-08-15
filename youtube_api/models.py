"""
models.py

Define la estructura de datos de un UploadedVideo: el registro de un
vídeo ya subido a YouTube para un Script concreto.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UploadedVideo:
    """Representa un vídeo ya subido a YouTube."""

    script_id: int
    channel_id: int
    youtube_video_id: str
    privacy_status: str
    thumbnail_uploaded: bool = False
    id: Optional[int] = None
    uploaded_at: Optional[str] = None

    def __post_init__(self):
        if self.uploaded_at is None:
            self.uploaded_at = datetime.now().isoformat()

    @property
    def youtube_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.youtube_video_id}"