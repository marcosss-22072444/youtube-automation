"""
verifier.py

Verifica los hechos extraídos SIN necesidad de una llamada adicional
al LLM: decide si cada hecho tiene evidencia suficiente (corroboración
entre fuentes) y detecta contradicciones numéricas entre hechos sobre
el mismo tema. También ofrece una comprobación ligera del guion final
contra los hechos usados.
"""

import re

from research.models import (
    ExtractedFact, Source,
    FACT_VERIFIED, FACT_UNCERTAIN, FACT_CONFLICTING,
    PRIMARY_OFFICIAL,
)
from core.logger import get_logger

logger = get_logger(__name__)

_HIGH_RELIABILITY_THRESHOLD = 0.85


def _normalize_claim_key(claim: str) -> str:
    """Quita números y espacios extra para agrupar hechos sobre el mismo tema."""
    without_numbers = re.sub(r"\d+([.,]\d+)?", "#", claim.lower())
    return re.sub(r"\s+", " ", without_numbers).strip()


def _extract_numbers(claim: str) -> list[str]:
    return re.findall(r"\d+(?:[.,]\d+)?", claim)


def verify_facts(
    facts: list[ExtractedFact], sources: list[Source], min_sources_required: int
) -> list[ExtractedFact]:
    """
    Asigna el estado final a cada hecho: 'verified' si tiene
    corroboración suficiente, 'uncertain' si no, y 'conflicting' si
    contradice numéricamente a otro hecho sobre el mismo tema.
    Modifica los ExtractedFact en el sitio y también los devuelve.
    """
    sources_by_id = {s.id: s for s in sources}

    # Paso 1: corroboración
    for fact in facts:
        supporting_sources = [sources_by_id[sid] for sid in fact.source_ids if sid in sources_by_id]

        is_single_high_reliability_official = (
            len(supporting_sources) == 1
            and supporting_sources[0].source_type == PRIMARY_OFFICIAL
            and supporting_sources[0].reliability_score >= _HIGH_RELIABILITY_THRESHOLD
        )

        if len(supporting_sources) >= min_sources_required or is_single_high_reliability_official:
            fact.status = FACT_VERIFIED
            fact.confidence_score = min(1.0, 0.5 + 0.15 * len(supporting_sources))
        else:
            fact.status = FACT_UNCERTAIN
            fact.confidence_score = 0.3

    # Paso 2: contradicciones (comparando hechos entre sí, sin llamar al LLM)
    groups: dict[str, list[ExtractedFact]] = {}
    for fact in facts:
        key = _normalize_claim_key(fact.claim)
        groups.setdefault(key, []).append(fact)

    for key, group in groups.items():
        if len(group) < 2:
            continue

        numbers_per_fact = [set(_extract_numbers(f.claim)) for f in group]
        all_same_numbers = all(numbers == numbers_per_fact[0] for numbers in numbers_per_fact)

        if not all_same_numbers:
            for fact in group:
                fact.status = FACT_CONFLICTING
                fact.confidence_score = 0.0
            logger.warning(f"Contradicción detectada entre {len(group)} hechos sobre: '{key}'")

    return facts


def check_script_claims(script_content: str, facts: list[ExtractedFact]) -> list[str]:
    """
    Comprobación ligera post-generación: busca números en el guion
    final y avisa (sin bloquear) de cualquier cifra que no aparezca
    respaldada por ningún hecho 'verified' — para poder auditarlo.
    Devuelve la lista de avisos (vacía si todo está respaldado).
    """
    verified_numbers = set()
    for fact in facts:
        if fact.status == FACT_VERIFIED:
            verified_numbers.update(_extract_numbers(fact.claim))

    script_numbers = set(_extract_numbers(script_content))
    unverified_numbers = script_numbers - verified_numbers

    warnings = []
    for number in unverified_numbers:
        warnings.append(f"Cifra '{number}' en el guion sin respaldo directo en hechos verificados.")

    return warnings