"""
kokoro_provider.py

Implementación concreta de VoiceProvider usando Kokoro TTS, que se
ejecuta localmente (sin depender de una API externa).
"""

from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

from core.voice_providers.base import VoiceProvider
from core.voice_providers.text_normalizer import normalize_text_for_tts, normalize_text_for_tts_with_ai
from core.config import settings
from core.exceptions import VoiceProviderError
from core.logger import get_logger

logger = get_logger(__name__)

_SAMPLE_RATE = 24000

# Kokoro agrupa sus voces por idioma según la primera letra del nombre
# de la voz (ej: 'ef_dora' -> español, 'af_heart' -> inglés americano).
_LANG_CODE_BY_PREFIX = {
    "a": "a",  # inglés americano
    "b": "b",  # inglés británico
    "e": "e",  # español
    "f": "f",  # francés
    "j": "j",  # japonés
    "z": "z",  # chino mandarín
}


class KokoroProvider(VoiceProvider):
    """Proveedor de voz IA usando Kokoro TTS (ejecución local)."""

    def __init__(self):
        # Cache de pipelines por idioma: crear un KPipeline es costoso
        # (carga el modelo), así que reutilizamos uno por idioma detectado.
        self._pipelines: dict[str, KPipeline] = {}

    def _get_pipeline(self, voice_name: str) -> KPipeline:
        prefix = voice_name[0].lower()
        lang_code = _LANG_CODE_BY_PREFIX.get(prefix)

        if lang_code is None:
            raise VoiceProviderError(
                f"No se reconoce el idioma de la voz '{voice_name}'."
            )

        if lang_code not in self._pipelines:
            self._pipelines[lang_code] = KPipeline(lang_code=lang_code)

        return self._pipelines[lang_code]

    def generate(self, text: str, voice_name: str, output_path: Path) -> Path:
        try:
            text = normalize_text_for_tts(text)
            text = normalize_text_for_tts_with_ai(text)
            pipeline = self._get_pipeline(voice_name)
            speed = settings.voice_naturalness.get("speed", 1.0)
            generator = pipeline(text, voice=voice_name, speed=speed)

            pause_ms = settings.voice_naturalness.get("pause_between_segments_ms", 0)
            silence_samples = int(_SAMPLE_RATE * (pause_ms / 1000))
            silence = np.zeros(silence_samples, dtype=np.float32)

            audio_chunks = []
            for _, _, audio in generator:
                audio_chunks.append(audio)
                audio_chunks.append(silence)

            if not audio_chunks:
                raise VoiceProviderError("Kokoro no generó ningún audio.")

            full_audio = np.concatenate(audio_chunks)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(output_path), full_audio, _SAMPLE_RATE)

            return output_path

        except VoiceProviderError:
            raise
        except Exception as error:
            logger.error(f"Error al generar audio con Kokoro: {error}")
            raise VoiceProviderError(f"Fallo en KokoroProvider: {error}") from error