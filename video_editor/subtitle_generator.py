"""
subtitle_generator.py

Divide el texto de un guion en líneas de subtítulo, calcula su
sincronización proporcional a la duración real del audio, y genera
tanto un archivo .srt (para exportar/uso externo) como un .ass (para
quemar en el vídeo, con estilo y resolución explícitos y fiables).
"""

import re
from pathlib import Path

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

_MAX_WORDS_PER_SUBTITLE = 10


_ASS_COLORS = {
    "white": "&H00FFFFFF",
    "yellow": "&H0000FFFF",
    "black": "&H00000000",
    "red": "&H000000FF",
    "green": "&H0000FF00",
    "cyan": "&H00FFFF00",
    "orange": "&H0000A5FF",
}


def _split_into_chunks(text: str) -> list[str]:
    """Divide el texto en fragmentos cortos y legibles."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    chunks = []
    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue
        for i in range(0, len(words), _MAX_WORDS_PER_SUBTITLE):
            chunk = " ".join(words[i:i + _MAX_WORDS_PER_SUBTITLE])
            chunks.append(chunk)

    return chunks


def _calculate_segments(script_content: str, audio_duration_seconds: float) -> list[tuple[str, float, float]]:
    """Devuelve una lista de (texto, inicio_segundos, fin_segundos)."""
    chunks = _split_into_chunks(script_content)
    total_words = sum(len(chunk.split()) for chunk in chunks)

    if total_words == 0:
        raise ValueError("El guion no contiene texto para generar subtítulos.")

    segments = []
    current_time = 0.0
    for chunk in chunks:
        chunk_words = len(chunk.split())
        chunk_duration = (chunk_words / total_words) * audio_duration_seconds
        start_time = current_time
        end_time = current_time + chunk_duration
        current_time = end_time
        segments.append((chunk, start_time, end_time))

    return segments


def _format_srt_timestamp(seconds: float) -> str:
    total_ms = round(seconds * 1000)
    hours, remainder_ms = divmod(total_ms, 3_600_000)
    minutes, remainder_ms = divmod(remainder_ms, 60_000)
    secs, ms = divmod(remainder_ms, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def _format_ass_timestamp(seconds: float) -> str:
    total_cs = round(seconds * 100)
    hours, remainder_cs = divmod(total_cs, 360_000)
    minutes, remainder_cs = divmod(remainder_cs, 6_000)
    secs, cs = divmod(remainder_cs, 100)
    return f"{hours}:{minutes:02}:{secs:02}.{cs:02}"


def generate_srt(script_content: str, audio_duration_seconds: float, output_path: Path) -> Path:
    """Genera un archivo .srt estándar, sincronizado proporcionalmente."""
    segments = _calculate_segments(script_content, audio_duration_seconds)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as srt_file:
        for index, (text, start, end) in enumerate(segments, start=1):
            srt_file.write(f"{index}\n")
            srt_file.write(f"{_format_srt_timestamp(start)} --> {_format_srt_timestamp(end)}\n")
            srt_file.write(f"{text}\n\n")

    logger.info(f"Subtítulos .srt generados: {output_path} ({len(segments)} líneas)")
    return output_path


def generate_ass(
    script_content: str, audio_duration_seconds: float, output_path: Path,
    video_width: int, video_height: int,
) -> Path:
    """
    Genera un archivo .ass con resolución y estilo explícitos (fuente,
    color, borde, posición), tomados de config.yaml. Se usa para quemar
    los subtítulos en el vídeo de forma fiable, sin depender del
    escalado automático de FFmpeg al convertir desde .srt.
    """
    segments = _calculate_segments(script_content, audio_duration_seconds)
    sub_config = settings.video["subtitles"]

    alignment = {"bottom": 2, "center": 5, "top": 8}.get(sub_config.get("position", "bottom"), 2)
    font_color = _ASS_COLORS.get(sub_config.get("font_color", "white"), "&H00FFFFFF")
    outline_color = _ASS_COLORS.get(sub_config.get("outline_color", "black"), "&H00000000")
    font_size = sub_config.get("font_size", 60)
    outline_width = sub_config.get("outline_width", 3)
    margin_v = round(video_height * 0.05)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as ass_file:
        ass_file.write("[Script Info]\n")
        ass_file.write("ScriptType: v4.00+\n")
        ass_file.write(f"PlayResX: {video_width}\n")
        ass_file.write(f"PlayResY: {video_height}\n\n")

        ass_file.write("[V4+ Styles]\n")
        ass_file.write(
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        )
        ass_file.write(
            f"Style: Default,Arial,{font_size},{font_color},&H000000FF,"
            f"{outline_color},&H00000000,1,0,0,0,100,100,0,0,1,"
            f"{outline_width},0,{alignment},20,20,{margin_v},1\n\n"
        )

        ass_file.write("[Events]\n")
        ass_file.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for text, start, end in segments:
            text_escaped = text.replace("\n", "\\N")
            ass_file.write(
                f"Dialogue: 0,{_format_ass_timestamp(start)},{_format_ass_timestamp(end)},"
                f"Default,,0,0,0,,{text_escaped}\n"
            )

    logger.info(f"Subtítulos .ass generados: {output_path} ({len(segments)} líneas)")
    return output_path