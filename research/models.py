"""
models.py

Define las estructuras de datos del módulo de investigación:
- Source: una fuente web recuperada (con su tipo y fiabilidad).
- ExtractedFact: un hecho concreto, vinculado a las fuentes que lo
  respaldan, con un estado (verified/uncertain/conflicting/rejected).
- ResearchResult: el resultado completo de investigar una Idea.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# --- Tipos de fuente (fijos, es una clasificación del dominio, no configuración) ---
PRIMARY_OFFICIAL = "primary_official"
SPECIALIZED_MEDIA = "specialized_media"
REFERENCE_DATABASE = "reference_database"
GENERAL_MEDIA = "general_media"
SECONDARY_SOURCE = "secondary_source"
LOW_CONFIDENCE = "low_confidence"

VALID_SOURCE_TYPES = (
    PRIMARY_OFFICIAL, SPECIALIZED_MEDIA, REFERENCE_DATABASE,
    GENERAL_MEDIA, SECONDARY_SOURCE, LOW_CONFIDENCE,
)

# --- Estados de un hecho extraído ---
FACT_VERIFIED = "verified"
FACT_UNCERTAIN = "uncertain"
FACT_CONFLICTING = "conflicting"
FACT_REJECTED = "rejected"

# --- Estados de una investigación completa ---
RESEARCH_COMPLETED = "completed"
RESEARCH_INSUFFICIENT_EVIDENCE = "insufficient_evidence"
RESEARCH_FAILED = "failed"


@dataclass
class Source:
    """Representa una fuente web recuperada durante la investigación."""

    url: str
    source_type: str
    reliability_score: float  # 0.0 - 1.0
    title: Optional[str] = None
    raw_content: Optional[str] = None
    id: Optional[int] = None


@dataclass
class ExtractedFact:
    """Representa un hecho concreto extraído de las fuentes, con su respaldo."""

    claim: str
    status: str
    confidence_score: float  # 0.0 - 1.0
    source_ids: list[int] = field(default_factory=list)
    id: Optional[int] = None


@dataclass
class ResearchResult:
    """Representa el resultado completo de investigar una Idea."""

    idea_id: int
    channel_id: int
    status: str
    sources: list[Source] = field(default_factory=list)
    facts: list[ExtractedFact] = field(default_factory=list)
    id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    @property
    def verified_facts(self) -> list[ExtractedFact]:
        """Solo los hechos con evidencia suficiente, listos para usarse en el guion."""
        return [f for f in self.facts if f.status == FACT_VERIFIED]