"""
retry_manager.py

Revisa periódicamente los schedule_runs fallidos y reintenta
automáticamente los que sean reintentables (errores transitorios),
con backoff exponencial y un límite máximo de intentos configurables.
Los errores permanentes (o los que agotan sus reintentos) se dejan
como 'failed' definitivamente, sin más acción automática.
"""

from datetime import datetime, timedelta

from scheduler import repository as schedule_repository
from scheduler.job_queue import enqueue
from scheduler.models import Job
from error_handler.classifier import classify_error, RETRYABLE
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


def _calculate_backoff_seconds(retry_count: int) -> float:
    """Backoff exponencial: base * 2^retry_count, limitado a max_retry_delay_seconds."""
    base = settings.error_handler["base_retry_delay_seconds"]
    max_delay = settings.error_handler["max_retry_delay_seconds"]
    return min(base * (2 ** retry_count), max_delay)


def check_and_requeue_failed_runs() -> None:
    """
    Revisa todos los schedule_runs fallidos: clasifica su error,
    programa su próximo reintento si procede, y reencola los que ya
    han cumplido su tiempo de espera.
    """
    max_retries = settings.error_handler["max_retries"]
    failed_runs = schedule_repository.list_failed_runs()

    for run in failed_runs:
        log_prefix = f"[run={run.id} entry={run.schedule_entry_id} intentos={run.retry_count}/{max_retries}]"

        if run.retry_count >= max_retries:
            continue  # ya agotó sus reintentos, no se toca más

        classification = classify_error(run.error_message or "")

        if classification != RETRYABLE:
            logger.info(f"{log_prefix} Error permanente, no se reintenta: {run.error_message}")
            schedule_repository.mark_exhausted(run.id, max_retries)
            continue

        if run.next_retry_at is None:
            delay_seconds = _calculate_backoff_seconds(run.retry_count)
            next_retry_at = (datetime.now() + timedelta(seconds=delay_seconds)).isoformat()
            schedule_repository.schedule_next_retry(run.id, next_retry_at)
            logger.info(f"{log_prefix} Reintento programado en {delay_seconds:.0f}s ({next_retry_at}).")
            continue

        if datetime.now().isoformat() >= run.next_retry_at:
            entry = schedule_repository.get_entry_by_id(run.schedule_entry_id)
            if entry is None:
                logger.warning(f"{log_prefix} La franja original ya no existe, se descarta el reintento.")
                schedule_repository.mark_exhausted(run.id, max_retries)
                continue

            new_retry_count = run.retry_count + 1
            schedule_repository.requeue_for_retry(run.id, new_retry_count)

            job = Job(schedule_run_id=run.id, channel_id=entry.channel_id, content_type=entry.content_type)
            enqueue(job)
            logger.info(f"{log_prefix} Reintento {new_retry_count}/{max_retries} encolado.")