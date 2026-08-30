"""main.py — TEST voice per-canal: name/speed/pause_ms via channel_settings, fallback intacto."""
from core.logger import get_logger
from core.schema import initialize_database
from channels import manager as channel_manager
from channel_settings import manager as settings_manager
from ideas import repository as idea_repository
from ideas.models import Idea
from scripts import repository as script_repository
from scripts.models import Script
from voice.generator import generate_voice_for_script
from core.voice_providers.base import VoiceProvider

logger = get_logger(__name__)

class FakeVoiceProvider(VoiceProvider):
    def __init__(self):
        self.calls = []
    def generate(self, text, voice_name, output_path, speed=None, pause_ms=None):
        self.calls.append({"voice_name": voice_name, "speed": speed, "pause_ms": pause_ms})
        output_path.write_bytes(b"fake_audio")
        return output_path

def _make_script(channel_id, content_type="short"):
    idea = Idea(channel_id=channel_id, content_type=content_type, title="T", summary="S")
    idea = idea_repository.create(idea)
    script = Script(idea_id=idea.id, content_type=content_type, content="Texto de prueba.", word_count=3)
    return script_repository.create(script)

def main():
    initialize_database()

    canal_custom = channel_manager.create_channel(
        name="Canal Voz Custom", topic="t", shorts_per_week=1, long_videos_per_week=0, voice_name="ef_dora"
    )
    canal_default = channel_manager.create_channel(
        name="Canal Voz Default", topic="t", shorts_per_week=1, long_videos_per_week=0, voice_name="ef_dora"
    )

    settings_manager.set_setting(canal_custom.id, "voice.name", "em_alex")
    settings_manager.set_setting(canal_custom.id, "voice.speed", 0.7)
    settings_manager.set_setting(canal_custom.id, "voice.pause_ms", 300)

    script1 = _make_script(canal_custom.id)
    fake1 = FakeVoiceProvider()
    generate_voice_for_script(script1, canal_custom, provider=fake1)
    call1 = fake1.calls[0]
    p1 = call1["voice_name"] == "em_alex" and call1["speed"] == 0.7 and call1["pause_ms"] == 300
    logger.info(f"P1 canal con config propia usa sus valores: {p1} ({call1})")

    script2 = _make_script(canal_default.id)
    fake2 = FakeVoiceProvider()
    generate_voice_for_script(script2, canal_default, provider=fake2)
    call2 = fake2.calls[0]
    p2 = call2["voice_name"] == "ef_dora" and call2["speed"] == 0.95 and call2["pause_ms"] == 200
    logger.info(f"P2 canal sin config usa fallback (channels.voice_name + global): {p2} ({call2})")

    logger.info("✅ TODO CORRECTO" if p1 and p2 else "❌ FALLOS")

if __name__ == "__main__":
    main()