"""
repository.py

Acceso a la base de datos para la tabla 'voice_tracks'.
"""

import sqlite3

from core.database import get_connection
from voice.models import VoiceTrack
from voice.exceptions import VoiceTrackNotFoundError


def _row_to_voice_track(row: sqlite3.Row) -> VoiceTrack:
    """Convierte una fila de la base de datos en un objeto VoiceTrack."""
    return VoiceTrack(
        id=row["id"],
        script_id=row["script_id"],
        file_path=row["file_path"],
        voice_name=row["voice_name"],
        created_at=row["created_at"],
    )


def create(voice_track: VoiceTrack) -> VoiceTrack:
    """Guarda un registro de audio nuevo en la base de datos."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO voice_tracks (script_id, file_path, voice_name, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (voice_track.script_id, voice_track.file_path, voice_track.voice_name, voice_track.created_at),
        )
    voice_track.id = cursor.lastrowid
    return voice_track


def get_by_script_id(script_id: int) -> VoiceTrack | None:
    """Devuelve el audio de un guion concreto, o None si aún no tiene."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM voice_tracks WHERE script_id = ?", (script_id,)
        ).fetchone()

    return _row_to_voice_track(row) if row else None