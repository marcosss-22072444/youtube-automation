"""main.py — TEST subtitles per-canal: font_size/color/words_per_group via channel_settings."""
from core.logger import get_logger
from core.schema import initialize_database
from channels import manager as channel_manager
from channel_settings import manager as settings_manager
from core.config import settings

logger = get_logger(__name__)

def main():
    initialize_database()
    canal = channel_manager.create_channel(name="Canal Subs Custom", topic="t", shorts_per_week=1, long_videos_per_week=0)
    canal_default = channel_manager.create_channel(name="Canal Subs Default", topic="t", shorts_per_week=1, long_videos_per_week=0)

    settings_manager.set_setting(canal.id, "subtitles.font_size", 90)
    settings_manager.set_setting(canal.id, "subtitles.font_color", "red")
    settings_manager.set_setting(canal.id, "subtitles.words_per_group", 3)

    global_cfg = settings.video["subtitles"]

    resolved_custom = {
        key: settings_manager.get_setting(canal.id, f"subtitles.{key}", default=v)
        for key, v in global_cfg.items()
    }
    resolved_custom["words_per_group"] = settings_manager.get_setting(canal.id, "subtitles.words_per_group", default=10)

    resolved_default = {
        key: settings_manager.get_setting(canal_default.id, f"subtitles.{key}", default=v)
        for key, v in global_cfg.items()
    }
    resolved_default["words_per_group"] = settings_manager.get_setting(canal_default.id, "subtitles.words_per_group", default=10)

    p1 = resolved_custom["font_size"] == 90 and resolved_custom["font_color"] == "red" and resolved_custom["words_per_group"] == 3
    logger.info(f"P1 canal con config propia resuelve valores correctos: {p1} ({resolved_custom['font_size']}, {resolved_custom['font_color']}, {resolved_custom['words_per_group']})")

    p2 = (resolved_default["font_size"] == global_cfg["font_size"] and
          resolved_default["font_color"] == global_cfg["font_color"] and
          resolved_default["words_per_group"] == 10)
    logger.info(f"P2 canal sin config usa fallback global intacto: {p2} ({resolved_default['font_size']}, {resolved_default['font_color']}, {resolved_default['words_per_group']})")

    logger.info("✅ TODO CORRECTO" if p1 and p2 else "❌ FALLOS")

if __name__ == "__main__":
    main()