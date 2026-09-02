"""
torchaudio_provider.py

Implementación de ForcedAlignmentProvider usando torchaudio (modelo
MMS_FA, alineación forzada CTC, GPU si está disponible). El texto ya
es conocido (es el guion generado por Kokoro) — esto NO transcribe,
solo alinea audio contra texto exacto.
"""

import re
import unicodedata
from pathlib import Path

from core.voice_providers.text_normalizer import normalize_text_for_tts

import torch
import torchaudio
from torchaudio.pipelines import MMS_FA as bundle

from core.alignment.base import ForcedAlignmentProvider, WordTimestamp
from core.alignment.exceptions import AlignmentError
from core.logger import get_logger

logger = get_logger(__name__)


class TorchaudioForcedAlignmentProvider(ForcedAlignmentProvider):
    """Proveedor de alineación forzada usando torchaudio MMS_FA (local, GPU)."""

    def __init__(self):
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Cargando modelo de alineación forzada MMS_FA en '{self._device}'...")
        self._model = bundle.get_model().to(self._device)
        self._tokenizer = bundle.get_tokenizer()
        self._aligner = bundle.get_aligner()

    def _strip_accents(self, word: str) -> str:
        decomposed = unicodedata.normalize("NFD", word.lower())
        without_accents = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
        return re.sub(r"[^a-zñ]", "", without_accents)

    def _build_alignment_plan(self, text: str) -> tuple[list[str], list[tuple[str, int, int]]]:
        """
        Devuelve (tokens_para_alinear, plan) donde plan es una lista de
        (palabra_original, indice_inicio_token, indice_fin_token_exclusivo)
        — permite fusionar N sub-tokens (de un número expandido) en 1
        timestamp con el texto original.
        """
        original_words = re.findall(r"\S+", text)
        align_tokens: list[str] = []
        plan: list[tuple[str, int, int]] = []

        for original_word in original_words:
            has_digit = any(c.isdigit() for c in original_word)
            source = normalize_text_for_tts(original_word) if has_digit else original_word
            sub_tokens = [self._strip_accents(w) for w in re.findall(r"[a-zA-Zñáéíóúü]+", source)]
            sub_tokens = [t for t in sub_tokens if t]

            if not sub_tokens:
                continue

            start_index = len(align_tokens)
            align_tokens.extend(sub_tokens)
            plan.append((original_word, start_index, start_index + len(sub_tokens)))

        return align_tokens, plan

    def align(self, audio_path: Path, text: str) -> list[WordTimestamp]:
        align_tokens, plan = self._build_alignment_plan(text)
        if not align_tokens:
            raise AlignmentError("El texto no contiene palabras alineables.")

        try:
            waveform, sample_rate = torchaudio.load(str(audio_path))
            if sample_rate != bundle.sample_rate:
                waveform = torchaudio.functional.resample(waveform, sample_rate, bundle.sample_rate)
            waveform = waveform.to(self._device)

            with torch.inference_mode():
                emission, _ = self._model(waveform)
                token_spans = self._aligner(emission[0], self._tokenizer(align_tokens))

            num_frames = emission.shape[1]
            ratio = waveform.shape[1] / num_frames / bundle.sample_rate

            token_timestamps = []
            for spans in token_spans:
                token_timestamps.append((spans[0].start * ratio, spans[-1].end * ratio))

            timestamps = []
            for original_word, start_idx, end_idx in plan:
                sub_spans = token_timestamps[start_idx:end_idx]
                timestamps.append(
                    WordTimestamp(word=original_word, start_seconds=sub_spans[0][0], end_seconds=sub_spans[-1][1])
                )

            return timestamps

        except Exception as error:
            raise AlignmentError(f"Fallo en alineación forzada: {error}") from error