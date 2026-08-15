"""
uploader.py

Sube un vídeo completo (archivo + metadata + miniatura) a YouTube,
usando las credenciales OAuth del canal correspondiente.
"""

from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from channels.models import Channel
from scripts.models import Script
from video_editor.models import Video
from metadata.models import Metadata
from thumbnails.models import Thumbnail
from youtube_api import repository as upload_repository
from youtube_api.auth import get_youtube_client
from youtube_api.models import UploadedVideo
from youtube_api.exceptions import YouTubeUploadError
from ideas import repository as idea_repository
from core.storage.base import StorageBackend
from core.storage.factory import get_default_storage
from core.logger import get_logger

logger = get_logger(__name__)


def _validate_ownership(
    script: Script, channel: Channel, video: Video, metadata: Metadata, thumbnail: Thumbnail | None
) -> None:
    """
    Comprobación de seguridad antes de subir: verifica que video,
    metadata y (si se indica) thumbnail pertenecen realmente al mismo
    script, y que ese script pertenece al canal indicado. Evita subir
    contenido al canal equivocado por un error de programación.
    """
    if video.script_id != script.id:
        raise YouTubeUploadError(
            f"El vídeo (script_id={video.script_id}) no corresponde al guion {script.id}."
        )

    if metadata.script_id != script.id:
        raise YouTubeUploadError(
            f"La metadata (script_id={metadata.script_id}) no corresponde al guion {script.id}."
        )

    if thumbnail is not None and thumbnail.script_id != script.id:
        raise YouTubeUploadError(
            f"La miniatura (script_id={thumbnail.script_id}) no corresponde al guion {script.id}."
        )

    idea = idea_repository.get_by_id(script.idea_id)
    if idea.channel_id != channel.id:
        raise YouTubeUploadError(
            f"El guion {script.id} pertenece al canal {idea.channel_id}, "
            f"no al canal {channel.id} indicado."
        )


def _upload_thumbnail(youtube, storage: StorageBackend, thumbnail: Thumbnail, youtube_video_id: str) -> bool:
    """
    Sube la miniatura de un vídeo ya subido. Devuelve True si tuvo
    éxito, False si falló — un fallo aquí NUNCA debe hacer fallar la
    subida del vídeo, que ya se realizó con éxito.
    """
    try:
        thumbnail_path = storage.resolve_path(thumbnail.file_path)
        youtube.thumbnails().set(
            videoId=youtube_video_id,
            media_body=MediaFileUpload(str(thumbnail_path)),
        ).execute()
        logger.info(f"Miniatura subida para el vídeo {youtube_video_id}")
        return True
    except HttpError as error:
        logger.warning(
            f"El vídeo {youtube_video_id} se subió correctamente, pero falló la "
            f"miniatura (se puede reintentar más tarde sin volver a subir el vídeo): {error}"
        )
        return False


def upload_video(
    script: Script,
    channel: Channel,
    video: Video,
    metadata: Metadata,
    thumbnail: Thumbnail | None = None,
    privacy_status: str = "private",
    storage: StorageBackend | None = None,
) -> UploadedVideo:
    """
    Sube un vídeo a YouTube con su metadata, usando las credenciales
    del canal indicado. La miniatura (si se indica) se intenta subir
    después, como paso independiente: si falla, el vídeo ya subido
    NO se considera fallido, y queda registrado con
    thumbnail_uploaded=False para poder reintentarlo más tarde con
    retry_thumbnail_upload().
    """
    if storage is None:
        storage = get_default_storage()

    _validate_ownership(script, channel, video, metadata, thumbnail)

    youtube = get_youtube_client(channel.id)

    try:
        video_path = storage.resolve_path(video.file_path)

        body = {
            "snippet": {
                "title": metadata.title,
                "description": metadata.description,
                "tags": metadata.tags,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Subiendo vídeo del guion {script.id}: {int(status.progress() * 100)}%")

        youtube_video_id = response["id"]
        logger.info(f"Vídeo subido a YouTube: {youtube_video_id}")

    except HttpError as error:
        raise YouTubeUploadError(f"Fallo al subir vídeo a YouTube: {error}") from error

    # A partir de aquí, el vídeo YA está subido con éxito. Cualquier
    # fallo posterior (miniatura) se registra pero no revierte esto.
    uploaded_video = UploadedVideo(
        script_id=script.id,
        channel_id=channel.id,
        youtube_video_id=youtube_video_id,
        privacy_status=privacy_status,
        thumbnail_uploaded=False,
    )
    saved_upload = upload_repository.create(uploaded_video)
    logger.info(f"✅ Vídeo publicado: {saved_upload.youtube_url}")

    if thumbnail is not None and script.content_type != "short":
        success = _upload_thumbnail(youtube, storage, thumbnail, youtube_video_id)
        if success:
            upload_repository.mark_thumbnail_uploaded(saved_upload.id)
            saved_upload.thumbnail_uploaded = True
    elif thumbnail is not None:
        logger.info(
            f"Guion {script.id} es un Short: se omite la miniatura personalizada "
            f"(YouTube la elige automáticamente para Shorts)."
        )

    return saved_upload


def retry_thumbnail_upload(
    uploaded_video: UploadedVideo, channel: Channel, thumbnail: Thumbnail, storage: StorageBackend | None = None
) -> bool:
    """
    Reintenta subir la miniatura de un vídeo ya publicado, sin volver
    a subir el vídeo. Útil cuando el fallo original fue de permisos
    temporales o de conexión.
    """
    if storage is None:
        storage = get_default_storage()

    youtube = get_youtube_client(channel.id)
    success = _upload_thumbnail(youtube, storage, thumbnail, uploaded_video.youtube_video_id)

    if success:
        upload_repository.mark_thumbnail_uploaded(uploaded_video.id)

    return success