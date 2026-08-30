"""main.py — PRUEBA REAL: visuals con niveles de especificidad y orientacion."""
from core.logger import get_logger
from core.schema import initialize_database
from core.constants import CONTENT_TYPE_SHORT
from channels import manager as channel_manager
from ideas.generator import generate_idea_for_channel
from scripts.generator import generate_script_for_idea
from visuals.generator import generate_visuals_for_script

logger = get_logger(__name__)

def main():
    initialize_database()
    canal = next((c for c in channel_manager.list_channels() if c.name == "Curiosidades de Superdeportivos"), None)
    if canal is None:
        canal = channel_manager.create_channel(
            name="Curiosidades de Superdeportivos", topic="Coches deportivos y superdeportivos",
            shorts_per_week=5, long_videos_per_week=1, voice_name="em_alex",
        )
    idea = generate_idea_for_channel(canal, content_type=CONTENT_TYPE_SHORT)
    logger.info(f"Idea: {idea.title}")
    script = generate_script_for_idea(idea)
    logger.info(f"Guion: {script.word_count} palabras")
    visuals = generate_visuals_for_script(script, audio_duration_seconds=30, channel_id=canal.id)
    for v in visuals:
        logger.info(f"  - {v.asset_type} de {v.source} | query usada: '{v.image_prompt}'")

if __name__ == "__main__":
    main()