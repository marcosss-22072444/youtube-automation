"""
generator.py

Genera el audio narrado de un Script, usando el VoiceProvider
configurado (Kokoro por defecto) y la voz asignada al canal del guion.
"""

from channels.models import Channel
from scripts.models import Script
from voice import repository as voice_repository
from voice.models import VoiceTrack
from core.voice_providers.base import VoiceProvider
from core.voice_providers.kokoro_provider import KokoroProvider
from core.exceptions import VoiceProviderError
from core.constants import OUTPUT_DIR
from core.logger import get_logger

logger = get_logger(__name__)


def generate_voice_for_script(
    script: Script,
    channel: Channel,
    provider: VoiceProvider | None = None,
) -> VoiceTrack:
    """
    Genera el audio narrado del guion dado, usando la voz configurada
    en el canal correspondiente, y lo guarda en output/.
    """
    if provider is None:
        provider = KokoroProvider()

    output_path = OUTPUT_DIR / "voice" / f"script_{script.id}.wav"

    try:
        provider.generate(script.content, channel.voice_name, output_path)
    except VoiceProviderError as error:
        raise error

    voice_track = VoiceTrack(
        script_id=script.id,
        file_path=str(output_path),
        voice_name=channel.voice_name,
    )
    saved_track = voice_repository.create(voice_track)

    logger.info(f"Audio generado para guion {script.id}: {output_path}")
    return saved_track