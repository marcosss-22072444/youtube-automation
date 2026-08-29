"""
pipeline_executor.py

Ejecuta el pipeline completo de generación y publicación para un Job
concreto: idea -> guion -> voz -> visuals -> video -> miniatura ->
metadata -> YouTube. Reutiliza sin modificar ninguno de los
generadores de los módulos 1-10. Cualquier fallo se captura aquí y se
registra como 'failed' en schedule_runs, sin propagar la excepción —
un error en un canal nunca debe detener los demás.
"""

from channels import manager as channel_manager
from ideas.generator import generate_idea_for_channel
from scripts.generator import generate_script_for_idea
from voice.generator import generate_voice_for_script
from visuals.generator import generate_visuals_for_script
from video_editor.assembler import assemble_video, _get_audio_duration
from thumbnails.generator import generate_thumbnail_for_script
from metadata.generator import generate_metadata_for_script
from youtube_api.uploader import upload_video
from core.storage.factory import get_default_storage
from core.config import settings
from scheduler import repository as schedule_repository
from scheduler.models import Job, STATUS_RUNNING, STATUS_SUCCESS, STATUS_FAILED
from scheduler.exceptions import PipelineExecutionError
from core.logger import get_logger
from research.manager import research_idea

logger = get_logger(__name__)


def execute_job(job: Job) -> None:
    """
    Ejecuta el pipeline completo para un trabajo, actualizando su
    ScheduleRun asociado al finalizar (éxito o fallo). Nunca lanza
    excepción hacia el llamador — el fallo queda registrado en BD y
    en el log, y el worker puede continuar con el siguiente trabajo.
    """
    log_prefix = f"[canal={job.channel_id} tipo={job.content_type} run={job.schedule_run_id}]"
    logger.info(f"{log_prefix} Iniciando ejecución del pipeline.")

    schedule_repository.update_run_status(job.schedule_run_id, STATUS_RUNNING)

    try:
        storage = get_default_storage()
        canal = channel_manager.get_channel(job.channel_id)

        idea = generate_idea_for_channel(canal, content_type=job.content_type)
        logger.info(f"{log_prefix} Idea: {idea.title}")

        research_result = research_idea(idea, canal)
        logger.info(
            f"{log_prefix} Research: {len(research_result.sources)} fuentes, "
            f"{len(research_result.verified_facts)} hechos verificados (status={research_result.status})"
        )

        script = generate_script_for_idea(idea, research_result=research_result)
        logger.info(f"{log_prefix} Guion: {script.id}")

        voice_track = generate_voice_for_script(script, canal)
        audio_duration = _get_audio_duration(storage.resolve_path(voice_track.file_path))
        logger.info(f"{log_prefix} Audio: {audio_duration:.1f}s")

        visuals = generate_visuals_for_script(script, audio_duration_seconds=audio_duration, channel_id=canal.id)
        logger.info(f"{log_prefix} Escenas: {len(visuals)}")

        video = assemble_video(script, visuals, voice_track)
        logger.info(f"{log_prefix} Vídeo montado: {video.file_path}")

        thumbnail = generate_thumbnail_for_script(
            script_id=script.id,
            content_type=script.content_type,
            title=idea.title.upper(),
            background_prompt=f"{canal.topic}, cinematic lighting, high detail",
        )
        logger.info(f"{log_prefix} Miniatura: {thumbnail.file_path}")

        metadata = generate_metadata_for_script(script, canal)
        logger.info(f"{log_prefix} Metadata: {metadata.title}")

        privacy_status = settings.scheduler.get("default_privacy_status", "private")
        uploaded = upload_video(
            script=script, channel=canal, video=video, metadata=metadata,
            thumbnail=thumbnail, privacy_status=privacy_status,
        )
        logger.info(f"{log_prefix} ✅ Publicado: {uploaded.youtube_url} (privacy={privacy_status})")

        schedule_repository.update_run_status(job.schedule_run_id, STATUS_SUCCESS, uploaded_video_id=uploaded.id)

    except Exception as error:
        logger.error(f"{log_prefix} ❌ Fallo en el pipeline: {error}")
        schedule_repository.update_run_status(job.schedule_run_id, STATUS_FAILED, error_message=str(error))