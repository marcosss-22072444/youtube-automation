"""
repository.py

Acceso a la base de datos para la tabla 'scripts'.
"""

import sqlite3

from core.database import get_connection
from scripts.models import Script
from scripts.exceptions import ScriptNotFoundError


def _row_to_script(row: sqlite3.Row) -> Script:
    """Convierte una fila de la base de datos en un objeto Script."""
    return Script(
        id=row["id"],
        idea_id=row["idea_id"],
        content_type=row["content_type"],
        content=row["content"],
        word_count=row["word_count"],
        status=row["status"],
        created_at=row["created_at"],
    )


def create(script: Script) -> Script:
    """Guarda un guion nuevo en la base de datos."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO scripts (idea_id, content_type, content, word_count, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                script.idea_id, script.content_type, script.content,
                script.word_count, script.status, script.created_at,
            ),
        )
    script.id = cursor.lastrowid
    return script


def get_by_id(script_id: int) -> Script:
    """Busca un guion por su id. Lanza ScriptNotFoundError si no existe."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM scripts WHERE id = ?", (script_id,)).fetchone()

    if row is None:
        raise ScriptNotFoundError(f"No existe ningún guion con id {script_id}.")

    return _row_to_script(row)


def get_by_idea_id(idea_id: int) -> Script | None:
    """Devuelve el guion de una idea concreta, o None si aún no tiene."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM scripts WHERE idea_id = ?", (idea_id,)).fetchone()

    return _row_to_script(row) if row else None