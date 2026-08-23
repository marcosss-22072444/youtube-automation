"""
runner.py

El orquestador del Scheduler: un hilo detector que revisa
periódicamente qué franjas de channel_schedules coinciden con la
hora actual (respetando el timezone global o el del canal), las
reclama de forma atómica (evitando duplicados), y las encola; y uno o
varios hilos worker que consumen la cola y ejecutan el pipeline.
"""

import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from channels import manager as channel_manager
from scheduler import repository as schedule_repository
from scheduler.job_queue import enqueue, dequeue
from scheduler.models import Job
from scheduler.pipeline_executor import execute_job
from error_handler.retry_manager import check_and_requeue_failed_runs
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

_stop_event = threading.Event()


def _get_channel_timezone(channel_id: int) -> ZoneInfo:
    """Devuelve el timezone del canal si lo tiene, o el global por defecto."""
    canal = channel_manager.get_channel(channel_id)
    tz_name = canal.timezone or settings.scheduler.get("timezone", "Europe/Madrid")
    return ZoneInfo(tz_name)


def _detect_and_enqueue_due_entries() -> None:
    """Revisa todas las franjas activas y encola las que coincidan con la hora actual."""
    entries = schedule_repository.list_all_enabled_entries()

    for entry in entries:
        tz = _get_channel_timezone(entry.channel_id)
        now_local = datetime.now(tz)

        current_day = now_local.weekday()  # 0=lunes ... 6=domingo, coincide con nuestra convención
        current_time = now_local.strftime("%H:%M")

        if entry.day_of_week != current_day or entry.time_of_day != current_time:
            continue

        run_date = now_local.strftime("%Y-%m-%d")
        run = schedule_repository.claim_run(entry.id, run_date)

        if run is None:
            # Ya reclamada por este u otro ciclo — evita duplicados.
            continue

        job = Job(schedule_run_id=run.id, channel_id=entry.channel_id, content_type=entry.content_type)
        enqueue(job)
        logger.info(
            f"Franja reclamada y encolada: canal={entry.channel_id}, tipo={entry.content_type}, "
            f"fecha={run_date}, hora={entry.time_of_day} ({tz.key})"
        )


def _detector_loop() -> None:
    """Bucle del hilo detector: revisa franjas pendientes cada check_interval_seconds."""
    interval = settings.scheduler.get("check_interval_seconds", 60)
    logger.info(f"Detector de horarios iniciado (revisión cada {interval}s).")

    while not _stop_event.is_set():
        try:
            _detect_and_enqueue_due_entries()
            check_and_requeue_failed_runs()
        except Exception as error:
            logger.error(f"Error en el ciclo de detección de horarios: {error}")

        _stop_event.wait(interval)


def _worker_loop(worker_id: int) -> None:
    """Bucle de un worker: consume trabajos de la cola secuencialmente."""
    logger.info(f"Worker {worker_id} iniciado.")

    while not _stop_event.is_set():
        job = dequeue(timeout=5)
        if job is None:
            continue

        logger.info(f"Worker {worker_id}: procesando trabajo (canal={job.channel_id}, tipo={job.content_type}).")
        execute_job(job)


def start_scheduler() -> list[threading.Thread]:
    """
    Arranca el detector y el/los worker(s) en hilos separados, y
    devuelve la lista de hilos (para poder esperarlos o pararlos).
    """
    _stop_event.clear()
    worker_count = settings.scheduler.get("worker_count", 1)

    threads = [threading.Thread(target=_detector_loop, name="scheduler-detector", daemon=True)]
    for i in range(worker_count):
        threads.append(threading.Thread(target=_worker_loop, args=(i + 1,), name=f"scheduler-worker-{i+1}", daemon=True))

    for thread in threads:
        thread.start()

    logger.info(f"Scheduler iniciado: 1 detector + {worker_count} worker(s).")
    return threads


def stop_scheduler() -> None:
    """Señala a todos los hilos del Scheduler que deben detenerse."""
    _stop_event.set()
    logger.info("Señal de parada enviada al Scheduler.")