"""
generator.py

Genera las imágenes de un Script: primero usa IA de texto para dividir
el guion en escenas (la IA decide cuántas, o un número exacto si se
indica audio_duration_seconds), y después genera una imagen por
escena usando el ImageProvider configurado (SDXL local por defecto).
Los archivos generados se publican a través de StorageBackend.
"""

import tempfile
from pathlib import Path

from scripts.models import Script
from visuals import repository as visual_repository
from visuals.models import Visual
from visuals.exceptions import SceneSplittingError
from core.ai_providers.base import TextAIProvider
from core.ai_providers.factory import get_default_text_provider
from core.image_providers.base import ImageProvider
from core.image_providers.factory import get_default_image_provider
from core.storage.base import StorageBackend
from core.storage.factory import get_default_storage
from core.exceptions import AIProviderError, ImageProviderError
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_INSTRUCTION = (
    "Eres un director de fotografía para vídeos de YouTube. Recibes un guion "
    "y debes dividirlo en escenas visuales. Decide tú cuántas escenas son "
    "necesarias según el contenido (no hay un número fijo). "
    "Respondes ÚNICAMENTE con una escena por línea, cada línea con este "
    "formato exacto:\n"
    "ESCENA: <descripción visual en inglés, detallada, apta para un "
    "generador de imágenes>\n"
    "No incluyas numeración, títulos ni ningún otro texto."
)


def _split_script_into_scenes(
    script_content: str, provider: TextAIProvider, target_scene_count: int | None
) -> list[str]:
    """Usa IA de texto para dividir el guion en prompts de imagen, uno por escena."""
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
            scenes.append(line.split(":", 1)[1].strip())

    if not scenes:
        raise SceneSplittingError(
            f"La IA no devolvió ninguna escena en el formato esperado. Respuesta: {respuesta!r}"
        )

    return scenes


def generate_visuals_for_script(
    script: Script,
    audio_duration_seconds: float | None = None,
    text_provider: TextAIProvider | None = None,
    image_provider: ImageProvider | None = None,
    storage: StorageBackend | None = None,
) -> list[Visual]:
    """
    Divide el guion en escenas y genera una imagen por cada una,
    publicándolas en el almacenamiento configurado y registrándolas
    en la base de datos.
    """
    if text_provider is None:
        text_provider = get_default_text_provider()
    if image_provider is None:
        image_provider = get_default_image_provider()
    if storage is None:
        storage = get_default_storage()

    target_scene_count = None
    if audio_duration_seconds:
        scene_duration = settings.video["scene_duration_seconds"]
        target_scene_count = max(1, round(audio_duration_seconds / scene_duration))

    scene_prompts = _split_script_into_scenes(script.content, text_provider, target_scene_count)
    logger.info(f"Guion {script.id} dividido en {len(scene_prompts)} escenas.")

    visuals = []
    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)

        for scene_number, prompt in enumerate(scene_prompts, start=1):
            temp_path = temp_dir / f"scene_{scene_number}.png"
            key = f"visuals/script_{script.id}_scene_{scene_number}.png"

            try:
                image_provider.generate(prompt, temp_path)
            except ImageProviderError as error:
                logger.error(f"Fallo al generar la escena {scene_number}: {error}")
                raise

            storage.save(temp_path, key)

            visual = Visual(
                script_id=script.id,
                scene_number=scene_number,
                image_prompt=prompt,
                file_path=key,
            )
            saved_visual = visual_repository.create(visual)
            visuals.append(saved_visual)
            logger.info(f"Escena {scene_number}/{len(scene_prompts)} generada: {key}")

    return visuals