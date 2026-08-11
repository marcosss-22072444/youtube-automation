"""
repository.py

Acceso a la base de datos para la tabla 'metadata'.
"""

import sqlite3

from core.database import get_connection
from metadata.models import Metadata


def _row_to_metadata(row: sqlite3.Row) -> Metadata:
    """Convierte una fila de la base de datos en un objeto Metadata."""
    tags = row["tags"].split(",") if row["tags"] else []
    return Metadata(
        id=row["id"],
        script_id=row["script_id"],
        title=row["title"],
        description=row["description"],
        tags=tags,
        created_at=row["created_at"],
    )


def create(metadata: Metadata) -> Metadata:
    """Guarda el título/descripción/etiquetas de un vídeo en la base de datos."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO metadata (script_id, title, description, tags, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (metadata.script_id, metadata.title, metadata.description, metadata.tags_as_string, metadata.created_at),
        )
    metadata.id = cursor.lastrowid
    return metadata