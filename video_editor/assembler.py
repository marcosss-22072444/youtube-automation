"""
assembler.py

Monta el vídeo final: genera un clip con efecto Ken Burns por cada
imagen, los concatena, y añade la pista de audio y los subtítulos
incrustados usando FFmpeg. Todas las entradas/salidas de archivo
pasan por StorageBackend, usando claves lógicas en vez de rutas.
"""

import tempfile
from pathlib import Path

import soundfile as sf

from scripts.models import Script
from visuals.models import Visual
from voice.models import VoiceTrack
from video_editor import repository as video_repository
from video_editor.models import Video
from video_editor.subtitle_generator import generate_srt, generate_ass
from video_editor.exceptions import VideoAssemblyError
from core.storage.base import StorageBackend
from core.storage.factory import get_default_storage
from core.config import settings
from core.logger import get_logger
from ideas import repository as idea_repository
from channel_settings import manager as settings_manager

import subprocess

logger = get_logger(__name__)

_FPS = 25
_WIDTH = 1080
_HEIGHT = 1920

_ASS_COLORS = {
    "white": "&H00FFFFFF",
    "yellow": "&H0000FFFF",
    "black": "&H00000000",
    "red": "&H000000FF",
    "green": "&H0000FF00",
    "cyan": "&H00FFFF00",
    "orange": "&H0000A5FF",
}


def _get_audio_duration(audio_path: Path) -> float:
    """Devuelve la duración del audio en segundos."""
    info = sf.info(str(audio_path))
    return info.frames / info.samplerate


def _build_scene_durations(visuals: list[Visual], audio_duration: float) -> list[tuple[Visual, float]]:
    """Asigna a cada Visual (ya en orden narrativo) una duración
    proporcional, repartiendo la duración total del audio a partes
    iguales entre las escenas generadas."""
    if not visuals:
        raise VideoAssemblyError("No hay imágenes disponibles para montar el vídeo.")

    per_scene = audio_duration / len(visuals)
    return [(visual, per_scene) for visual in visuals]


def _render_scene_segment(asset_type: str, source_path: Path, duration: float, output_path: Path) -> None:
    """
    Genera un clip de vídeo de duración exacta a partir de una escena.
    Si es una imagen fija, aplica el efecto Ken Burns (zoom suave) si
    está activado. Si es un clip de vídeo de stock, lo recorta o lo
    repite en bucle hasta cubrir la duración asignada, sin Ken Burns
    (el clip ya tiene movimiento propio) y sin su audio original.
    """
    scale_crop = f"scale={_WIDTH}:{_HEIGHT}:force_original_aspect_ratio=increase,crop={_WIDTH}:{_HEIGHT}"

    if asset_type == "video":
        vf = f"{scale_crop},fps={_FPS}"
        command = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(source_path),
            "-vf", vf,
            "-t", str(duration),
            "-an",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
    else:
        ken_burns = settings.video["ken_burns"]
        num_frames = max(1, round(duration * _FPS))

        if ken_burns.get("enabled", True):
            zoom_end = ken_burns.get("zoom_end", 1.15)
            zoompan = (
                f"zoompan=z='min(zoom+{(zoom_end - 1.0) / num_frames:.6f},{zoom_end})'"
                f":d={num_frames}:s={_WIDTH}x{_HEIGHT}:fps={_FPS}"
            )
            vf = f"{scale_crop},{zoompan}"
        else:
            vf = f"{scale_crop},fps={_FPS}"

        command = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(source_path),
            "-vf", vf,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise VideoAssemblyError(f"FFmpeg falló generando escena {source_path.name}: {result.stderr[-800:]}")


def _concat_segments(segment_paths: list[Path], output_path: Path, temp_dir: Path) -> None:
    """Concatena varios clips de vídeo en uno solo, sin recodificar."""
    list_file = temp_dir / "concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for segment in segment_paths:
            f.write(f"file '{segment.as_posix()}'\n")

    command = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output_path),
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise VideoAssemblyError(f"FFmpeg falló concatenando escenas: {result.stderr[-800:]}")

def _mux_audio_and_subtitles(
    background_video: Path, audio_path: Path, ass_path: Path | None, output_path: Path
) -> None:
    """Combina el vídeo (Ken Burns) con la pista de audio y, si está
    activado, incrusta los subtítulos desde un .ass ya estilizado,
    usando filter_complex con etiquetas explícitas para garantizar
    que el audio se incluye siempre."""
    sub_config = settings.video["subtitles"]
    use_subtitles = ass_path is not None and sub_config.get("burn_in", True) and sub_config.get("enabled", True)

    command = [
        "ffmpeg", "-y",
        "-i", str(background_video),
        "-i", str(audio_path),
    ]

    if use_subtitles:
        ass_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")
        filter_complex = f"[0:v]ass='{ass_escaped}'[vout]"
        command += ["-filter_complex", filter_complex, "-map", "[vout]", "-map", "1:a"]
    else:
        command += ["-map", "0:v", "-map", "1:a"]

    command += [
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(output_path),
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise VideoAssemblyError(f"FFmpeg falló en el montaje final: {result.stderr[-800:]}")


def assemble_video(
    script: Script,
    visuals: list[Visual],
    voice_track: VoiceTrack,
    channel_id: int | None = None,
    storage: StorageBackend | None = None,
) -> Video:
    """
    Monta el vídeo final combinando las imágenes (con efecto Ken Burns),
    el audio narrado y los subtítulos sincronizados, y lo publica en
    el almacenamiento configurado.
    """
    if storage is None:
        storage = get_default_storage()

    if channel_id is None:
        idea = idea_repository.get_by_id(script.idea_id)
        channel_id = idea.channel_id

    global_sub_config = settings.video["subtitles"]
    subtitle_config = {
        key: settings_manager.get_setting(channel_id, f"subtitles.{key}", default=default_value)
        for key, default_value in global_sub_config.items()
    }
    subtitle_config["words_per_group"] = settings_manager.get_setting(
        channel_id, "subtitles.words_per_group", default=10
    )

    audio_path = storage.resolve_path(voice_track.file_path)
    audio_duration = _get_audio_duration(audio_path)

    scene_plan = _build_scene_durations(visuals, audio_duration)

    logger.info(
        f"Montando vídeo para guion {script.id}: {audio_duration:.1f}s de audio, "
        f"{len(scene_plan)} escenas (~{audio_duration / len(scene_plan):.1f}s cada una)."
    )

    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        segment_paths = []

        for index, (visual, duration) in enumerate(scene_plan):
            source_path = storage.resolve_path(visual.file_path)
            segment_path = temp_dir / f"segment_{index:04}.mp4"
            _render_scene_segment(visual.asset_type, source_path, duration, segment_path)
            segment_paths.append(segment_path)

        background_path = temp_dir / "background.mp4"
        _concat_segments(segment_paths, background_path, temp_dir)

        srt_key = None
        if settings.video["subtitles"].get("export_srt", True):
            srt_temp_path = temp_dir / f"script_{script.id}.srt"
            generate_srt(script.content, audio_duration, srt_temp_path)
            srt_key = f"subtitles/script_{script.id}.srt"
            storage.save(srt_temp_path, srt_key)

        ass_temp_path = None
        if settings.video["subtitles"].get("enabled", True):
            ass_temp_path = temp_dir / f"script_{script.id}.ass"
            generate_ass(script.content, audio_duration, ass_temp_path, _WIDTH, _HEIGHT, subtitle_config)

        video_temp_path = temp_dir / f"script_{script.id}.mp4"
        _mux_audio_and_subtitles(background_path, audio_path, ass_temp_path, video_temp_path)

        video_key = f"videos/script_{script.id}.mp4"
        storage.save(video_temp_path, video_key)

    video = Video(
        script_id=script.id,
        file_path=video_key,
        srt_path=srt_key,
        duration_seconds=audio_duration,
    )
    saved_video = video_repository.create(video)
    logger.info(f"Vídeo final generado: {video_key}")
    return saved_video