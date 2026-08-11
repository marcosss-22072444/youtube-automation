"""
generator.py

Genera título, descripción y etiquetas optimizados para YouTube a
partir de un Script, usando IA de texto (con fallback Gemini->Groq).
"""

from channels.models import Channel
from scripts.models import Script
from metadata import repository as metadata_repository
from metadata.models import Metadata
from metadata.exceptions import MetadataGenerationError
from core.ai_providers.base import TextAIProvider
from core.ai_providers.factory import get_default_text_provider
from core.exceptions import AIProviderError
from core.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_INSTRUCTION = (
    "Eres un experto en SEO para YouTube. Recibes el guion de un vídeo y "
    "la temática del canal, y debes generar título, descripción y "
    "etiquetas optimizados para maximizar clics y alcance, sin caer en "
    "clickbait engañoso (el contenido debe corresponder con lo prometido). "
    "Respondes ÚNICAMENTE con este formato exacto, sin nada más:\n"
    "TITULO: <título llamativo, máximo 100 caracteres>\n"
    "DESCRIPCION:\n"
    "<descripción de 3-5 líneas, con contexto del vídeo y una llamada a "
    "la acción para suscribirse>\n"
    "ETIQUETAS: <etiqueta1, etiqueta2, etiqueta3, ... (10-15 etiquetas, "
    "separadas por comas, relevantes para búsqueda en YouTube)>"
)


def _build_prompt(script: Script, channel: Channel) -> str:
    return (
        f"Temática del canal: {channel.topic}\n\n"
        f"Guion del vídeo:\n{script.content}"
    )


def _parse_ai_response(text: str) -> tuple[str, str, list[str]]:
    """Extrae título, descripción y etiquetas de la respuesta de la IA."""
    title = ""
    tags: list[str] = []
    description_lines: list[str] = []

    section = None  # None | "description"

    for line in text.strip().splitlines():
        stripped = line.strip()

        if stripped.upper().startswith("TITULO:"):
            title = stripped.split(":", 1)[1].strip()
            section = None
        elif stripped.upper().startswith("DESCRIPCION:"):
            section = "description"
            resto = stripped.split(":", 1)[1].strip()
            if resto:
                description_lines.append(resto)
        elif stripped.upper().startswith("ETIQUETAS:"):
            tags_raw = stripped.split(":", 1)[1].strip()
            tags = [tag.strip() for tag in tags_raw.split(",") if tag.strip()]
            section = None
        elif section == "description" and stripped:
            description_lines.append(stripped)

    description = "\n".join(description_lines)

    if not title or not description or not tags:
        raise MetadataGenerationError(
            f"La IA no devolvió el formato esperado. Respuesta: {text!r}"
        )

    return title, description, tags


def generate_metadata_for_script(
    script: Script, channel: Channel, provider: TextAIProvider | None = None
) -> Metadata:
    """
    Genera título, descripción y etiquetas para el guion dado, y los
    guarda en la base de datos.
    """
    if provider is None:
        provider = get_default_text_provider()

    prompt = _build_prompt(script, channel)

    try:
        respuesta = provider.generate(prompt, system_instruction=_SYSTEM_INSTRUCTION)
    except AIProviderError as error:
        raise MetadataGenerationError(f"Fallo al generar metadata con IA: {error}") from error

    title, description, tags = _parse_ai_response(respuesta)

    metadata = Metadata(script_id=script.id, title=title, description=description, tags=tags)
    saved_metadata = metadata_repository.create(metadata)

    logger.info(f"Metadata generada para guion {script.id}: '{title}' ({len(tags)} etiquetas)")
    return saved_metadata