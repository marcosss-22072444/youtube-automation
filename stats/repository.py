"""
repository.py

Acceso a la base de datos para la tabla 'video_stats'.
"""

import sqlite3

from core.database import get_connection
from stats.models import VideoStats


def _row_to_stats(row: sqlite3.Row) -> VideoStats:
    """Convierte una fila de la base de datos en un objeto VideoStats."""
    return VideoStats(
        id=row["id"],
        uploaded_video_id=row["uploaded_video_id"],
        channel_id=row["channel_id"],
        view_count=row["view_count"],
        like_count=row["like_count"],
        comment_count=row["comment_count"],
        subscriber_count=row["subscriber_count"],
        collected_at=row["collected_at"],
    )


def create(stats: VideoStats) -> VideoStats:
    """Guarda un nuevo snapshot de estadísticas."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO video_stats
                (uploaded_video_id, channel_id, view_count, like_count,
                 comment_count, subscriber_count, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stats.uploaded_video_id, stats.channel_id, stats.view_count,
                stats.like_count, stats.comment_count, stats.subscriber_count,
                stats.collected_at,
            ),
        )
    stats.id = cursor.lastrowid
    return stats


def get_latest_for_video(uploaded_video_id: int) -> VideoStats | None:
    """Devuelve el snapshot más reciente de un vídeo, o None si nunca se ha recogido."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM video_stats WHERE uploaded_video_id = ? ORDER BY collected_at DESC LIMIT 1",
            (uploaded_video_id,),
        ).fetchone()
    return _row_to_stats(row) if row else None


def get_history_for_video(uploaded_video_id: int) -> list[VideoStats]:
    """Devuelve todo el histórico de snapshots de un vídeo, más antiguo primero."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM video_stats WHERE uploaded_video_id = ? ORDER BY collected_at ASC",
            (uploaded_video_id,),
        ).fetchall()
    return [_row_to_stats(row) for row in rows]