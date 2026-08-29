"""
repository.py

Acceso a la base de datos para 'research_runs', 'research_sources',
'research_facts' y 'channel_research_config'.
"""

import json
import sqlite3
from datetime import datetime

from core.database import get_connection
from research.models import ResearchResult, Source, ExtractedFact


def _row_to_source(row: sqlite3.Row) -> Source:
    return Source(
        id=row["id"],
        url=row["url"],
        title=row["title"],
        source_type=row["source_type"],
        reliability_score=row["reliability_score"],
        raw_content=row["raw_content"],
    )


def _row_to_fact(row: sqlite3.Row) -> ExtractedFact:
    return ExtractedFact(
        id=row["id"],
        claim=row["claim"],
        status=row["status"],
        confidence_score=row["confidence_score"],
        source_ids=json.loads(row["source_ids"]),
    )


def save_research_result(result: ResearchResult) -> ResearchResult:
    """
    Guarda un ResearchResult completo: la ejecución, sus fuentes y sus
    hechos, en ese orden (las fuentes necesitan existir antes de que
    los hechos puedan referenciarlas por id).
    """
    now = datetime.now().isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO research_runs (idea_id, channel_id, status, created_at) VALUES (?, ?, ?, ?)",
            (result.idea_id, result.channel_id, result.status, now),
        )
        result.id = cursor.lastrowid

        for source in result.sources:
            source_cursor = conn.execute(
                """
                INSERT INTO research_sources
                    (research_run_id, url, title, source_type, reliability_score, raw_content, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.id, source.url, source.title, source.source_type,
                    source.reliability_score, source.raw_content, now,
                ),
            )
            source.id = source_cursor.lastrowid

        for fact in result.facts:
            fact_cursor = conn.execute(
                """
                INSERT INTO research_facts
                    (research_run_id, claim, status, confidence_score, source_ids, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.id, fact.claim, fact.status, fact.confidence_score,
                    json.dumps(fact.source_ids), now,
                ),
            )
            fact.id = fact_cursor.lastrowid

    return result


def get_research_result_by_idea(idea_id: int) -> ResearchResult | None:
    """Recupera el ResearchResult más reciente de una idea, con sus fuentes y hechos."""
    with get_connection() as conn:
        run_row = conn.execute(
            "SELECT * FROM research_runs WHERE idea_id = ? ORDER BY created_at DESC LIMIT 1",
            (idea_id,),
        ).fetchone()

        if run_row is None:
            return None

        source_rows = conn.execute(
            "SELECT * FROM research_sources WHERE research_run_id = ?", (run_row["id"],)
        ).fetchall()
        fact_rows = conn.execute(
            "SELECT * FROM research_facts WHERE research_run_id = ?", (run_row["id"],)
        ).fetchall()

    return ResearchResult(
        id=run_row["id"],
        idea_id=run_row["idea_id"],
        channel_id=run_row["channel_id"],
        status=run_row["status"],
        created_at=run_row["created_at"],
        sources=[_row_to_source(row) for row in source_rows],
        facts=[_row_to_fact(row) for row in fact_rows],
    )


# --- Configuración de research por canal ---

def get_channel_research_config(channel_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM channel_research_config WHERE channel_id = ?", (channel_id,)
        ).fetchone()
    return dict(row) if row else None


def upsert_channel_research_config(
    channel_id: int, instructions: str | None, min_sources_required: int | None,
    confidence_threshold: float | None, enabled: bool,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO channel_research_config
                (channel_id, instructions, min_sources_required, confidence_threshold, enabled)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET
                instructions = excluded.instructions,
                min_sources_required = excluded.min_sources_required,
                confidence_threshold = excluded.confidence_threshold,
                enabled = excluded.enabled
            """,
            (channel_id, instructions, min_sources_required, confidence_threshold, int(enabled)),
        )

def create_run(idea_id: int, channel_id: int, status: str) -> int:
    """Crea la ejecución de investigación y devuelve su id."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO research_runs (idea_id, channel_id, status, created_at) VALUES (?, ?, ?, ?)",
            (idea_id, channel_id, status, datetime.now().isoformat()),
        )
    return cursor.lastrowid


def add_source(run_id: int, source: Source) -> Source:
    """Guarda una fuente y le asigna su id real."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO research_sources
                (research_run_id, url, title, source_type, reliability_score, raw_content, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, source.url, source.title, source.source_type,
                source.reliability_score, source.raw_content, datetime.now().isoformat(),
            ),
        )
    source.id = cursor.lastrowid
    return source


def add_fact(run_id: int, fact: ExtractedFact) -> ExtractedFact:
    """Guarda un hecho (ya con estado final) y le asigna su id real."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO research_facts
                (research_run_id, claim, status, confidence_score, source_ids, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, fact.claim, fact.status, fact.confidence_score,
                json.dumps(fact.source_ids), datetime.now().isoformat(),
            ),
        )
    fact.id = cursor.lastrowid
    return fact


def update_run_status(run_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE research_runs SET status = ? WHERE id = ?", (status, run_id))