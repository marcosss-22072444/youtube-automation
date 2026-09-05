"""main.py — PRUEBA REAL end-to-end: subtitulos karaoke con timestamps reales."""
from core.logger import get_logger
from core.schema import initialize_database
from core.constants import CONTENT_TYPE_SHORT
from channels import manager as channel_manager
from ideas.generator import generate_idea_for_channel
from scripts.generator import generate_script_for_idea
from voice.generator import generate_voice_for_script
from visuals.generator import generate_visuals_for_script
from video_editor.assembler import assemble_video, _get_audio_duration
from core.storage.factory import get_default_storage


logger = get_logger(__name__)


def main():
    initialize_database()
    storage = get_default_storage()


    canal = next((c for c in channel_manager.list_channels() if c.name == "Curiosidades de Superdeportivos"), None)
    if canal is None:
        canal = channel_manager.create_channel(
            name="Curiosidades de Superdeportivos", topic="Coches deportivos",
            shorts_per_week=5, long_videos_per_week=1, voice_name="em_alex",
        )


    idea = generate_idea_for_channel(canal, content_type=CONTENT_TYPE_SHORT)
    logger.info(f"Idea: {idea.title}")


    script = generate_script_for_idea(idea)
    logger.info(f"Guion: {script.word_count} palabras")


    voice_track = generate_voice_for_script(script, canal)
    logger.info(f"Timestamps guardados: {voice_track.word_timestamps_path}")
    audio_duration = _get_audio_duration(storage.resolve_path(voice_track.file_path))


    visuals = generate_visuals_for_script(script, audio_duration_seconds=audio_duration, channel_id=canal.id)


    video = assemble_video(script, visuals, voice_track, channel_id=canal.id)
    logger.info(f"✅ VIDEO FINAL: {storage.resolve_path(video.file_path)}")


if __name__ == "__main__":
    main()

