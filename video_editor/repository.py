"""
repository.py

Acceso a la base de datos para la tabla 'videos'.
"""

import sqlite3

from core.database import get_connection
from video_editor.models import Video


def _row_to_video(row: sqlite3.Row) -> Video:
    """Convierte una fila de la base de datos en un objeto Video."""
    return Video(
        id=row["id"],
        script_id=row["script_id"],
        file_path=row["file_path"],
        srt_path=row["srt_path"],
        duration_seconds=row["duration_seconds"],
        created_at=row["created_at"],
    )


def create(video: Video) -> Video:
    """Guarda un vídeo final en la base de datos."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO videos (script_id, file_path, srt_path, duration_seconds, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (video.script_id, video.file_path, video.srt_path, video.duration_seconds, video.created_at),
        )
    video.id = cursor.lastrowid
    return video