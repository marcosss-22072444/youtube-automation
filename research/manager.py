"""
manager.py

Punto de entrada único del módulo de investigación: research_idea()
orquesta búsqueda web, extracción de hechos y verificación, respetando
la configuración y credenciales propias de cada canal.
"""

import re
from urllib.parse import urlparse

from ideas.models import Idea
from channels.models import Channel
from research import repository
from research.models import (
    Source, ResearchResult,
    PRIMARY_OFFICIAL, SPECIALIZED_MEDIA, REFERENCE_DATABASE, GENERAL_MEDIA, SECONDARY_SOURCE,
    FACT_VERIFIED, RESEARCH_COMPLETED, RESEARCH_INSUFFICIENT_EVIDENCE,
)
from research.search.base import SearchProvider
from research.search.tavily_provider import TavilySearchProvider
from research.verification import fact_extractor, verifier
from research.exceptions import SearchProviderError
from core.ai_providers.base import TextAIProvider
from core.ai_providers.factory import get_text_provider_for_channel
from core.exceptions import AIProviderError
from core.credentials.base import resolve_credential
from core.credentials.factory import get_default_credentials_store
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

_REFERENCE_DOMAINS = ("wikipedia.org", "wikidata.org")


def _classify_source(url: str, title: str, content: str) -> Source:
    """Heurística por dominio: clasifica el tipo de fuente y su fiabilidad."""
    domain = urlparse(url).netloc.lower()

    if any(ref in domain for ref in _REFERENCE_DOMAINS):
        source_type, score = REFERENCE_DATABASE, 0.8
    elif domain.count(".") == 1 and not any(x in domain for x in ("blog", "forum", "reddit")):
        # Heurística simple: dominios "raíz" cortos suelen ser sitios oficiales de marca
        source_type, score = PRIMARY_OFFICIAL, 0.75
    elif any(x in domain for x in ("news", "magazine", "media", "auto", "motor", "tech")):
        source_type, score = SPECIALIZED_MEDIA, 0.65
    elif any(x in domain for x in ("blog", "forum", "reddit", "medium.com")):
        source_type, score = SECONDARY_SOURCE, 0.35
    else:
        source_type, score = GENERAL_MEDIA, 0.5

    return Source(url=url, title=title, source_type=source_type, reliability_score=score, raw_content=content)


def _build_search_queries(idea: Idea, instructions: str, provider: TextAIProvider, max_queries: int) -> list[str]:
    """Genera unas pocas consultas de búsqueda relevantes a partir de la idea."""
    system_instruction = (
        f"{instructions}\n\n"
        f"Genera hasta {max_queries} consultas de búsqueda cortas (en inglés, 3-6 palabras) "
        f"para investigar datos concretos y verificables sobre el siguiente tema de vídeo. "
        f"Responde ÚNICAMENTE con una consulta por línea, sin numeración ni texto adicional."
    )
    prompt = f"Título: {idea.title}\nResumen: {idea.summary}"

    try:
        response = provider.generate(prompt, system_instruction=system_instruction)
    except AIProviderError as error:
        logger.warning(f"Fallo al generar consultas de búsqueda, se usa el título como única consulta: {error}")
        return [idea.title]

    queries = [line.strip() for line in response.strip().splitlines() if line.strip()]
    return queries[:max_queries] if queries else [idea.title]


def research_idea(
    idea: Idea, channel: Channel,
    search_provider: SearchProvider | None = None,
    text_provider: TextAIProvider | None = None,
) -> ResearchResult:
    """
    Investiga una Idea: busca fuentes reales en la web, extrae hechos
    citados, los verifica, y devuelve un ResearchResult ya guardado en
    la base de datos, listo para usarse en la generación del guion.
    """
    config = settings.research
    channel_config = repository.get_channel_research_config(channel.id)

    if channel_config and not channel_config["enabled"]:
        logger.info(f"Canal {channel.id}: investigación desactivada para este canal.")
        run_id = repository.create_run(idea.id, channel.id, RESEARCH_INSUFFICIENT_EVIDENCE)
        return ResearchResult(id=run_id, idea_id=idea.id, channel_id=channel.id, status=RESEARCH_INSUFFICIENT_EVIDENCE)

    instructions = (channel_config or {}).get("instructions") or config["default_instructions"]
    min_sources = (channel_config or {}).get("min_sources_required") or config["min_sources_required"]

    if text_provider is None:
        text_provider = get_text_provider_for_channel(channel.id)

    if search_provider is None:
        store = get_default_credentials_store()
        api_key = resolve_credential(channel.id, "tavily", settings.tavily_api_key, store)
        search_provider = TavilySearchProvider(api_key=api_key)

    queries = _build_search_queries(idea, instructions, text_provider, config["max_search_queries_per_idea"])
    logger.info(f"Canal {channel.id}: investigando idea {idea.id} con {len(queries)} consulta(s).")

    seen_urls = set()
    raw_results = []
    for query in queries:
        try:
            results = search_provider.search(query, config["candidates_per_search"])
        except SearchProviderError as error:
            logger.warning(f"Búsqueda '{query}' falló, se continúa con las demás: {error}")
            continue

        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                raw_results.append(result)

    if not raw_results:
        run_id = repository.create_run(idea.id, channel.id, RESEARCH_INSUFFICIENT_EVIDENCE)
        logger.warning(f"Idea {idea.id}: sin fuentes encontradas, investigación marcada como insuficiente.")
        return ResearchResult(id=run_id, idea_id=idea.id, channel_id=channel.id, status=RESEARCH_INSUFFICIENT_EVIDENCE)

    run_id = repository.create_run(idea.id, channel.id, RESEARCH_COMPLETED)

    saved_sources = [
        repository.add_source(run_id, _classify_source(r.url, r.title, r.content))
        for r in raw_results
    ]

    facts = fact_extractor.extract_facts(idea.title, raw_results, saved_sources, text_provider)
    facts = verifier.verify_facts(facts, saved_sources, min_sources)

    for fact in facts:
        repository.add_fact(run_id, fact)

    final_status = RESEARCH_COMPLETED if any(f.status == FACT_VERIFIED for f in facts) else RESEARCH_INSUFFICIENT_EVIDENCE
    repository.update_run_status(run_id, final_status)

    logger.info(
        f"Idea {idea.id}: investigación completada. {len(saved_sources)} fuentes, "
        f"{len(facts)} hechos ({sum(1 for f in facts if f.status == FACT_VERIFIED)} verificados)."
    )

    return ResearchResult(
        id=run_id, idea_id=idea.id, channel_id=channel.id, status=final_status,
        sources=saved_sources, facts=facts,
    )