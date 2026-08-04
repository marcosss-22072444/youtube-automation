"""
repository.py

Acceso a la base de datos para la tabla 'visuals'.
"""

import sqlite3

from core.database import get_connection
from visuals.models import Visual


def _row_to_visual(row: sqlite3.Row) -> Visual:
    """Convierte una fila de la base de datos en un objeto Visual."""
    return Visual(
        id=row["id"],
        script_id=row["script_id"],
        scene_number=row["scene_number"],
        image_prompt=row["image_prompt"],
        file_path=row["file_path"],
        created_at=row["created_at"],
    )


def create(visual: Visual) -> Visual:
    """Guarda una imagen generada en la base de datos."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO visuals (script_id, scene_number, image_prompt, file_path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (visual.script_id, visual.scene_number, visual.image_prompt, visual.file_path, visual.created_at),
        )
    visual.id = cursor.lastrowid
    return visual


def list_by_script(script_id: int) -> list[Visual]:
    """Lista todas las imágenes generadas para un guion, ordenadas por escena."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM visuals WHERE script_id = ? ORDER BY scene_number",
            (script_id,),
        ).fetchall()

    return [_row_to_visual(row) for row in rows]