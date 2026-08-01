"""
repository.py

Acceso a la base de datos para la tabla 'ideas'. Es la única parte
del proyecto que ejecuta SQL directamente sobre ideas.
"""

import sqlite3

from core.database import get_connection
from core.config import settings
from ideas.models import Idea
from ideas.exceptions import IdeaNotFoundError


def _row_to_idea(row: sqlite3.Row) -> Idea:
    """Convierte una fila de la base de datos en un objeto Idea."""
    return Idea(
        id=row["id"],
        channel_id=row["channel_id"],
        content_type=row["content_type"],
        title=row["title"],
        summary=row["summary"],
        used=bool(row["used"]),
        created_at=row["created_at"],
    )

def create(idea: Idea) -> Idea:
    """Guarda una idea nueva en la base de datos."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO ideas (channel_id, content_type, title, summary, used, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (idea.channel_id, idea.content_type, idea.title, idea.summary, int(idea.used), idea.created_at),
        )
    idea.id = cursor.lastrowid
    return idea


def get_by_id(idea_id: int) -> Idea:
    """Busca una idea por su id. Lanza IdeaNotFoundError si no existe."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()

    if row is None:
        raise IdeaNotFoundError(f"No existe ninguna idea con id {idea_id}.")

    return _row_to_idea(row)


def list_by_channel(channel_id: int, only_used: bool = False) -> list[Idea]:
    """Lista las ideas de un canal, opcionalmente solo las ya usadas."""
    query = "SELECT * FROM ideas WHERE channel_id = ?"
    params = [channel_id]

    if only_used:
        query += " AND used = 1"

    query += " ORDER BY created_at DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [_row_to_idea(row) for row in rows]


def get_recent_titles_for_context(channel_id: int, limit: int | None = None) -> list[str]:
    """
    Devuelve los últimos títulos usados de un canal, para pasárselos
    a la IA como contexto de 'qué no repetir'. El límite es configurable
    desde config.yaml (settings.ideas_context_limit) si no se especifica.
    """
    if limit is None:
        limit = settings.ideas_context_limit

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT title FROM ideas
            WHERE channel_id = ? AND used = 1
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (channel_id, limit),
        ).fetchall()

    return [row["title"] for row in rows]


def mark_as_used(idea_id: int) -> Idea:
    """Marca una idea como usada (ya convertida en guion/vídeo)."""
    idea = get_by_id(idea_id)
    with get_connection() as conn:
        conn.execute("UPDATE ideas SET used = 1 WHERE id = ?", (idea_id,))
    idea.used = True
    return idea