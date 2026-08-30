"""
generator.py

Genera los assets visuales de un Script: primero usa IA de texto para
dividir el guion en escenas (un número exacto si se indica
audio_duration_seconds), y por cada escena resuelve un asset visual
(clip de stock o imagen SDXL como fallback) a través de
SceneAssetResolver. Los archivos generados se publican mediante
StorageBackend.
"""

import random
import tempfile
import time
from pathlib import Path

from scripts.models import Script
from ideas import repository as idea_repository
from visuals import repository as visual_repository
from visuals.models import Visual
from visuals.exceptions import SceneSplittingError
from core.ai_providers.base import TextAIProvider
from core.ai_providers.factory import get_text_provider_for_channel
from core.media_providers.scene_asset_resolver import SceneAssetResolver
from core.storage.base import StorageBackend
from core.storage.factory import get_default_storage
from core.exceptions import AIProviderError
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_INSTRUCTION = (
    "Eres un editor de vídeo que busca clips de stock para un guion de "
    "YouTube. Divide el guion en escenas visuales (decide tú cuántas, "
    "salvo que se indique un número exacto). Para CADA escena, genera "
    "varios niveles de búsqueda en inglés, de más específico a más genérico:\n"
    "- Nivel 1: el sujeto/objeto EXACTO mencionado (nombre de modelo, pieza concreta)\n"
    "- Nivel 2: un concepto muy cercano si el nivel 1 fuera raro de encontrar\n"
    "- Nivel 3: la categoría genérica relacionada\n"
    "Responde con una línea por escena, formato exacto:\n"
    "ESCENA: <nivel1> | <nivel2> | <nivel3>\n"
    "No incluyas numeración ni texto adicional."
)


def _split_script_into_scenes(
    script_content: str, provider: TextAIProvider, target_scene_count: int | None
) -> list[str]:
    """Usa IA de texto para dividir el guion en consultas de búsqueda, una por escena."""
    if target_scene_count:
        instruction = _SYSTEM_INSTRUCTION.replace(
            "Decide tú cuántas escenas son necesarias según el contenido (no hay un número fijo).",
            f"Debes dividirlo en EXACTAMENTE {target_scene_count} escenas, "
            f"repartidas en orden a lo largo de todo el guion, de principio a fin.",
        )
    else:
        instruction = _SYSTEM_INSTRUCTION

    try:
        respuesta = provider.generate(script_content, system_instruction=instruction)
    except AIProviderError as error:
        raise SceneSplittingError(f"Fallo al dividir el guion en escenas: {error}") from error

    scenes = []
    for line in respuesta.strip().splitlines():
        line = line.strip()
        if line.upper().startswith("ESCENA:"):
            query_levels = [q.strip() for q in line.split(":", 1)[1].split("|") if q.strip()]
            if query_levels:
                scenes.append(query_levels)

    if not scenes:
        raise SceneSplittingError(
            f"La IA no devolvió ninguna escena en el formato esperado. Respuesta: {respuesta!r}"
        )

    return scenes


def generate_visuals_for_script(
    script: Script,
    audio_duration_seconds: float | None = None,
    channel_id: int | None = None,
    text_provider: TextAIProvider | None = None,
    storage: StorageBackend | None = None,
) -> list[Visual]:
    """
    Divide el guion en escenas y resuelve un asset visual por cada una
    (clip de stock, o imagen SDXL como fallback), publicándolos en el
    almacenamiento configurado y registrándolos en la base de datos.
    """
    if channel_id is None:
        idea = idea_repository.get_by_id(script.idea_id)
        channel_id = idea.channel_id

    if text_provider is None:
        text_provider = get_text_provider_for_channel(channel_id)
    if storage is None:
        storage = get_default_storage()

    target_scene_count = None
    if audio_duration_seconds:
        duration_range = settings.video["scene_duration"][script.content_type]
        mid_scene_duration = (duration_range["min_seconds"] + duration_range["max_seconds"]) / 2
        target_scene_count = max(1, round(audio_duration_seconds / mid_scene_duration))

    scene_queries = _split_script_into_scenes(script.content, text_provider, target_scene_count)
    logger.info(f"Guion {script.id} dividido en {len(scene_queries)} escenas.")

    resolver = SceneAssetResolver(channel_id=channel_id)
    visuals = []

    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)

        delay_range = settings.media_sources["request_delay_seconds"]
        pause_every = settings.media_sources["pause_every_n_scenes"]
        pause_range = settings.media_sources["pause_seconds"]

        for scene_number, query_levels in enumerate(scene_queries, start=1):
            asset_type, source = resolver.resolve(query_levels, script.content_type, temp_dir / f"scene_{scene_number}_raw")

            # El resolver guarda con extensión implícita según el tipo;
            # normalizamos la ruta real generada antes de publicarla.
            raw_path = temp_dir / f"scene_{scene_number}_raw"
            extension = ".mp4" if asset_type == "video" else ".png"
            final_temp_path = raw_path.with_suffix(extension)
            if raw_path.exists() and not final_temp_path.exists():
                raw_path.rename(final_temp_path)

            key = f"visuals/script_{script.id}_scene_{scene_number}{extension}"
            storage.save(final_temp_path, key)

            visual = Visual(
                script_id=script.id,
                scene_number=scene_number,
                image_prompt=query_levels[0],
                file_path=key,
                asset_type=asset_type,
                source=source,
            )
            saved_visual = visual_repository.create(visual)
            visuals.append(saved_visual)
            logger.info(f"Escena {scene_number}/{len(scene_queries)}: {asset_type} de {source} ({key})")

            if scene_number < len(scene_queries):
                if scene_number % pause_every == 0:
                    long_pause = random.uniform(pause_range["min"], pause_range["max"])
                    logger.info(f"Pausa larga de {long_pause:.1f}s tras {scene_number} escenas (evitar bloqueo de API)...")
                    time.sleep(long_pause)
                else:
                    delay = random.uniform(delay_range["min"], delay_range["max"])
                    time.sleep(delay)

    return visuals