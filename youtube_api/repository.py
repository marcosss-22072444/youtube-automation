"""
repository.py

Acceso a la base de datos para la tabla 'uploaded_videos'.
"""

import sqlite3

from core.database import get_connection
from youtube_api.models import UploadedVideo


def _row_to_uploaded_video(row: sqlite3.Row) -> UploadedVideo:
    """Convierte una fila de la base de datos en un objeto UploadedVideo."""
    return UploadedVideo(
        id=row["id"],
        script_id=row["script_id"],
        channel_id=row["channel_id"],
        youtube_video_id=row["youtube_video_id"],
        privacy_status=row["privacy_status"],
        thumbnail_uploaded=bool(row["thumbnail_uploaded"]),
        uploaded_at=row["uploaded_at"],
    )


def create(uploaded_video: UploadedVideo) -> UploadedVideo:
    """Registra un vídeo ya subido a YouTube."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO uploaded_videos
                (script_id, channel_id, youtube_video_id, privacy_status, thumbnail_uploaded, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                uploaded_video.script_id, uploaded_video.channel_id,
                uploaded_video.youtube_video_id, uploaded_video.privacy_status,
                int(uploaded_video.thumbnail_uploaded), uploaded_video.uploaded_at,
            ),
        )
    uploaded_video.id = cursor.lastrowid
    return uploaded_video


def mark_thumbnail_uploaded(uploaded_video_id: int) -> None:
    """Marca que la miniatura de un vídeo ya subido se subió correctamente."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE uploaded_videos SET thumbnail_uploaded = 1 WHERE id = ?",
            (uploaded_video_id,),
        )


def list_pending_thumbnails(channel_id: int) -> list[UploadedVideo]:
    """Lista los vídeos subidos de un canal cuya miniatura aún no se subió."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM uploaded_videos WHERE channel_id = ? AND thumbnail_uploaded = 0",
            (channel_id,),
        ).fetchall()

    return [_row_to_uploaded_video(row) for row in rows]


def list_by_channel(channel_id: int) -> list[UploadedVideo]:
    """Lista todos los vídeos subidos de un canal, más recientes primero."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM uploaded_videos WHERE channel_id = ? ORDER BY uploaded_at DESC",
            (channel_id,),
        ).fetchall()

    return [_row_to_uploaded_video(row) for row in rows]