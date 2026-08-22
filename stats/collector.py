"""
collector.py

Recoge estadísticas (vistas, likes, comentarios, suscriptores) de los
vídeos ya publicados de un canal, usando la YouTube Data API, y
guarda un snapshot nuevo por cada recogida.
"""

from channels.models import Channel
from youtube_api.auth import get_youtube_client
from youtube_api.models import UploadedVideo
from youtube_api import repository as upload_repository
from stats import repository as stats_repository
from stats.models import VideoStats
from stats.exceptions import StatsCollectionError
from core.logger import get_logger

logger = get_logger(__name__)

_MAX_IDS_PER_REQUEST = 50  # límite de la API de YouTube para videos().list


def _get_subscriber_count(youtube, channel_youtube_id: str | None) -> int:
    """
    Obtiene el número de suscriptores del canal de YouTube autenticado
    (el propio canal del token, ya que "mine=True" no requiere conocer
    su ID de YouTube de antemano).
    """
    try:
        response = youtube.channels().list(part="statistics", mine=True).execute()
        items = response.get("items", [])
        if not items:
            return 0
        return int(items[0]["statistics"].get("subscriberCount", 0))
    except Exception as error:
        logger.warning(f"No se pudo obtener el número de suscriptores: {error}")
        return 0


def collect_stats_for_channel(channel: Channel) -> list[VideoStats]:
    """
    Recoge estadísticas de todos los vídeos publicados de un canal y
    guarda un snapshot nuevo de cada uno.
    """
    uploaded_videos = upload_repository.list_by_channel(channel.id)
    if not uploaded_videos:
        logger.info(f"Canal {channel.id}: no hay vídeos publicados todavía, nada que recoger.")
        return []

    try:
        youtube = get_youtube_client(channel.id)
    except Exception as error:
        raise StatsCollectionError(f"Fallo al autenticar canal {channel.id} para recoger stats: {error}") from error

    subscriber_count = _get_subscriber_count(youtube, None)

    snapshots = []
    for batch_start in range(0, len(uploaded_videos), _MAX_IDS_PER_REQUEST):
        batch = uploaded_videos[batch_start:batch_start + _MAX_IDS_PER_REQUEST]
        video_ids = ",".join(v.youtube_video_id for v in batch)
        by_id = {v.youtube_video_id: v for v in batch}

        try:
            response = youtube.videos().list(part="statistics", id=video_ids).execute()
        except Exception as error:
            logger.warning(f"Canal {channel.id}: fallo al recoger estadísticas de un lote de vídeos: {error}")
            continue

        for item in response.get("items", []):
            uploaded_video: UploadedVideo = by_id.get(item["id"])
            if uploaded_video is None:
                continue

            stats_data = item.get("statistics", {})
            snapshot = VideoStats(
                uploaded_video_id=uploaded_video.id,
                channel_id=channel.id,
                view_count=int(stats_data.get("viewCount", 0)),
                like_count=int(stats_data.get("likeCount", 0)),
                comment_count=int(stats_data.get("commentCount", 0)),
                subscriber_count=subscriber_count,
            )
            saved = stats_repository.create(snapshot)
            snapshots.append(saved)

    logger.info(f"Canal {channel.id}: {len(snapshots)} snapshot(s) de estadísticas guardados.")
    return snapshots