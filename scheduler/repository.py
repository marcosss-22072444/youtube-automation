"""
repository.py

Acceso a la base de datos para 'channel_schedules' y 'schedule_runs'.
Incluye claim_run(), el mecanismo atómico que garantiza que una franja
nunca se ejecute dos veces el mismo día.
"""

import sqlite3
from datetime import datetime

from core.database import get_connection
from scheduler.models import ScheduleEntry, ScheduleRun, STATUS_QUEUED


def _row_to_entry(row: sqlite3.Row) -> ScheduleEntry:
    return ScheduleEntry(
        id=row["id"],
        channel_id=row["channel_id"],
        content_type=row["content_type"],
        day_of_week=row["day_of_week"],
        time_of_day=row["time_of_day"],
        enabled=bool(row["enabled"]),
        created_at=row["created_at"],
    )


def _row_to_run(row: sqlite3.Row) -> ScheduleRun:
    return ScheduleRun(
        id=row["id"],
        schedule_entry_id=row["schedule_entry_id"],
        run_date=row["run_date"],
        status=row["status"],
        uploaded_video_id=row["uploaded_video_id"],
        error_message=row["error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# --- ScheduleEntry ---

def create_entry(entry: ScheduleEntry) -> ScheduleEntry:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO channel_schedules
                (channel_id, content_type, day_of_week, time_of_day, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entry.channel_id, entry.content_type, entry.day_of_week,
                entry.time_of_day, int(entry.enabled), entry.created_at,
            ),
        )
    entry.id = cursor.lastrowid
    return entry


def delete_entry(entry_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM channel_schedules WHERE id = ?", (entry_id,))


def list_entries_by_channel(channel_id: int) -> list[ScheduleEntry]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM channel_schedules WHERE channel_id = ? ORDER BY day_of_week, time_of_day",
            (channel_id,),
        ).fetchall()
    return [_row_to_entry(row) for row in rows]


def list_all_enabled_entries() -> list[ScheduleEntry]:
    """Todas las franjas activas de todos los canales (lo usa el runner)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM channel_schedules WHERE enabled = 1"
        ).fetchall()
    return [_row_to_entry(row) for row in rows]


# --- ScheduleRun / idempotencia ---

def claim_run(schedule_entry_id: int, run_date: str) -> ScheduleRun | None:
    """
    Intenta reclamar la ejecución de una franja en una fecha concreta.
    Devuelve el ScheduleRun creado si tuvo éxito, o None si ya estaba
    reclamada (por este mismo proceso u otro) — gracias al UNIQUE
    (schedule_entry_id, run_date) en la base de datos.
    """
    now = datetime.now().isoformat()
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO schedule_runs
                    (schedule_entry_id, run_date, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (schedule_entry_id, run_date, STATUS_QUEUED, now, now),
            )
        return ScheduleRun(
            id=cursor.lastrowid, schedule_entry_id=schedule_entry_id,
            run_date=run_date, status=STATUS_QUEUED, created_at=now, updated_at=now,
        )
    except sqlite3.IntegrityError:
        return None


def update_run_status(
    run_id: int, status: str, uploaded_video_id: int | None = None, error_message: str | None = None
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE schedule_runs
            SET status = ?, uploaded_video_id = ?, error_message = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, uploaded_video_id, error_message, datetime.now().isoformat(), run_id),
        )