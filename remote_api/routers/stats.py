"""stats.py — Endpoints REST de estadisticas. Preparado para YouTube Analytics futuro."""
from fastapi import APIRouter

from stats import repository as stats_repository
from youtube_api import repository as upload_repository

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/channel/{channel_id}")
def get_channel_stats(channel_id: int):
    """Ultimo snapshot de cada video subido del canal (vistas/likes/comentarios/suscriptores)."""
    uploaded = upload_repository.list_by_channel(channel_id)
    result = []
    for video in uploaded:
        latest = stats_repository.get_latest_for_video(video.id)
        result.append({
            "uploaded_video_id": video.id,
            "youtube_video_id": video.youtube_video_id,
            "view_count": latest.view_count if latest else None,
            "like_count": latest.like_count if latest else None,
            "comment_count": latest.comment_count if latest else None,
            "subscriber_count": latest.subscriber_count if latest else None,
            # Reservado para YouTube Analytics (ingresos/impresiones/CTR) cuando se integre:
            "revenue": None,
            "impressions": None,
            "ctr": None,
        })
    return result


@router.get("/video/{uploaded_video_id}/history")
def get_video_history(uploaded_video_id: int):
    """Historial completo de snapshots de un video (serie temporal)."""
    history = stats_repository.get_history_for_video(uploaded_video_id)
    return [
        {"view_count": s.view_count, "like_count": s.like_count,
         "comment_count": s.comment_count, "subscriber_count": s.subscriber_count,
         "collected_at": s.collected_at}
        for s in history
    ]