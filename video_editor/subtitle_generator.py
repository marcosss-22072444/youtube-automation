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


def _split_into_chunks(text: str, words_per_group: int) -> list[str]:
    """Divide el texto en fragmentos cortos y legibles."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    chunks = []
    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue
        for i in range(0, len(words), words_per_group):
            chunk = " ".join(words[i:i + words_per_group])
            chunks.append(chunk)

    return chunks


def _calculate_segments(
    script_content: str, audio_duration_seconds: float, words_per_group: int = _MAX_WORDS_PER_SUBTITLE
) -> list[tuple[str, float, float]]:
    """Devuelve una lista de (texto, inicio_segundos, fin_segundos)."""
    chunks = _split_into_chunks(script_content, words_per_group)
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
    video_width: int, video_height: int, subtitle_config: dict,
) -> Path:
    """
    Genera un archivo .ass con resolución y estilo explícitos (fuente,
    color, borde, posición), tomados de config.yaml. Se usa para quemar
    los subtítulos en el vídeo de forma fiable, sin depender del
    escalado automático de FFmpeg al convertir desde .srt.
    """
    words_per_group = subtitle_config.get("words_per_group", _MAX_WORDS_PER_SUBTITLE)
    segments = _calculate_segments(script_content, audio_duration_seconds, words_per_group)
    sub_config = subtitle_config

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

def generate_ass_karaoke(
    word_timestamps: list[dict], output_path: Path,
    video_width: int, video_height: int, subtitle_config: dict,
) -> Path:
    """
    Genera un .ass estilo TikTok: bloques de N palabras (words_per_group),
    con la palabra activa resaltada en amarillo y el resto en blanco,
    usando timestamps reales por palabra (alineación forzada).
    """
    words_per_group = subtitle_config.get("words_per_group", 3)
    font_size = subtitle_config.get("font_size", 60)
    outline_color = _ASS_COLORS.get(subtitle_config.get("outline_color", "black"), "&H00000000")
    outline_width = subtitle_config.get("outline_width", 3)
    alignment = {"bottom": 2, "center": 5, "top": 8}.get(subtitle_config.get("position", "bottom"), 2)
    margin_v = round(video_height * 0.05)

    active_color = _ASS_COLORS.get(subtitle_config.get("active_word_color", "yellow"), "&H0000FFFF")
    inactive_color = _ASS_COLORS.get(subtitle_config.get("inactive_word_color", "white"), "&H00FFFFFF")

    # Cierra huecos de silencio: cada palabra dura hasta que empieza la
    # siguiente, para que el bloque no desaparezca entre palabra y palabra.
    for i in range(len(word_timestamps) - 1):
        word_timestamps[i]["end"] = word_timestamps[i + 1]["start"]

    groups = [word_timestamps[i:i + words_per_group] for i in range(0, len(word_timestamps), words_per_group)]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as ass_file:
        ass_file.write("[Script Info]\nScriptType: v4.00+\n")
        ass_file.write(f"PlayResX: {video_width}\nPlayResY: {video_height}\n\n")
        ass_file.write("[V4+ Styles]\n")
        ass_file.write(
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        )
        ass_file.write(
            f"Style: Default,Arial,{font_size},{inactive_color},&H000000FF,"
            f"{outline_color},&H00000000,1,0,0,0,100,100,0,0,1,"
            f"{outline_width},0,{alignment},20,20,{margin_v},1\n\n"
        )
        ass_file.write("[Events]\n")
        ass_file.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for group in groups:
            for i, active_word in enumerate(group):
                parts = []
                for j, w in enumerate(group):
                    color = active_color if j == i else inactive_color
                    parts.append(f"{{\\c{color}}}{w['word'].upper()}")
                text = "\\N".join(parts) if False else " ".join(parts)

                start = _format_ass_timestamp(active_word["start"])
                end = _format_ass_timestamp(active_word["end"])
                ass_file.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

    logger.info(f"Subtítulos karaoke .ass generados: {output_path} ({len(groups)} bloques)")
    return output_path