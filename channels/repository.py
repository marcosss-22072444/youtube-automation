"""
repository.py

Acceso a la base de datos para la tabla 'channels'. Es la única parte
del proyecto que ejecuta SQL directamente sobre channels. Si en el
futuro migras de SQLite a MariaDB, solo este archivo necesita cambiar.
"""

import sqlite3
from typing import Optional

from core.database import get_connection
from channels.models import Channel
from channels.exceptions import ChannelNotFoundError, DuplicateChannelNameError


def _row_to_channel(row: sqlite3.Row) -> Channel:
    """Convierte una fila de la base de datos en un objeto Channel."""
    return Channel(
        id=row["id"],
        name=row["name"],
        topic=row["topic"],
        status=row["status"],
        shorts_per_week=row["shorts_per_week"],
        long_videos_per_week=row["long_videos_per_week"],
        voice_name=row["voice_name"],
        created_at=row["created_at"],
    )


def create(channel: Channel) -> Channel:
    """Inserta un nuevo canal en la base de datos y le asigna un id."""
    with get_connection() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO channels
                    (name, topic, status, shorts_per_week, long_videos_per_week, voice_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    channel.name,
                    channel.topic,
                    channel.status,
                    channel.shorts_per_week,
                    channel.long_videos_per_week,
                    channel.voice_name,
                    channel.created_at,
                ),
            )
        except sqlite3.IntegrityError:
            raise DuplicateChannelNameError(
                f"Ya existe un canal con el nombre '{channel.name}'."
            )

        channel.id = cursor.lastrowid
        return channel

def get_by_id(channel_id: int) -> Channel:
    """Busca un canal por su id. Lanza ChannelNotFoundError si no existe."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM channels WHERE id = ?", (channel_id,)
        ).fetchone()

    if row is None:
        raise ChannelNotFoundError(f"No existe ningún canal con id {channel_id}.")

    return _row_to_channel(row)


def list_all() -> list[Channel]:
    """Devuelve todos los canales guardados."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM channels ORDER BY created_at").fetchall()

    return [_row_to_channel(row) for row in rows]


def update(channel: Channel) -> Channel:
    """Actualiza un canal existente (debe tener id)."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE channels
            SET name = ?, topic = ?, status = ?,
                shorts_per_week = ?, long_videos_per_week = ?, voice_name = ?
            WHERE id = ?
            """,
            (
                channel.name,
                channel.topic,
                channel.status,
                channel.shorts_per_week,
                channel.long_videos_per_week,
                channel.voice_name,
                channel.id,
            ),
        )
    return channel


def delete(channel_id: int) -> None:
    """Elimina un canal por su id."""
    with get_connection() as conn:
        conn.execute("DELETE FROM channels WHERE id = ?", (channel_id,))