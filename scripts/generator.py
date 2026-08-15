"""
generator.py

Genera un guion completo a partir de una Idea, usando IA. Calcula la
longitud objetivo (en palabras) a partir de la duración configurada
en config.yaml (segundos) y la velocidad de narración (palabras/minuto).
"""

from ideas.models import Idea
from scripts import repository as script_repository
from scripts.models import Script
from scripts.exceptions import ScriptGenerationError
from core.ai_providers.base import TextAIProvider
from core.ai_providers.factory import get_default_text_provider
from core.config import settings
from core.exceptions import AIProviderError
from core.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_INSTRUCTION = (
    "Eres un guionista profesional de vídeos de YouTube. Escribes guiones "
    "completos, listos para narrar, con gancho inicial, desarrollo y cierre. "
    "Respondes ÚNICAMENTE con el texto del guion, sin títulos, sin encabezados, "
    "sin explicaciones adicionales."
)


def _calculate_target_words(content_type: str) -> int:
    """Calcula las palabras objetivo según duración configurada y velocidad de narración."""
    duration_seconds = settings.script_duration_seconds.get(content_type)
    if duration_seconds is None:
        raise ScriptGenerationError(
            f"No hay duración configurada para content_type '{content_type}' "
            f"en config.yaml (script_duration_seconds)."
        )
    return round((duration_seconds / 60) * settings.narration_wpm)


def _build_prompt(idea: Idea, target_words: int) -> str:
    return (
        f"Título del vídeo: {idea.title}\n"
        f"Resumen: {idea.summary}\n\n"
        f"Escribe el guion completo de este vídeo, en aproximadamente "
        f"{target_words} palabras."
    )


def generate_script_for_idea(idea: Idea, provider: TextAIProvider | None = None) -> Script:
    """
    Genera el guion completo de una idea, calculando la longitud según
    la duración configurada para su content_type, y lo guarda.
    """
    if provider is None:
        provider = get_default_text_provider()

    target_words = _calculate_target_words(idea.content_type)
    prompt = _build_prompt(idea, target_words)

    try:
        content = provider.generate(prompt, system_instruction=_SYSTEM_INSTRUCTION)
    except AIProviderError as error:
        raise ScriptGenerationError(f"Fallo al generar guion con IA: {error}") from error

    if not content.strip():
        raise ScriptGenerationError("La IA devolvió un guion vacío.")

    word_count = len(content.split())

    script = Script(
        idea_id=idea.id, content_type=idea.content_type,
        content=content.strip(), word_count=word_count,
    )
    saved_script = script_repository.create(script)

    logger.info(
        f"Guion generado para idea '{idea.title}' "
        f"(objetivo={target_words} palabras, real={word_count} palabras)"
    )
    return saved_script