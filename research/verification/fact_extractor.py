"""
fact_extractor.py

Usa un LLM (Gemini/Groq, vía get_text_provider_for_channel) para
extraer hechos ESTRUCTURADOS y CITADOS a partir de las fuentes
recuperadas. El LLM nunca actúa como fuente de verdad: solo puede
citar fuentes que existen realmente en la lista proporcionada —
cualquier hecho sin cita válida se descarta.
"""

import re

from research.models import ExtractedFact, Source, FACT_UNCERTAIN
from research.search.base import RawSearchResult
from research.exceptions import FactExtractionError
from core.ai_providers.base import TextAIProvider
from core.exceptions import AIProviderError
from core.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_INSTRUCTION = (
    "Eres un asistente de verificación factual. Recibes un tema y una lista "
    "numerada de fuentes con su contenido. Tu única tarea es EXTRAER hechos "
    "concretos que aparezcan LITERALMENTE en esas fuentes — nunca completar "
    "huecos con tu propio conocimiento ni inventar cifras.\n\n"
    "Responde ÚNICAMENTE con una línea por hecho, en este formato exacto:\n"
    "HECHO: <afirmación concreta y verificable> | FUENTES: <números de fuente, separados por comas>\n\n"
    "Reglas estrictas:\n"
    "- Cada hecho debe citar al menos un número de fuente real de la lista.\n"
    "- Si un dato solo aparece en tu conocimiento general y NO en las fuentes, NO lo incluyas.\n"
    "- No mezcles datos de modelos o productos distintos.\n"
    "- Si no hay hechos claros y verificables en las fuentes, responde exactamente: SIN_HECHOS"
)


def _build_prompt(topic: str, sources: list[RawSearchResult]) -> str:
    numbered_sources = "\n\n".join(
        f"[Fuente {i}] {src.title}\nURL: {src.url}\nContenido: {src.content[:2000]}"
        for i, src in enumerate(sources, start=1)
    )
    return f"Tema: {topic}\n\nFuentes disponibles:\n\n{numbered_sources}"


def extract_facts(
    topic: str, raw_sources: list[RawSearchResult], saved_sources: list[Source], provider: TextAIProvider
) -> list[ExtractedFact]:
    """
    Extrae hechos citados a partir de las fuentes recuperadas. saved_sources
    debe estar en el MISMO ORDEN que raw_sources (para mapear número de
    fuente citado -> id real en la base de datos).
    """
    if not raw_sources:
        return []

    prompt = _build_prompt(topic, raw_sources)

    try:
        response = provider.generate(prompt, system_instruction=_SYSTEM_INSTRUCTION)
    except AIProviderError as error:
        raise FactExtractionError(f"Fallo al extraer hechos con IA: {error}") from error

    if response.strip() == "SIN_HECHOS":
        return []

    facts = []
    for line in response.strip().splitlines():
        line = line.strip()
        if not line.upper().startswith("HECHO:"):
            continue

        match = re.match(r"HECHO:\s*(.+?)\s*\|\s*FUENTES:\s*(.+)", line, re.IGNORECASE)
        if not match:
            continue

        claim = match.group(1).strip()
        cited_numbers_raw = match.group(2).strip()

        source_ids = []
        for number_str in cited_numbers_raw.split(","):
            number_str = number_str.strip()
            if not number_str.isdigit():
                continue
            index = int(number_str) - 1
            if 0 <= index < len(saved_sources):
                source_ids.append(saved_sources[index].id)

        if not source_ids:
            logger.warning(f"Hecho descartado por no citar ninguna fuente válida: '{claim}'")
            continue

        facts.append(
            ExtractedFact(
                claim=claim,
                status=FACT_UNCERTAIN,  # el verifier decide el estado final
                confidence_score=0.5,
                source_ids=source_ids,
            )
        )

    return facts