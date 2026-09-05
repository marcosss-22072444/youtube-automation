"""main.py — TEST prompt override ideas/scripts via channel_settings."""
from core.logger import get_logger
from core.schema import initialize_database
from channels import manager as channel_manager
from channel_settings import manager as settings_manager
from ideas.generator import _SYSTEM_INSTRUCTION as IDEAS_DEFAULT
from scripts.generator import _SYSTEM_INSTRUCTION as SCRIPTS_DEFAULT

logger = get_logger(__name__)

def main():
    initialize_database()
    canal = channel_manager.create_channel(name="Canal Prompt Test", topic="t", shorts_per_week=1, long_videos_per_week=0)

    p1 = settings_manager.get_setting(canal.id, "ideas.system_instruction_override", default=IDEAS_DEFAULT) == IDEAS_DEFAULT
    logger.info(f"P1 sin override, ideas usa default: {p1}")

    settings_manager.set_setting(canal.id, "ideas.system_instruction_override", "PROMPT CUSTOM IDEAS")
    p2 = settings_manager.get_setting(canal.id, "ideas.system_instruction_override", default=IDEAS_DEFAULT) == "PROMPT CUSTOM IDEAS"
    logger.info(f"P2 con override, ideas usa custom: {p2}")

    p3 = settings_manager.get_setting(canal.id, "scripts.system_instruction_override", default=SCRIPTS_DEFAULT) == SCRIPTS_DEFAULT
    logger.info(f"P3 sin override, scripts usa default: {p3}")

    logger.info("✅ TODO CORRECTO" if p1 and p2 and p3 else "❌ FALLOS")

if __name__ == "__main__":
    main()