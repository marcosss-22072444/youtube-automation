"""pipeline.py — Endpoints REST de estado de pipeline/generacion (schedule_runs)."""
from fastapi import APIRouter

from scheduler import repository as schedule_repository
from core.database import get_connection

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/channel/{channel_id}/runs")
def list_runs_for_channel(channel_id: int):
    """Historial de ejecuciones (schedule_runs) del canal, con su estado y errores."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT sr.id, sr.schedule_entry_id, sr.run_date, sr.status, sr.uploaded_video_id,
                   sr.error_message, sr.retry_count, sr.created_at, sr.updated_at,
                   cs.content_type
            FROM schedule_runs sr
            JOIN channel_schedules cs ON cs.id = sr.schedule_entry_id
            WHERE cs.channel_id = ?
            ORDER BY sr.created_at DESC
            """,
            (channel_id,),
        ).fetchall()
    return [dict(row) for row in rows]


@router.get("/errors")
def list_recent_errors(limit: int = 50):
    """Errores recientes de cualquier canal (para panel de alertas)."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT sr.id, cs.channel_id, cs.content_type, sr.run_date, sr.error_message,
                   sr.retry_count, sr.updated_at
            FROM schedule_runs sr
            JOIN channel_schedules cs ON cs.id = sr.schedule_entry_id
            WHERE sr.status = 'failed'
            ORDER BY sr.updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]