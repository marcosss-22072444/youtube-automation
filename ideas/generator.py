"""
generator.py

Genera una idea de vídeo nueva para un canal, usando IA, evitando
repetir temas ya usados. Usa el proveedor de IA intercambiable
definido en core/ai_providers (Gemini por ahora).
"""

from channels.models import Channel
from ideas import repository as idea_repository
from ideas.models import Idea
from ideas.exceptions import IdeaGenerationError
from core.ai_providers.base import TextAIProvider
from core.ai_providers.gemini_provider import GeminiProvider
from core.exceptions import AIProviderError
from core.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_INSTRUCTION = (
    "Eres un generador de ideas para vídeos de YouTube. "
    "Respondes SIEMPRE en exactamente este formato, sin nada más:\n"
    "TITULO: <título llamativo y corto>\n"
    "RESUMEN: <resumen de una frase de qué tratará el vídeo>"
)


def _build_prompt(channel: Channel, previous_titles: list[str]) -> str:
    """Construye el prompt pidiendo una idea nueva que no se solape."""
    if previous_titles:
        titulos_previos = "\n".join(f"- {t}" for t in previous_titles)
        contexto = (
            f"Estos son los títulos ya usados en este canal, NO repitas "
            f"ninguno de estos temas ni algo muy parecido:\n{titulos_previos}\n\n"
        )
    else:
        contexto = "Este canal todavía no tiene ideas previas.\n\n"

    return (
        f"El canal se llama '{channel.name}' y trata sobre: {channel.topic}.\n\n"
        f"{contexto}"
        f"Genera UNA idea de vídeo nueva y original para este canal."
    )


def _parse_ai_response(text: str) -> tuple[str, str]:
    """Extrae título y resumen de la respuesta de la IA."""
    title = ""
    summary = ""

    for line in text.strip().splitlines():
        line = line.strip()
        if line.upper().startswith("TITULO:"):
            title = line.split(":", 1)[1].strip()
        elif line.upper().startswith("RESUMEN:"):
            summary = line.split(":", 1)[1].strip()

    if not title or not summary:
        raise IdeaGenerationError(
            f"La IA no devolvió el formato esperado. Respuesta recibida: {text!r}"
        )

    return title, summary


def generate_idea_for_channel(channel: Channel, provider: TextAIProvider | None = None) -> Idea:
    """
    Genera una idea nueva para el canal dado, evitando repetir temas ya
    usados, la guarda en la base de datos y la devuelve.
    """
    if provider is None:
        provider = GeminiProvider()

    previous_titles = idea_repository.get_recent_titles_for_context(channel.id)
    prompt = _build_prompt(channel, previous_titles)

    try:
        respuesta = provider.generate(prompt, system_instruction=_SYSTEM_INSTRUCTION)
    except AIProviderError as error:
        raise IdeaGenerationError(f"Fallo al generar idea con IA: {error}") from error

    title, summary = _parse_ai_response(respuesta)

    idea = Idea(channel_id=channel.id, title=title, summary=summary)
    saved_idea = idea_repository.create(idea)

    logger.info(f"Idea generada para canal '{channel.name}': '{saved_idea.title}'")
    return saved_idea