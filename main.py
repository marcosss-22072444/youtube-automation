"""main.py — TEST ai.text_model_override + visuals.orientation_override."""
from core.logger import get_logger
from core.schema import initialize_database
from core.config import settings
from channels import manager as channel_manager
from channel_settings import manager as settings_manager
from core.ai_providers.factory import get_text_provider_for_channel
from core.ai_providers.gemini_provider import GeminiProvider
from core.media_providers.scene_asset_resolver import SceneAssetResolver

logger = get_logger(__name__)

def main():
    initialize_database()
    canal = channel_manager.create_channel(name="Canal Model Test", topic="t", shorts_per_week=1, long_videos_per_week=0)

    provider = get_text_provider_for_channel(canal.id)
    gemini = provider._providers[0]
    p1 = gemini.model_name == settings.gemini_model
    logger.info(f"P1 sin override, usa modelo global: {p1} ({gemini.model_name})")

    settings_manager.set_setting(canal.id, "ai.gemini_model_override", "gemini-custom-test")
    provider2 = get_text_provider_for_channel(canal.id)
    p2 = provider2._providers[0].model_name == "gemini-custom-test"
    logger.info(f"P2 con override, usa modelo custom: {p2} ({provider2._providers[0].model_name})")

    resolver = SceneAssetResolver(channel_id=canal.id)
    p3 = resolver._channel_id == canal.id
    logger.info(f"P3 resolver guarda channel_id: {p3}")

    settings_manager.set_setting(canal.id, "visuals.orientation_override.short", "horizontal")
    override = settings_manager.get_setting(canal.id, "visuals.orientation_override.short", default="vertical")
    p4 = override == "horizontal"
    logger.info(f"P4 override de orientacion aplicado: {p4}")

    logger.info("✅ TODO CORRECTO" if p1 and p2 and p3 and p4 else "❌ FALLOS")

if __name__ == "__main__":
    main()