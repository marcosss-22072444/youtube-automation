"""main.py — TEST channel_settings: aislamiento, fallback, upsert, JSON, no-config."""
from core.logger import get_logger
from core.schema import initialize_database
from channels import manager as channel_manager
from channel_settings import manager as settings_manager

logger = get_logger(__name__)

def main():
    initialize_database()
    c1 = channel_manager.create_channel(name="Canal Settings A", topic="t", shorts_per_week=1, long_videos_per_week=0)
    c2 = channel_manager.create_channel(name="Canal Settings B", topic="t", shorts_per_week=1, long_videos_per_week=0)

    p1 = settings_manager.get_setting(c1.id, "voice.speed", default=0.95) == 0.95
    logger.info(f"P1 fallback global sin config: {p1}")

    settings_manager.set_setting(c1.id, "voice.speed", 0.8)
    p2 = settings_manager.get_setting(c1.id, "voice.speed", default=0.95) == 0.8
    logger.info(f"P2 set/get valor propio: {p2}")

    p3 = settings_manager.get_setting(c2.id, "voice.speed", default=0.95) == 0.95
    logger.info(f"P3 aislamiento entre canales: {p3}")

    settings_manager.set_setting(c1.id, "voice.speed", 0.7)
    p4 = settings_manager.get_setting(c1.id, "voice.speed", default=0.95) == 0.7
    logger.info(f"P4 upsert sobrescribe: {p4}")

    subtitle_cfg = {"font_size": 60, "color": "yellow", "position": "bottom"}
    settings_manager.set_setting(c1.id, "subtitles.style", subtitle_cfg)
    p5 = settings_manager.get_setting(c1.id, "subtitles.style", default={}) == subtitle_cfg
    logger.info(f"P5 JSON complejo (dict): {p5}")

    c3 = channel_manager.create_channel(name="Canal Sin Config", topic="t", shorts_per_week=1, long_videos_per_week=0)
    p6 = (settings_manager.get_setting(c3.id, "voice.speed", default=0.95) == 0.95 and
          settings_manager.list_settings(c3.id) == {})
    logger.info(f"P6 canal sin config usa defaults: {p6}")

    settings_manager.delete_setting(c1.id, "voice.speed")
    p7 = settings_manager.get_setting(c1.id, "voice.speed", default=0.95) == 0.95
    logger.info(f"P7 delete vuelve a fallback: {p7}")

    todas = all([p1, p2, p3, p4, p5, p6, p7])
    logger.info("✅ TODO CORRECTO" if todas else "❌ FALLOS")

if __name__ == "__main__":
    main()