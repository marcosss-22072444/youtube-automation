"""
repository.py

Acceso a la base de datos para la tabla 'thumbnails'.
"""

import sqlite3

from core.database import get_connection
from thumbnails.models import Thumbnail


def _row_to_thumbnail(row: sqlite3.Row) -> Thumbnail:
    """Convierte una fila de la base de datos en un objeto Thumbnail."""
    return Thumbnail(
        id=row["id"],
        script_id=row["script_id"],
        file_path=row["file_path"],
        title_text=row["title_text"],
        created_at=row["created_at"],
    )


def create(thumbnail: Thumbnail) -> Thumbnail:
    """Guarda una miniatura generada en la base de datos."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO thumbnails (script_id, file_path, title_text, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (thumbnail.script_id, thumbnail.file_path, thumbnail.title_text, thumbnail.created_at),
        )
    thumbnail.id = cursor.lastrowid
    return thumbnail