"""
generator.py

Genera las imágenes de un Script: primero usa IA de texto para dividir
el guion en escenas (la IA decide cuántas), y después genera una
imagen por escena usando el ImageProvider configurado (FLUX por defecto).
"""

from scripts.models import Script
from visuals import repository as visual_repository
from visuals.models import Visual
from visuals.exceptions import SceneSplittingError
from core.ai_providers.base import TextAIProvider
from core.ai_providers.factory import get_default_text_provider
from core.image_providers.base import ImageProvider
from core.image_providers.factory import get_default_image_provider
from core.exceptions import AIProviderError, ImageProviderError
from core.constants import OUTPUT_DIR
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


def _split_script_into_scenes(script_content: str, provider: TextAIProvider) -> list[str]:
    """Usa IA de texto para dividir el guion en prompts de imagen, uno por escena."""
    try:
        respuesta = provider.generate(script_content, system_instruction=_SYSTEM_INSTRUCTION)
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
    text_provider: TextAIProvider | None = None,
    image_provider: ImageProvider | None = None,
) -> list[Visual]:
    """
    Divide el guion en escenas y genera una imagen por cada una,
    guardándolas en output/visuals/ y registrándolas en la base de datos.
    """
    if text_provider is None:
        text_provider = get_default_text_provider()
    if image_provider is None:
        image_provider = get_default_image_provider()

    scene_prompts = _split_script_into_scenes(script.content, text_provider)
    logger.info(f"Guion {script.id} dividido en {len(scene_prompts)} escenas.")

    visuals = []
    for scene_number, prompt in enumerate(scene_prompts, start=1):
        output_path = OUTPUT_DIR / "visuals" / f"script_{script.id}_scene_{scene_number}.png"

        try:
            image_provider.generate(prompt, output_path)
        except ImageProviderError as error:
            logger.error(f"Fallo al generar la escena {scene_number}: {error}")
            raise

        visual = Visual(
            script_id=script.id,
            scene_number=scene_number,
            image_prompt=prompt,
            file_path=str(output_path),
        )
        saved_visual = visual_repository.create(visual)
        visuals.append(saved_visual)
        logger.info(f"Escena {scene_number}/{len(scene_prompts)} generada: {output_path.name}")

    return visuals