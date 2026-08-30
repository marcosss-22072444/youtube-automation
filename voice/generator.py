"""
generator.py

Genera el audio narrado de un Script, usando el VoiceProvider
configurado (Kokoro por defecto) y la voz asignada al canal del guion.
El archivo generado se publica a través de StorageBackend, para que
el resto del proyecto lo referencie por clave lógica, no por ruta.
"""

import tempfile
from pathlib import Path

from channels.models import Channel
from scripts.models import Script
from voice import repository as voice_repository
from voice.models import VoiceTrack
from core.voice_providers.base import VoiceProvider
from core.voice_providers.kokoro_provider import KokoroProvider
from core.storage.base import StorageBackend
from core.storage.factory import get_default_storage
from core.exceptions import VoiceProviderError
from core.logger import get_logger
from core.config import settings
from channel_settings import manager as settings_manager

logger = get_logger(__name__)


def generate_voice_for_script(
    script: Script,
    channel: Channel,
    provider: VoiceProvider | None = None,
    storage: StorageBackend | None = None,
) -> VoiceTrack:
    """
    Genera el audio narrado del guion dado, usando la voz configurada
    en el canal correspondiente, y lo publica en el almacenamiento
    configurado (local por defecto).
    """
    if provider is None:
        provider = KokoroProvider()
    if storage is None:
        storage = get_default_storage()

    key = f"voice/script_{script.id}.wav"

    with tempfile.TemporaryDirectory() as tmp:
        temp_path = Path(tmp) / f"script_{script.id}.wav"

        try:
            voice_name = settings_manager.get_setting(channel.id, "voice.name", default=channel.voice_name)
            speed = settings_manager.get_setting(
                channel.id, "voice.speed", default=settings.voice_naturalness.get("speed", 1.0)
            )
            pause_ms = settings_manager.get_setting(
                channel.id, "voice.pause_ms", default=settings.voice_naturalness.get("pause_between_segments_ms", 0)
            )
            provider.generate(script.content, voice_name, temp_path, speed=speed, pause_ms=pause_ms)
        except VoiceProviderError as error:
            raise error

        storage.save(temp_path, key)

    voice_track = VoiceTrack(
        script_id=script.id,
        file_path=key,
        voice_name=channel.voice_name,
    )
    saved_track = voice_repository.create(voice_track)

    logger.info(f"Audio generado para guion {script.id}: {key}")
    return saved_track